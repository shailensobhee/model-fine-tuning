#!/usr/bin/env bash
# =============================================================================
# studio_autostart.sh - bring up Unsloth Studio + its Cloudflare tunnel and
#                       record the public URL where the notebook can find it.
#
# Called by /etc/jupyter/jupyter_server_config.py every time jupyter-lab starts
# (that hook is the only launch path that survives the AMD Dev Cloud platform
# overriding the container ENTRYPOINT with its own jupyter-lab command).
#
# Idempotent and safe to run on every boot / every jupyter (re)start:
#   * if Studio is already healthy on $STUDIO_PORT, it does nothing but refresh
#     the registry from the existing tunnel URL;
#   * otherwise it launches Studio (0.0.0.0 -> auto Cloudflare quick-tunnel,
#     forced IPv4) and waits for the public URL.
#
# Writes $TUNNELS_JSON (default /run/aai/tunnels.json, OUTSIDE /workspace so the
# per-session /workspace wipe never deletes it):
#   {"studio": "https://<rand>.trycloudflare.com", "local": "http://127.0.0.1:8890",
#    "port": 8890, "healthy": true, "updated_at": "...Z"}
# The instinct notebook's "Get your Studio link" cell reads the "studio" key.
# =============================================================================
set -uo pipefail

WS=/workspace
STUDIO_PORT="${STUDIO_PORT:-8890}"
STUDIO_HOME="${UNSLOTH_STUDIO_HOME:-/root/.unsloth/studio}"
UNSLOTH_BIN=/root/.unsloth/studio/unsloth_studio/bin/unsloth
STUDIO_LOG="$WS/studio_launch.log"

# Registry MUST live outside /workspace (reset_session wipes /workspace).
TUNNELS_JSON="${TUNNELS_JSON:-/run/aai/tunnels.json}"
LOCKDIR=/run/aai/studio_autostart.lock

CF_RE='https://[a-z0-9-]+\.trycloudflare\.com'

log() { echo "[$(date -u +%H:%M:%S)] [studio-autostart] $*" >&2; }

mkdir -p "$WS" "$STUDIO_HOME" "$(dirname "$TUNNELS_JSON")"

# ---- single-flight lock: multiple jupyter workers must not race ------------
# mkdir is atomic; if we don't get the lock another invocation is handling it.
if ! mkdir "$LOCKDIR" 2>/dev/null; then
    log "another autostart holds the lock ($LOCKDIR); exiting"
    exit 0
fi
# Release the lock only for THIS process; keep it if we background Studio and
# exit (the trap fires on our exit, which is fine: the launch is already done).
trap 'rmdir "$LOCKDIR" 2>/dev/null || true' EXIT

# ---- preset the admin password (skip the first-boot setup screen) ----------
# Studio's ensure_default_admin() would otherwise seed a RANDOM password with
# must_change_password=True, forcing the "Setup your account / Choose a new
# password" screen. We seed user "unsloth" / "amdadvancingai" first (idempotent,
# never clobbers a changed password) so ensure_default_admin() is a no-op and the
# user goes straight to login. Run this BEFORE Studio launches. The auth DB lives
# in the image layer (not /workspace), so this normally only ever seeds once; the
# call stays here as a self-heal in case the auth dir is wiped.
SEED_ADMIN=/usr/local/bin/seed_admin.sh
if [ -x "$SEED_ADMIN" ]; then
    log "ensuring admin account is preset (skips first-boot password setup)"
    bash "$SEED_ADMIN" || log "seed_admin returned non-zero (non-fatal)"
fi

# ---- fire-and-forget model/dataset prefetch --------------------------------
# On the AMD Dev Cloud the platform overrides the container ENTRYPOINT, so
# entrypoint.sh (which normally kicks off the prefetch) never runs. This hook is
# the only launch path that survives, so start the prefetch here too. It is
# idempotent (per-repo stamps under /workspace) and self-contained (also stages
# the Local-tab JSONL), and we background it fully detached so it never delays
# Studio startup.
#
# Guard is a RUNNING-process check (not a permanent marker): a session reset
# wipes /workspace (models + stamps gone) while this hook re-fires, so we MUST be
# free to re-download. We only skip if a prefetch is already in flight, which
# prevents concurrent duplicate runs when jupyter-lab loads this config twice.
PREFETCH=/usr/local/bin/prefetch_workspace.sh
if [ -x "$PREFETCH" ]; then
    if pgrep -f "bash $PREFETCH" >/dev/null 2>&1; then
        log "prefetch already running; not starting another"
    else
        log "starting background prefetch ($PREFETCH -> $WS/prefetch.log)"
        setsid bash "$PREFETCH" >> "$WS/prefetch.log" 2>&1 < /dev/null &
    fi
fi

health() {
    curl -fsS -m 4 "http://127.0.0.1:${STUDIO_PORT}/api/health" 2>/dev/null \
        | grep -q '"healthy"'
}

find_cf_url() {
    grep -rhoE "$CF_RE" \
        "$STUDIO_LOG" "$STUDIO_HOME"/logs/server/server-*.log 2>/dev/null \
        | head -1
}

write_registry() {
    # $1 = studio cloudflare url (may be empty), $2 = healthy (true/false)
    local url="$1" healthy="$2"
    python3 - "$TUNNELS_JSON" "$url" "$STUDIO_PORT" "$healthy" <<'PY'
import json, sys, datetime
path, url, port, healthy = sys.argv[1:5]
json.dump({
    "studio":     url or None,
    "local":      f"http://127.0.0.1:{port}",
    "port":       int(port),
    "healthy":    healthy == "true",
    "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}, open(path, "w"))
PY
    log "wrote $TUNNELS_JSON (studio=${url:-none} healthy=$healthy)"
}

# ---- already running? just refresh the registry ----------------------------
if health; then
    url="$(find_cf_url)"
    log "Studio already healthy on :$STUDIO_PORT (url=${url:-unknown})"
    write_registry "$url" "true"
    exit 0
fi

# ---- launch Studio (backgrounded; tunnel is auto-created on 0.0.0.0) --------
if [ ! -x "$UNSLOTH_BIN" ]; then
    log "ERROR: unsloth binary not found at $UNSLOTH_BIN; cannot start Studio"
    write_registry "" "false"
    exit 1
fi

log "launching Unsloth Studio on :$STUDIO_PORT (Cloudflare tunnel, IPv4)"
: > "$STUDIO_LOG"
# setsid + </dev/null so Studio fully detaches from jupyter's process group and
# is not killed when this hook returns control to jupyter-lab.
setsid "$UNSLOTH_BIN" studio -H 0.0.0.0 -p "$STUDIO_PORT" --cloudflare \
    >> "$STUDIO_LOG" 2>&1 < /dev/null &
STUDIO_PID=$!
log "Studio pid $STUDIO_PID"

# ---- wait (up to ~90s) for the public Cloudflare URL -----------------------
CF_URL=""
for _ in $(seq 1 30); do
    CF_URL="$(find_cf_url)"
    [ -n "$CF_URL" ] && break
    kill -0 "$STUDIO_PID" 2>/dev/null || { log "Studio exited early; see $STUDIO_LOG"; break; }
    sleep 3
done

if [ -n "$CF_URL" ]; then
    log "Studio tunnel up: $CF_URL"
    write_registry "$CF_URL" "$(health && echo true || echo false)"
else
    log "tunnel URL not seen yet; registry written without it (notebook re-run will pick it up)"
    write_registry "" "$(health && echo true || echo false)"
fi

exit 0
