# Unsloth Studio image (AMD Instinct MI300X)

These files build and auto-start the Unsloth Studio container image that backs
`../model-finetuning-unsloth-instinct.ipynb` on AMD Dev Cloud.

They were moved here from the `ROCm/AAI-2026-Workshops-Dev` workshop repo, which
now keeps only the two Jupyter notebooks. This folder is the home for the image
build and its runtime scripts.

## Files

| File | Role |
|------|------|
| `Dockerfile.unsloth-studio` | Builds `shailensobhee1/unsloth-studio-amd-aai:mi300x` (ROCm PyTorch stack + Unsloth Studio + cloudflared). |
| `jupyter_server_config.py` | Baked to `/etc/jupyter/`. Auto-starts Studio when jupyter-lab boots. See "why a Jupyter hook" below. |
| `studio_autostart.sh` | Idempotent launcher: starts Studio on `:8890` + a Cloudflare tunnel, writes `/run/aai/tunnels.json`. |
| `entrypoint.sh` | Standalone `docker run` entrypoint (the platform bypasses it on Dev Cloud, see below). |
| `cloudflared-shim.sh` | Forces IPv4 on cloudflared for hosts with broken IPv6. |
| `prefetch_workspace.sh` | Idempotent prefetch of HF caches onto the `/workspace` volume. |

## Why a Jupyter startup hook (not ENTRYPOINT)

AMD Dev Cloud spawns the image with its own command, roughly:

```
/bin/sh -c "pip install ... jupyter ... && jupyter-lab --ip=0.0.0.0 --port=8888 ..."
```

That replaces the Docker `ENTRYPOINT`/`CMD`, so `entrypoint.sh` never runs and
Studio would never auto-start. `jupyter-lab` always loads
`/etc/jupyter/jupyter_server_config.py` regardless of how it is invoked, so the
hook there fires `studio_autostart.sh` in the background. It is the one launch
path that survives the platform command override.

## Contract with the notebook

The notebook's "Get your Studio link" cell reads `/run/aai/tunnels.json`:

```json
{"studio": "https://<sub>.trycloudflare.com", "local": "http://127.0.0.1:8890", "port": 8890, "healthy": true, "updated_at": "..."}
```

Studio binds `:8890` (8888 belongs to the platform's jupyter-lab). The registry
lives under `/run/aai` (outside `/workspace`) so a session reset that wipes
`/workspace` does not delete it.

## Build

```bash
docker build -f Dockerfile.unsloth-studio -t shailensobhee1/unsloth-studio-amd-aai:mi300x .
```
