# model-fine-tuning

Working repository for LLM fine-tuning notebooks and workshop material, targeting AMD GPUs (Instinct MI300X / ROCm and Radeon / RDNA).

## Layout

```
notebooks/
  unsloth/
    llama-3.2-vision-finetune-unsloth.ipynb   Llama 3.2 Vision fine-tune (Unsloth)
    llama-3.1-8b-grpo-unsloth.ipynb           Llama 3.1 8B GRPO (Unsloth), reference
    model-finetuning-on-radeon.ipynb          ACTIVE working notebook (Radeon GPU)
    utils_unsloth.py                          Helper module for the vision notebook
```

## Working notebook

`notebooks/unsloth/model-finetuning-on-radeon.ipynb` is the active working
notebook. It started as a copy of the Llama 3.1 8B GRPO notebook and is being
adapted for Radeon (RDNA) consumer GPUs.

## Roadmap

- [x] Unsloth Llama 3.2 Vision fine-tune notebook
- [x] Unsloth Llama 3.1 8B GRPO notebook
- [ ] Adapt the working notebook for Radeon (RDNA) GPUs

## Notes

The Unsloth notebooks were originally authored for the AAI workshop.
