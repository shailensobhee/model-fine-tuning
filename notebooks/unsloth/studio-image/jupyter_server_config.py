# =============================================================================
# jupyter_server_config.py - AMD Dev Cloud Unsloth Studio (MI300X) auto-start
#
# WHY THIS FILE EXISTS
# --------------------
# On AMD Dev Cloud the notebook platform spawns this image with its OWN command,
# roughly:
#     /bin/sh -c "pip install ... jupyter ... && jupyter-lab --ip=0.0.0.0 --port=8888 ..."
# That injected command REPLACES the Docker ENTRYPOINT/CMD, so the image's
# entrypoint.sh never runs and Unsloth Studio never auto-starts (the bug we
# debugged: Studio port closed, no Cloudflare tunnel, no /run/aai/tunnels.json).
#
# jupyter-lab, however, ALWAYS loads this config file on startup regardless of
# how it was invoked. So we hook Studio's launch here: as jupyter-lab boots we
# fire studio_autostart.sh in the background. It launches Studio on $STUDIO_PORT
# (8890; 8888 belongs to jupyter-lab itself) with a Cloudflare tunnel and records
# the public URL in /run/aai/tunnels.json, which the "Get your Studio link"
# notebook cell reads.
#
# DESIGN NOTES
# ------------
# * Fire-and-forget: we spawn a fully detached background process and return
#   immediately, so nothing here can delay or break the Jupyter server. The user
#   always gets their notebook; Studio is best-effort on top.
# * Idempotent by construction: studio_autostart.sh takes a single-flight lock
#   and no-ops if Studio is already healthy, so it is safe even if jupyter-lab
#   loads this config more than once (multiple workers, restarts).
# * Version-independent: we do the launch at config-load time rather than via a
#   jupyter-server post-start hook API (which differs across versions). The
#   autostart script polls for Studio health itself, so a few seconds' head start
#   is harmless.
# =============================================================================
import os
import shutil
import subprocess

_AUTOSTART = "/usr/local/bin/studio_autostart.sh"


def _launch_studio_autostart():
    if not (os.path.exists(_AUTOSTART) and os.access(_AUTOSTART, os.X_OK)):
        print("[studio-autostart] %s missing or not executable; skipping"
              % _AUTOSTART)
        return
    bash = shutil.which("bash") or "/bin/bash"
    try:
        # Detached and non-blocking: start_new_session detaches Studio from the
        # Jupyter process group; stdio -> DEVNULL so it never blocks on a pipe.
        subprocess.Popen(
            [bash, _AUTOSTART],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=os.environ.copy(),
        )
        print("[studio-autostart] launched %s (Studio + Cloudflare tunnel will "
              "come up in the background)" % _AUTOSTART)
    except Exception as exc:  # never let this break the Jupyter server
        print("[studio-autostart] failed to launch %s: %r" % (_AUTOSTART, exc))


_launch_studio_autostart()
