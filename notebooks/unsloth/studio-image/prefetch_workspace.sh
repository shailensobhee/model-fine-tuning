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
MODELS=(
  "unsloth/gemma-4-E2B-it"
  "unsloth/Qwen3.5-2B"
)

DATASETS=(
  "mlabonne/FineTome-100k"
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

# ---- Offline-proof alpaca JSONL of FineTome (Local source for the demo) ------
if [ ! -f "$JSONL_DIR/finetome_100k.jsonl" ]; then
  echo "== exporting FineTome-100k -> alpaca JSONL =="
  HF_DATASETS_CACHE="$HF_DATASETS_CACHE" "$PY" - <<'PYEOF' || echo "  !! JSONL export skipped"
import os, json
from datasets import load_dataset
OUT="/workspace/datasets_jsonl"; os.makedirs(OUT, exist_ok=True)
try:
    ds = load_dataset("mlabonne/FineTome-100k", split="train")
    p = os.path.join(OUT, "finetome_100k.jsonl"); n=0
    with open(p, "w") as f:
        for e in ds:
            conv = e.get("conversations") or []
            u = next((c["value"] for c in conv if c.get("from") in ("human","user")), None)
            a = next((c["value"] for c in conv if c.get("from") in ("gpt","assistant")), None)
            if u and a:
                f.write(json.dumps({"instruction":u,"input":"","output":a}, ensure_ascii=False)+"\n"); n+=1
    print(f"  wrote {n} rows -> {p}")
except Exception as e:
    print("  !! FineTome export failed:", e)
PYEOF
fi

echo "== prefetch inventory =="
echo "-- models --";   ls -1 "$HF_HUB_CACHE"      2>/dev/null | sed 's/^/   /'
echo "-- datasets --"; ls -1 "$HF_DATASETS_CACHE" 2>/dev/null | sed 's/^/   /'
echo "-- JSONL --";    ls -1 "$JSONL_DIR"         2>/dev/null | sed 's/^/   /'
echo "== prefetch done =="
