# model-fine-tuning

Working repository for LLM fine-tuning notebooks and workshop material, targeting AMD GPUs (Instinct MI300X / ROCm and Radeon / RDNA).

## Layout

```
notebooks/
  unsloth/
    model-finetuning-unsloth-radeon.ipynb            START HERE (Radeon): student landing guide
    model-finetuning-unsloth-instinct.ipynb          START HERE (Instinct MI300X): student landing guide
    llama-3.2-vision-finetune-unsloth.ipynb   Llama 3.2 Vision fine-tune (Unsloth)
    llama-3.1-8b-grpo-unsloth.ipynb           Llama 3.1 8B GRPO (Unsloth), reference
    model-finetuning-on-radeon.ipynb          ACTIVE working notebook (Radeon GPU)
    qwen3_qlora_smoketest.ipynb               Qwen3-4B QLoRA smoke test (Radeon W7900), VERIFIED
    qwen3_qlora_smoketest.executed.ipynb      Same notebook, with saved run outputs
    qwen3-qlora-radeon-w7900-notes.md         Setup notes, gotchas, measured results
    utils_unsloth.py                          Helper module for the vision notebook
scripts/
  landing_content.py                          Shared content for BOTH landing notebooks (edit generic text here)
  build_landing_notebook.py                   Generator: builds both landing notebooks from landing_content.py
  build_diagrams.py                            Generator for the notebook concept diagrams
notebooks/unsloth/assets/                      Concept diagrams (SVG source + PNG), embedded in the landing notebook
```

## Start here (new students)

New to fine-tuning? Open the landing notebook for your GPU:

- Radeon / RDNA (Radeon Cloud): `notebooks/unsloth/model-finetuning-unsloth-radeon.ipynb`
- Instinct MI300X (AMD Dev Cloud): `notebooks/unsloth/model-finetuning-unsloth-instinct.ipynb`

Both are friendly, self-contained landing notebooks that:

- explain the core concepts in plain English (LLMs, fine-tuning, SFT, GRPO,
  LoRA, QLoRA, and what training data looks like),
- walk you through launching **Unsloth Studio** on your GPU session (open a
  terminal, run `unsloth studio -H 0.0.0.0 -p 8888`, then open the secure
  Cloudflare link it prints),
- and guide you through your first fine-tune inside the Studio UI.

No prior deep-learning experience required.

### Keeping the two landing notebooks in sync

The generic teaching content is identical across both notebooks and lives in
ONE place: `scripts/landing_content.py`. Only the hardware and access specific
bits (title, VRAM headroom, how you reach the environment, platform name)
differ, and those are supplied by small per-target config dicts in
`scripts/build_landing_notebook.py`.

To update a concept, explanation, or workflow step, edit
`scripts/landing_content.py` and regenerate BOTH notebooks:

```bash
python scripts/build_landing_notebook.py            # builds radeon + instinct
python scripts/build_landing_notebook.py radeon     # or just one
```

This guarantees the two notebooks never drift. The five concept diagrams they
embed are regenerated from `scripts/build_diagrams.py` (light-themed SVG source
plus PNG, rendered with cairosvg, no external tools needed).

## Working notebook

`notebooks/unsloth/model-finetuning-on-radeon.ipynb` is the active working
notebook. It started as a copy of the Llama 3.1 8B GRPO notebook and is being
adapted for Radeon (RDNA) consumer GPUs.

## Verified Radeon notebook: Qwen3-4B QLoRA smoke test

`notebooks/unsloth/qwen3_qlora_smoketest.ipynb` is a self-contained, end-to-end
QLoRA smoke test that has been run on real AMD RDNA3 silicon. Every cell proves a
real capability (GPU matmul, actual training loss drop, post-train inference), not
just a version string. Set `SMOKE=1` for a fast 30-step demo run, or leave it unset
for 60 steps.

Verified environment and results (AMD Radeon Pro W7900, Navi 31 / gfx1100, 48 GB):

| Item | Value |
| --- | --- |
| torch | 2.10.0+rocm7.0 (hip 7.0.51831) |
| Unsloth / TRL / Transformers | 2026.7.2 / 0.23.1 / 4.57.6 |
| bitsandbytes | 0.50.0.dev0 (ROCm continuous-release, 4-bit clean, no NaN/Inf) |
| fp16 8192^3 matmul | 68.6 TFLOP/s |
| Model | unsloth/Qwen3-4B-unsloth-bnb-4bit (4-bit) |
| LoRA | r=16, 7 target modules, 33.0M trainable (1.30%) |
| Train (SMOKE=1, 30 steps, eff batch 16, seq 1024) | runtime 297 s, GPU 88-100% |
| Peak reserved VRAM | 5.56 GB |
| Loss | 1.844 -> 0.813 |

The executed copy with all outputs is `qwen3_qlora_smoketest.executed.ipynb`. Setup
gotchas (render group, the installer misdetecting the card as CPU-only without ROCm
userspace, and the ROCm bitsandbytes pre-release) are documented in
`qwen3-qlora-radeon-w7900-notes.md`.

## Roadmap

- [x] Student landing notebook (Unsloth Studio on Radeon Cloud)
- [x] Student landing notebook (Unsloth Studio on Instinct MI300X / AMD Dev Cloud)
- [x] Unsloth Llama 3.2 Vision fine-tune notebook
- [x] Unsloth Llama 3.1 8B GRPO notebook
- [x] Verified Qwen3-4B QLoRA notebook on Radeon (W7900 / RDNA3)
- [ ] Adapt the working notebook for Radeon (RDNA) GPUs

## Notes

The Unsloth notebooks were originally authored for the AAI workshop.
