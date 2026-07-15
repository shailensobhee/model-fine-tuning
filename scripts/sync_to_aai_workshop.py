#!/usr/bin/env python3
"""Sync the built landing notebooks into the upstream AAI workshop repo.

The upstream repo (ROCm/AAI-2026-Workshops-Dev) stores the notebooks two levels
deep under

    DevZone_Content/Model Fine-Tuning & Training/

and keeps the diagram images in a REPO-ROOT ``assets/`` folder. So the notebook
image paths there must be ``../../assets/...`` instead of the sibling ``assets/``
layout this repo uses.

This script regenerates BOTH notebooks with the correct ``asset_prefix`` for the
upstream layout and copies them (plus the PNG assets) into the target repo. It
does NOT commit or push; it just stages the files so you can review, then commit
and open a PR yourself.

Usage:
  python scripts/sync_to_aai_workshop.py <path-to-AAI-2026-Workshops-Dev>
  python scripts/sync_to_aai_workshop.py                 # uses $AAI_WORKSHOP_REPO
                                                         # or ~/AAI-2026-Workshops-Dev

After running, in the target repo:
  git checkout -b feat/sync-finetuning-notebooks
  git add "DevZone_Content/Model Fine-Tuning & Training" assets
  git commit -m "Sync Unsloth fine-tuning notebooks + assets"
  git push -u origin HEAD && gh pr create ...

No em dashes anywhere (repo style rule).
"""
import json
import os
import shutil
import sys

from landing_content import build_cells

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ASSETS = os.path.join(REPO_ROOT, "notebooks", "unsloth", "assets")

# Relative location of the notebooks inside the upstream workshop repo.
DEST_NB_SUBDIR = os.path.join("DevZone_Content", "Model Fine-Tuning & Training")
# Assets live at the upstream repo root.
DEST_ASSETS_SUBDIR = "assets"
# Notebook is two levels deep, so it points up to the root assets folder.
UPSTREAM_ASSET_PREFIX = "../../assets/"

# The 5 diagrams the notebooks embed (PNG only; the SVGs are source artifacts).
ASSET_PNGS = [
    "01-finetuning-overview.png",
    "02-sft-vs-grpo.png",
    "03-full-lora-qlora.png",
    "04-studio-loop.png",
    "05-launch-flow.png",
]

# Import the per-target cfg dicts from the builder so content stays in one place.
from build_landing_notebook import RADEON, INSTINCT  # noqa: E402


def build_notebook(cfg):
    cfg = dict(cfg)
    cfg["asset_prefix"] = UPSTREAM_ASSET_PREFIX
    cells = build_cells(cfg)
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }, len(cells)


def main():
    dest_repo = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.environ.get(
            "AAI_WORKSHOP_REPO",
            os.path.expanduser("~/AAI-2026-Workshops-Dev"),
        )
    )
    dest_repo = os.path.abspath(os.path.expanduser(dest_repo))
    if not os.path.isdir(os.path.join(dest_repo, ".git")):
        raise SystemExit(f"Not a git repo: {dest_repo}")

    nb_dir = os.path.join(dest_repo, DEST_NB_SUBDIR)
    assets_dir = os.path.join(dest_repo, DEST_ASSETS_SUBDIR)
    if not os.path.isdir(nb_dir):
        raise SystemExit(f"Target notebook dir missing: {nb_dir}")
    os.makedirs(assets_dir, exist_ok=True)

    # Write both notebooks with the upstream asset prefix.
    for cfg in (RADEON, INSTINCT):
        nb, ncells = build_notebook(cfg)
        out = os.path.join(nb_dir, cfg["filename"])
        with open(out, "w") as f:
            json.dump(nb, f, indent=1, ensure_ascii=True)
            f.write("\n")
        print("Wrote", out, "(cells:", str(ncells) + ", asset_prefix:", UPSTREAM_ASSET_PREFIX + ")")

    # Copy the PNG assets to the repo-root assets folder.
    for name in ASSET_PNGS:
        src = os.path.join(SRC_ASSETS, name)
        if not os.path.isfile(src):
            raise SystemExit(f"Missing source asset: {src}")
        shutil.copy2(src, os.path.join(assets_dir, name))
        print("Copied asset", name, "->", assets_dir)

    print()
    print("Sync complete. Review, then in", dest_repo + ":")
    print('  git checkout -b feat/sync-finetuning-notebooks')
    print('  git add "%s" %s' % (DEST_NB_SUBDIR, DEST_ASSETS_SUBDIR))
    print('  git commit -m "Sync Unsloth fine-tuning notebooks + assets"')
    print("  git push -u origin HEAD && gh pr create ...")


if __name__ == "__main__":
    main()
