#!/usr/bin/env bash
# =============================================================================
# prefetch_workspace.sh
# Pre-download the requested models + datasets onto the PERSISTENT /workspace
# volume so Unsloth Studio finds them AND they survive instance recreation.
#
# Idempotent: each repo is skipped if already present. Safe to run every boot.
# Runs INSIDE the container (called by entrypoint.sh); never over the tunnel
# (Studio's download API writes to the ephemeral /root/.cache).
# =============================================================================
set -uo pipefail

WS=/workspace
export HF_HOME="${HF_HOME:-$WS/.hf}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-$WS/hf_cache}"
export HF_DATASETS_CACHE="${HF_DATASETS_CACHE:-$WS/.hf/datasets}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"
# The base image sometimes sets HF_HUB_ENABLE_HF_TRANSFER=1 without shipping the
# hf_transfer package -> misleading "model not found". Force it off.
unset HF_HUB_ENABLE_HF_TRANSFER || true

MODELS_DIR="$WS/models"
JSONL_DIR="$WS/datasets_jsonl"
STAMP_DIR="$WS/.prefetch_done"
mkdir -p "$HF_HUB_CACHE" "$HF_DATASETS_CACHE" "$MODELS_DIR" "$JSONL_DIR" "$STAMP_DIR"

HF=/root/.unsloth/studio/unsloth_studio/bin/hf
PY=/root/.unsloth/studio/unsloth_studio/bin/python

# ---- Models -----------------------------------------------------------------
# All repo IDs verified against the HF Hub API (real safetensors weights present).
# Cached under HF_HUB_CACHE=/workspace/hf_cache, so Studio's model picker lists
# them automatically (its scanner globs models--* in HF_HUB_CACHE).
MODELS=(
  "unsloth/gemma-4-E2B-it"
  "unsloth/gemma-4-E4B-it"
  "unsloth/Qwen3.5-2B"
  "unsloth/Qwen3.5-9B"
  "unsloth/Llama-3.2-3B-Instruct"
)

# All repo IDs verified against the HF Hub API. Cached under HF_DATASETS_CACHE so
# the Studio "Hugging Face" dataset tab loads them instantly (no re-download).
# NOTE: Studio's "Local" dataset tab does NOT scan the HF cache; it only lists
# Data-Designer recipe dirs and files in the uploads dir. See the JSONL/upload
# staging step below for making these show up under "Local".
DATASETS=(
  "mlabonne/FineTome-100k"
  "unsloth/llava-instruct-mix-vsft-mini"
  "unsloth/alpaca-cleaned"
  "philschmid/guanaco-sharegpt-style"
)

_stamp() { echo "$STAMP_DIR/$(echo "$1" | tr '/:' '__').done"; }

echo "== prefetch into $WS =="
df -h "$WS" 2>/dev/null | sed 's/^/  /'

echo "== models -> $HF_HUB_CACHE =="
for repo in "${MODELS[@]}"; do
  st="$(_stamp "$repo")"
  if [ -f "$st" ]; then echo "  ok (cached) $repo"; continue; fi
  echo "  -> $repo"
  if HF_HUB_CACHE="$HF_HUB_CACHE" "$HF" download "$repo" \
        --exclude "*.pth" "original/*" "*.gguf" ${HF_TOKEN:+--token "$HF_TOKEN"}; then
    touch "$st"
  else
    echo "     !! failed: $repo (will retry next boot)"
  fi
done

echo "== datasets -> $HF_DATASETS_CACHE =="
for repo in "${DATASETS[@]}"; do
  st="$(_stamp "ds:$repo")"
  if [ -f "$st" ]; then echo "  ok (cached) $repo"; continue; fi
  echo "  -> $repo"
  if HF_HUB_CACHE="$HF_HUB_CACHE" "$HF" download "$repo" --repo-type dataset; then
    touch "$st"
  else
    echo "     !! failed: $repo (will retry next boot)"
  fi
done

# ---- Offline-proof alpaca JSONL exports (so they appear under Studio "Local") -
# Studio's "Local" tab does NOT scan the HF cache; it lists only Data-Designer
# recipe dirs and files in the uploads dir. So we export the text SFT datasets to
# alpaca-format JSONL on /workspace (survives restarts) AND stage a copy into the
# Studio uploads dir (see entrypoint) so participants can pick them under "Local".
# Vision (llava) is intentionally NOT exported to alpaca JSONL; use it from the
# "Hugging Face" tab where it is already cached.
echo "== exporting text SFT datasets -> alpaca JSONL ($JSONL_DIR) =="
HF_DATASETS_CACHE="$HF_DATASETS_CACHE" "$PY" - <<'PYEOF' || echo "  !! JSONL export step skipped"
import os, json
from datasets import load_dataset
OUT="/workspace/datasets_jsonl"; os.makedirs(OUT, exist_ok=True)

def first(conv, roles):
    for c in conv or []:
        frm = c.get("from") or c.get("role")
        if frm in roles:
            return c.get("value") or c.get("content")
    return None

def export(name, out_name, row_fn):
    p = os.path.join(OUT, out_name)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        print(f"  ok (exists) {out_name}"); return
    try:
        ds = load_dataset(name, split="train")
        n = 0
        with open(p, "w") as f:
            for e in ds:
                row = row_fn(e)
                if row and row.get("instruction") and row.get("output"):
                    f.write(json.dumps(row, ensure_ascii=False) + "\n"); n += 1
        print(f"  wrote {n} rows -> {out_name}")
    except Exception as ex:
        print(f"  !! export failed for {name}: {ex}")
        if os.path.exists(p) and os.path.getsize(p) == 0:
            os.remove(p)

# FineTome-100k: ShareGPT-style conversations -> first human/gpt turn
export("mlabonne/FineTome-100k", "finetome_100k.jsonl",
       lambda e: {"instruction": first(e.get("conversations"), ("human","user")),
                  "input": "",
                  "output": first(e.get("conversations"), ("gpt","assistant"))})

# alpaca-cleaned: already instruction/input/output
export("unsloth/alpaca-cleaned", "alpaca_cleaned.jsonl",
       lambda e: {"instruction": e.get("instruction"),
                  "input": e.get("input","") or "",
                  "output": e.get("output")})

# guanaco-sharegpt-style: conversations list
export("philschmid/guanaco-sharegpt-style", "guanaco_sharegpt.jsonl",
       lambda e: {"instruction": first(e.get("conversations"), ("human","user")),
                  "input": "",
                  "output": first(e.get("conversations"), ("gpt","assistant"))})
PYEOF

# ---- Stage JSONL into Studio's uploads dir so they show under "Local" --------
# Studio's "Local" tab scans ONLY <studio>/assets/datasets/{recipes,uploads};
# it does NOT scan the HF cache. The uploads scanner follows symlinks (verified
# against the Studio backend), so link the persistent /workspace JSONL exports
# into the uploads dir. Self-contained here so BOTH launch paths (entrypoint.sh
# for standalone docker run, and studio_autostart.sh for the AMD Dev Cloud
# Jupyter-hook path) get Local-tab datasets without extra wiring.
STUDIO_HOME="${UNSLOTH_STUDIO_HOME:-/root/.unsloth/studio}"
UPLOADS_DIR="$STUDIO_HOME/assets/datasets/uploads"
mkdir -p "$UPLOADS_DIR"
staged=0
for f in "$JSONL_DIR"/*.jsonl; do
  [ -e "$f" ] || continue
  if ln -sf "$f" "$UPLOADS_DIR/$(basename "$f")"; then
    staged=$((staged+1))
  fi
done
echo "== staged $staged JSONL dataset(s) into Studio uploads ($UPLOADS_DIR) =="

echo "== prefetch inventory =="
echo "-- models --";   ls -1 "$HF_HUB_CACHE"      2>/dev/null | sed 's/^/   /'
echo "-- datasets --"; ls -1 "$HF_DATASETS_CACHE" 2>/dev/null | sed 's/^/   /'
echo "-- JSONL --";    ls -1 "$JSONL_DIR"         2>/dev/null | sed 's/^/   /'
echo "-- Local uploads --"; ls -1 "$UPLOADS_DIR"  2>/dev/null | sed 's/^/   /'
echo "== prefetch done =="
