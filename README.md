# model-fine-tuning

Working repository for LLM fine-tuning notebooks and workshop material, targeting AMD GPUs (Instinct MI300X / ROCm and Radeon / RDNA).

## Layout

```
notebooks/
  unsloth/
    00-start-here-unsloth-studio-on-radeon-cloud.ipynb  START HERE: student landing guide
    llama-3.2-vision-finetune-unsloth.ipynb   Llama 3.2 Vision fine-tune (Unsloth)
    llama-3.1-8b-grpo-unsloth.ipynb           Llama 3.1 8B GRPO (Unsloth), reference
    model-finetuning-on-radeon.ipynb          ACTIVE working notebook (Radeon GPU)
    qwen3_qlora_smoketest.ipynb               Qwen3-4B QLoRA smoke test (Radeon W7900), VERIFIED
    qwen3_qlora_smoketest.executed.ipynb      Same notebook, with saved run outputs
    qwen3-qlora-radeon-w7900-notes.md         Setup notes, gotchas, measured results
    utils_unsloth.py                          Helper module for the vision notebook
scripts/
  build_landing_notebook.py                   Generator for the start-here landing notebook
```

## Start here (new students)

New to fine-tuning? Open
`notebooks/unsloth/00-start-here-unsloth-studio-on-radeon-cloud.ipynb`.

It is a friendly, self-contained landing notebook that:

- explains the core concepts in plain English (LLMs, fine-tuning, SFT, GRPO,
  LoRA, QLoRA, and what training data looks like),
- walks you through launching **Unsloth Studio** on a Radeon Cloud GPU session
  (open a terminal, run `unsloth studio -H 0.0.0.0 -p 8888`, then open the
  secure Cloudflare link it prints),
- and guides you through your first fine-tune inside the Studio UI.

No prior deep-learning experience required. The notebook is regenerated from
`scripts/build_landing_notebook.py` if you want to edit it in plain text.

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
- [x] Unsloth Llama 3.2 Vision fine-tune notebook
- [x] Unsloth Llama 3.1 8B GRPO notebook
- [x] Verified Qwen3-4B QLoRA notebook on Radeon (W7900 / RDNA3)
- [ ] Adapt the working notebook for Radeon (RDNA) GPUs

## Notes

The Unsloth notebooks were originally authored for the AAI workshop.
