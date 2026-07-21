#!/usr/bin/env bash
# =============================================================================
# entrypoint.sh - Unsloth Studio AMD (MI300X) devcloud image
#   1. prefetch models/datasets onto /workspace (idempotent, backgrounded)
#   2. launch Unsloth Studio (Cloudflare quick-tunnel, forced IPv4)
#   3. wait for the public URL, then print an MOTD with all the info needed
#   4. optionally launch JupyterLab
#
# Usage (CMD): studio (default) | studio+jupyter | bash
# =============================================================================
set -uo pipefail

WS=/workspace
STUDIO_PORT="${STUDIO_PORT:-8888}"
JUPYTER_PORT="${JUPYTER_PORT:-8889}"
STUDIO_HOME="${UNSLOTH_STUDIO_HOME:-/root/.unsloth/studio}"
# Studio's install lives in the venv install root, NOT on /workspace. Only the HF
# caches belong on the persistent volume. Force the studio home to the real
# install root so a stale/empty override never triggers "Studio not set up".
if [ ! -d "$STUDIO_HOME/unsloth_studio/bin" ]; then
    STUDIO_HOME=/root/.unsloth/studio
fi
export UNSLOTH_STUDIO_HOME="$STUDIO_HOME"
STUDIO_LOG="$WS/studio_launch.log"
UNSLOTH_BIN=/root/.unsloth/studio/unsloth_studio/bin/unsloth

mkdir -p "$WS" "$STUDIO_HOME"

mode="${1:-studio}"
if [ "$mode" = "bash" ] || [ "$mode" = "sh" ]; then
    exec "$@"
fi

# ---- 1. Prefetch (background so Studio comes up fast; models stream in) ------
echo "[entrypoint] starting /workspace prefetch in background (see $WS/prefetch.log)"
/usr/local/bin/prefetch_workspace.sh > "$WS/prefetch.log" 2>&1 &
PREFETCH_PID=$!

# ---- 1b. Stage exported JSONL into Studio's uploads dir so they show up under
#          the Studio "Local" dataset tab. The Local tab scans ONLY
#          <studio>/assets/datasets/{recipes,uploads}; it does NOT scan the HF
#          cache. Symlinks are followed by the scanner (it uses is_file()), so we
#          link the persistent /workspace JSONL into uploads. Backgrounded: waits
#          for the prefetch export to finish, then links whatever is present.
UPLOADS_DIR="$STUDIO_HOME/assets/datasets/uploads"
JSONL_DIR="$WS/datasets_jsonl"
(
  mkdir -p "$UPLOADS_DIR"
  for _ in $(seq 1 240); do
    if ls "$JSONL_DIR"/*.jsonl >/dev/null 2>&1; then
      for f in "$JSONL_DIR"/*.jsonl; do
        ln -sf "$f" "$UPLOADS_DIR/$(basename "$f")"
      done
    fi
    # keep re-linking until prefetch finishes (new files may appear)
    kill -0 "$PREFETCH_PID" 2>/dev/null || break
    sleep 5
  done
  # final pass after prefetch completes
  for f in "$JSONL_DIR"/*.jsonl; do
    [ -e "$f" ] && ln -sf "$f" "$UPLOADS_DIR/$(basename "$f")"
  done
  echo "[entrypoint] staged JSONL datasets into Studio uploads: $UPLOADS_DIR"
) >> "$WS/prefetch.log" 2>&1 &

# ---- 2. Launch Studio (0.0.0.0 -> auto Cloudflare quick-tunnel, IPv4 forced) -
echo "[entrypoint] launching Unsloth Studio on :$STUDIO_PORT (Cloudflare tunnel, IPv4)"
: > "$STUDIO_LOG"
"$UNSLOTH_BIN" studio -H 0.0.0.0 -p "$STUDIO_PORT" --cloudflare >> "$STUDIO_LOG" 2>&1 &
STUDIO_PID=$!

# ---- 3. Wait for the public Cloudflare URL + admin bootstrap password --------
CF_URL=""
for _ in $(seq 1 60); do
    CF_URL="$(grep -rhoE 'https://[a-z0-9-]+\.trycloudflare\.com' \
        "$STUDIO_LOG" "$STUDIO_HOME"/logs/server/server-*.log 2>/dev/null | head -1)"
    [ -n "$CF_URL" ] && break
    kill -0 "$STUDIO_PID" 2>/dev/null || { echo "[entrypoint] Studio exited early"; break; }
    sleep 3
done

BOOT_PW="$(cat "$STUDIO_HOME/auth/.bootstrap_password" 2>/dev/null || echo '(see Studio logs)')"

# ---- 4. Optional JupyterLab -------------------------------------------------
JUP_LINE="(not started; run with CMD 'studio+jupyter')"
if [ "$mode" = "studio+jupyter" ]; then
    echo "[entrypoint] launching JupyterLab on :$JUPYTER_PORT"
    jupyter lab --ip=0.0.0.0 --port="$JUPYTER_PORT" --allow-root --no-browser \
        --ServerApp.token=amd-oneclick --ServerApp.root_dir="$WS" \
        > "$WS/jupyter.log" 2>&1 &
    JUP_LINE="http://0.0.0.0:$JUPYTER_PORT/lab?token=amd-oneclick"
fi

# ---- 5. MOTD ----------------------------------------------------------------
cat <<MOTD

================================================================================
  Unsloth Studio  -  AMD MI300X (ROCm)  -  DevCloud image
================================================================================
  Public URL (Cloudflare) : ${CF_URL:-"(tunnel not up yet - check $STUDIO_LOG)"}
  Local URL               : http://0.0.0.0:$STUDIO_PORT
  JupyterLab              : $JUP_LINE

  Studio admin login      : username 'unsloth'
  Bootstrap password      : $BOOT_PW
  (you'll be asked to change it on first login)

  Persistent /workspace layout:
    models  (HF cache)    : $WS/hf_cache      (auto-listed in Studio model picker)
    datasets (HF cache)   : $WS/.hf/datasets  (use via Studio "Hugging Face" tab)
    local JSONL exports   : $WS/datasets_jsonl (linked into Studio "Local" tab)
    Studio data           : $STUDIO_HOME

  Prefetch (backgrounded) : tail -f $WS/prefetch.log
  Studio log              : tail -f $STUDIO_LOG
================================================================================

MOTD

# Persist the MOTD so it can be re-read any time.
{ echo "Public URL : ${CF_URL}"; echo "Local URL  : http://0.0.0.0:$STUDIO_PORT"; \
  echo "Jupyter    : $JUP_LINE"; echo "Admin      : unsloth / $BOOT_PW"; } > "$WS/CONNECTION_INFO.txt"

# ---- 6. Stay in foreground on the Studio process ----------------------------
wait "$STUDIO_PID"
