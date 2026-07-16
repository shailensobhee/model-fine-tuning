#!/usr/bin/env python3
"""Generate the student-facing landing notebooks for Unsloth Studio.

Generates BOTH notebooks from the shared content in landing_content.py so the
generic teaching material stays in sync automatically:

  notebooks/unsloth/model-finetuning-unsloth-radeon.ipynb    (Radeon / RDNA)
  notebooks/unsloth/model-finetuning-unsloth-instinct.ipynb  (Instinct MI300X)

Only the hardware / access specific bits differ (see the per-target cfg dicts
below). Edit generic content in landing_content.py, then run this script to
regenerate both notebooks at once.

Usage:
  python scripts/build_landing_notebook.py            # build both
  python scripts/build_landing_notebook.py radeon     # build one
  python scripts/build_landing_notebook.py instinct

WARNING: the instinct notebook has DIVERGED from this generator. It is now
hand-maintained (verified 2026-07-16 against the live AMD Dev Cloud portal):
  - the connection cell derives the Jupyter server-proxy URL
    (<host>/jupyter-user-<id>/proxy/8890/) instead of reading
    /workspace/CONNECTION_INFO.txt and advertising a Cloudflare link. On the
    hosted portal that file does not exist and the Cloudflare tunnel fails to
    start, so the old generated cell only ever printed "not up yet" + an IP.
  - diagram images are embedded (base64) and downscaled.
Regenerating instinct from this script will REVERT those fixes. Do NOT run
`build_landing_notebook.py instinct` without re-applying the proxy-aware
connection cell afterwards. The radeon target is still generator-driven.

No em dashes anywhere (repo style rule).
"""
import json
import os
import sys

from landing_content import build_cells

NB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "notebooks",
    "unsloth",
)


# ---------------------------------------------------------------- Radeon target
RADEON = {
    "filename": "model-finetuning-unsloth-radeon.ipynb",
    "platform": "Radeon Cloud",
    "gpu_display": "AMD Radeon",
    "title": "# Start Here: Fine-Tuning LLMs with Unsloth Studio on Radeon Cloud",
    "vram_note": [
        "On an AMD Radeon Pro W7900 (48 GB), a 4-bit Qwen3-4B QLoRA run in this repo",
        "used only about **5.6 GB** of VRAM. That is the magic: big model, small",
        "footprint.",
    ],
    "launch_heading": "# Part 2: Launch Unsloth Studio on Radeon Cloud",
    "part2_intro": [
        "You should already be inside a running **Radeon Cloud** GPU session with this",
        "notebook open (that is how you are reading this). If not, start a GPU session",
        "on Radeon Cloud and open this notebook first.",
    ],
    "step1_terminal": [
        "In the JupyterLab menu bar, click:",
        "",
        "> **File -> New -> Terminal**",
        "",
        "(Or click the **+** button to open the Launcher, then choose **Terminal**.)",
        "",
        "A black terminal tab opens. This is a normal shell on your GPU machine.",
    ],
    "studio_note": [
        "Give it a moment on the first run while it warms up. You do not need to",
        "install anything: Unsloth Studio is already available on the Radeon Cloud",
        "image.",
    ],
    "troubleshoot_env_fix": "You are in the wrong environment; confirm you are in the Radeon Cloud session shell.",
    "working_nb_bullet": [
        "- `model-finetuning-on-radeon.ipynb` : the active Radeon working notebook.",
    ],
}


# -------------------------------------------------------------- Instinct target
INSTINCT = {
    "filename": "model-finetuning-unsloth-instinct.ipynb",
    "platform": "AMD Dev Cloud",
    "gpu_display": "AMD Instinct MI300X",
    "title": "# Start Here: Fine-Tuning LLMs with Unsloth Studio on AMD Instinct MI300X",
    "vram_note": [
        "The AMD Instinct MI300X gives you a massive **192 GB** of HBM3 memory per GPU,",
        "so memory is rarely the constraint here. A 4-bit Qwen3-4B QLoRA run needs only",
        "about **5.6 GB**, which barely registers. On the MI300X you can comfortably go",
        "much bigger: fine-tune larger models (for example a Llama 3.x 70B in 4-bit),",
        "use longer sequence lengths, or bump up the batch size for faster training.",
        "The same QLoRA trick still applies, you just have far more headroom.",
    ],
    "launch_heading": "# Part 2: Launch Unsloth Studio on AMD Instinct MI300X",
    "part2_intro": [
        "You should already be inside a running **AMD Instinct MI300X** GPU session with",
        "this notebook open (that is how you are reading this). On the AMD Dev Cloud you",
        "do not provision anything by hand: opening this notebook from",
        "`notebooks.amd.com` automatically spins up an MI300X GPU instance for you in",
        "the background. If you are reading this, your GPU is already allocated and",
        "ready.",
    ],
    "step1_terminal": [
        "In the JupyterLab menu bar, click:",
        "",
        "> **File -> New -> Terminal**",
        "",
        "(Or click the **+** button to open the Launcher, then choose **Terminal**.)",
        "",
        "A black terminal tab opens. This is a normal shell on your MI300X GPU instance.",
    ],
    "studio_note": [
        "Give it a moment on the first run while it warms up. You do not need to",
        "install anything: Unsloth Studio is already available on the AMD Dev Cloud",
        "MI300X image.",
    ],
    "troubleshoot_env_fix": "You are in the wrong environment; confirm you are in the AMD Dev Cloud MI300X session shell.",
    "working_nb_bullet": [
        "- `model-finetuning-on-radeon.ipynb` : the Radeon working notebook (the code",
        "  is portable; it runs on MI300X too).",
    ],
}


TARGETS = {"radeon": RADEON, "instinct": INSTINCT}


def build_one(cfg):
    cells = build_cells(cfg)
    notebook = {
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
    }
    path = os.path.join(NB_DIR, cfg["filename"])
    with open(path, "w") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=True)
        f.write("\n")
    print("Wrote", path, "(cells:", str(len(cells)) + ")")


def main():
    which = sys.argv[1:] or ["radeon", "instinct"]
    for name in which:
        if name not in TARGETS:
            raise SystemExit(f"Unknown target '{name}'. Choose from: {', '.join(TARGETS)}")
        build_one(TARGETS[name])


if __name__ == "__main__":
    main()
