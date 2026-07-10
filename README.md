# model-fine-tuning

Working repository for LLM fine-tuning notebooks and workshop material, targeting AMD GPUs (Instinct MI300X / ROCm and Radeon / RDNA).

## Layout

```
notebooks/
  unsloth/
    llama-3.2-vision-finetune-unsloth.ipynb   Llama 3.2 Vision fine-tune (Unsloth)
    llama-3.1-8b-grpo-unsloth.ipynb           Llama 3.1 8B GRPO (Unsloth)
    utils_unsloth.py                          Helper module for the vision notebook
```

## Roadmap

- [x] Unsloth Llama 3.2 Vision fine-tune notebook
- [x] Unsloth Llama 3.1 8B GRPO notebook
- [ ] Radeon GPU (RDNA) fine-tuning notebook

## Notes

The Unsloth notebooks were originally authored for the AAI workshop. A dedicated
notebook for Radeon consumer GPUs is in progress.
