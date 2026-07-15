#!/usr/bin/env python3
"""Sync the built landing notebooks into the upstream AAI workshop repo.

The upstream repo (ROCm/AAI-2026-Workshops-Dev) is PRIVATE and stores the
notebooks two levels deep under

    DevZone_Content/Model Fine-Tuning & Training/

GitHub's notebook viewer renders relative image references by rewriting them to
raw.githubusercontent.com URLs. For a PRIVATE repo those URLs return 404 to an
unauthenticated browser, so externally-referenced diagrams show broken. The fix
is to embed the diagrams as base64 attachments so the notebooks are
self-contained and render regardless of repo visibility, path depth, or being
offline.

This script regenerates BOTH notebooks with the diagrams embedded and copies
them into the target repo. It does NOT copy a separate assets/ folder (there is
nothing external to reference) and it does NOT rewrite any paths. It does not
commit or push; it just writes the files so you can review, then commit and open
a PR yourself.

Usage:
  python scripts/sync_to_aai_workshop.py <path-to-AAI-2026-Workshops-Dev>
  python scripts/sync_to_aai_workshop.py                 # uses $AAI_WORKSHOP_REPO
                                                         # or ~/AAI-2026-Workshops-Dev

After running, in the target repo:
  git checkout -b feat/embed-notebook-diagrams
  git add "DevZone_Content/Model Fine-Tuning & Training"
  git commit -m "Embed diagrams in fine-tuning notebooks so they render in the private repo"
  git push -u origin HEAD && gh pr create ...

No em dashes anywhere (repo style rule).
"""
import json
import os
import sys

from landing_content import build_cells

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ASSETS = os.path.join(REPO_ROOT, "notebooks", "unsloth", "assets")

# Relative location of the notebooks inside the upstream workshop repo.
DEST_NB_SUBDIR = os.path.join("DevZone_Content", "Model Fine-Tuning & Training")

# Import the per-target cfg dicts from the builder so content stays in one place.
from build_landing_notebook import RADEON, INSTINCT  # noqa: E402


def build_notebook(cfg):
    cfg = dict(cfg)
    # Embed the diagrams as base64 attachments. This is what makes the notebook
    # render in the PRIVATE upstream repo (no external raw.githubusercontent.com
    # fetch, which 404s to an unauthenticated browser).
    cfg["embed_dir"] = SRC_ASSETS
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
    if not os.path.isdir(nb_dir):
        raise SystemExit(f"Target notebook dir missing: {nb_dir}")

    # Write both notebooks with the diagrams embedded.
    for cfg in (RADEON, INSTINCT):
        nb, ncells = build_notebook(cfg)
        out = os.path.join(nb_dir, cfg["filename"])
        with open(out, "w") as f:
            json.dump(nb, f, indent=1, ensure_ascii=True)
            f.write("\n")
        print("Wrote", out, "(cells:", str(ncells) + ", diagrams embedded)")

    print()
    print("Sync complete. Diagrams are embedded, so no assets/ folder is needed.")
    print("Review, then in", dest_repo + ":")
    print("  git checkout -b feat/embed-notebook-diagrams")
    print('  git add "%s"' % DEST_NB_SUBDIR)
    print('  git commit -m "Embed diagrams in fine-tuning notebooks"')
    print("  git push -u origin HEAD && gh pr create ...")
    print()
    print("Note: the repo-root assets/ folder (if present from an earlier PR) is")
    print("now unused by these notebooks and can be removed in the same PR.")


if __name__ == "__main__":
    main()
