#!/usr/bin/env bash
# =============================================================================
# seed_admin.sh - preset the Unsloth Studio admin account so the first-boot
#                 "Setup your account / Choose a new password" screen is skipped.
#
# Studio's ensure_default_admin() seeds user "unsloth" with a RANDOM diceware
# password and must_change_password=True, which is what forces the setup screen.
# We instead create that same user ourselves with a KNOWN password and
# must_change_password=False BEFORE Studio starts. ensure_default_admin() then
# finds the user already present and does nothing, so the user lands straight on
# the login form (or is already usable) with these fixed credentials:
#
#     username: unsloth
#     password: amdadvancingai
#
# Idempotent: if the account already exists this is a no-op (never clobbers a
# password the user has since changed). Safe to run on every boot. We seed using
# Studio's OWN hashing/storage modules so the hash format always matches.
#
# The auth DB lives at $UNSLOTH_STUDIO_HOME/auth/auth.db (default
# /root/.unsloth/studio/auth/auth.db) which is in the image layer, NOT under
# /workspace, so it survives the per-session /workspace wipe.
# =============================================================================
set -uo pipefail

ADMIN_USER="${STUDIO_ADMIN_USER:-unsloth}"
ADMIN_PASS="${STUDIO_ADMIN_PASS:-amdadvancingai}"

PY=/root/.unsloth/studio/unsloth_studio/bin/python
BACKEND=/root/.unsloth/studio/unsloth_studio/lib/python3.13/site-packages/studio/backend

log() { echo "[$(date -u +%H:%M:%S)] [seed-admin] $*" >&2; }

if [ ! -x "$PY" ]; then
    log "ERROR: studio python not found at $PY; cannot seed admin"
    exit 0   # never fail the boot over this
fi
if [ ! -d "$BACKEND" ]; then
    log "ERROR: studio backend not found at $BACKEND; cannot seed admin"
    exit 0
fi

PYTHONPATH="$BACKEND" STUDIO_ADMIN_USER="$ADMIN_USER" STUDIO_ADMIN_PASS="$ADMIN_PASS" \
"$PY" - <<'PYEOF'
import os, secrets, sys

try:
    from auth import storage, hashing
except Exception as e:
    print(f"[seed-admin] import failed: {e}", file=sys.stderr)
    sys.exit(0)  # do not block boot

user = os.environ.get("STUDIO_ADMIN_USER", "unsloth")
password = os.environ.get("STUDIO_ADMIN_PASS", "amdadvancingai")

# Enforce Studio's own minimum so we never write an unusable credential.
min_len = getattr(storage, "MIN_PASSWORD_LENGTH", 8)
if len(password) < min_len:
    print(f"[seed-admin] password shorter than {min_len} chars; refusing to seed", file=sys.stderr)
    sys.exit(0)

existing = storage.get_user_and_secret(user)
if existing is not None:
    # Account already present. Do NOT clobber a password the user may have
    # changed. Only report state.
    _, _, _, must_change = existing
    print(f"[seed-admin] user '{user}' already exists (must_change_password={must_change}); leaving as-is", file=sys.stderr)
    sys.exit(0)

storage.create_initial_user(
    username=user,
    password=password,
    jwt_secret=secrets.token_urlsafe(64),
    must_change_password=False,
)

# Verify what we just wrote so a silent hash mismatch can't ship.
rec = storage.get_user_and_secret(user)
if rec is None:
    print("[seed-admin] ERROR: user not present after create", file=sys.stderr)
    sys.exit(1)
salt, pwd_hash, _jwt, must_change = rec
ok = hashing.verify_password(password, salt, pwd_hash)
print(f"[seed-admin] seeded user '{user}' verify={ok} must_change_password={must_change} db={storage.DB_PATH}", file=sys.stderr)
sys.exit(0 if ok else 1)
PYEOF
rc=$?
if [ "$rc" -eq 0 ]; then
    log "admin seed complete (user=$ADMIN_USER)"
else
    log "admin seed reported rc=$rc (non-fatal; boot continues)"
fi
exit 0
