# Unsloth on AMD ROCm - Workshop Notes (homedev / W7900)

Running notes for the Unsloth-on-AMD demo. Every finding here doubles as slide material.

## Machine inventory

- Host: shailen-homedev (Tailscale 100.106.166.7), login user `shailen`
- OS: Ubuntu 24.04, kernel 6.17.0-35-generic
- GPU: AMD Radeon Pro W7900 (Navi 31, RDNA3, gfx1100, 48 GB)
- CPU/RAM: 31 GB system RAM
- Disk: 457 GB root, ~339 GB free
- Docker: present (user in `docker` group); sudo needs a password (no passwordless sudo)

## Setup timeline (what actually happened)

1. render/video group: user `shailen` was NOT in `render` -> torch would see 0 GPUs.
   Fixed with `sudo usermod -aG render,video shailen`. Group applies to NEW login
   sessions; each fresh SSH picks it up.
2. Ran the Unsloth one-line installer (`curl -fsSL https://unsloth.ai/install.sh | sh`),
   Python pinned to 3.11 via `UNSLOTH_PYTHON=3.11`. Installs into venv
   `~/.unsloth/studio/unsloth_studio`.
3. Installer needed `libcurl4-openssl-dev` (for the GGUF/llama.cpp engine) via sudo;
   installed it manually first (`apt-get install libcurl4-openssl-dev build-essential
   cmake`) so the non-interactive installer would not stall on the sudo prompt.

## GOTCHA #1 (NEW, not in the skill yet): installer misdetects W7900 as CPU-only

On this box the installer printed `gpu none (CPU-only)` and installed `torch==2.10.0+cpu`,
even though the GPU is present and /dev/kfd exists.

Root cause: the installer's KFD-sysfs fallback detection greps for a `gpu_id` line
*inside* `/sys/class/kfd/kfd/topology/nodes/*/properties`:

```
awk '/gpu_id/{ gpu=($2+0>0) } /vendor_id/{ amd=($2==4098) } gpu && amd {found=1}' \
    /sys/class/kfd/kfd/topology/nodes/*/properties
```

But on this kernel (6.17) `gpu_id` is a SEPARATE FILE
(`/sys/class/kfd/kfd/topology/nodes/1/gpu_id`), NOT a line in `properties`. So the
`gpu` flag never flips true and detection returns CPU-only. `vendor_id 4098` (0x1002 AMD)
and `simd_count 192` ARE in properties, so the card is clearly there:

```
/sys/class/kfd/kfd/topology/nodes/1/properties: simd_count 192, vendor_id 4098,
                                                 gfx_target_version 110000  (= gfx1100)
```

The installer has better paths (rocminfo / amd-smi) but neither is installed on a box
without ROCm userspace, so it fell through to the buggy sysfs path.

Fix applied: force-install the ROCm torch stack into the venv, replacing the CPU wheels:

```
~/.unsloth/studio/unsloth_studio/bin/python -m pip install --no-cache-dir \
  --force-reinstall --no-deps \
  --index-url https://download.pytorch.org/whl/rocm7.0 \
  torch==2.10.0+rocm7.0 torchvision==0.25.0+rocm7.0
# (torchaudio 2.10.0+rocm7.0 also installed)
```

IMPORTANT: `pip install torch==2.10.0` (no local tag) treats the already-installed
`2.10.0+cpu` as satisfying the spec and SKIPS the ROCm wheel. You MUST pin the local
version `torch==2.10.0+rocm7.0` AND use `--force-reinstall` to swap it.

Workshop talking point: on a machine with a fresh RDNA3 card but no ROCm userspace,
the auto-installer can guess wrong. Either install ROCm userspace first (so rocminfo/
amd-smi exist) or override the torch wheel manually. This is a great "read the installer
source, verify on real silicon" teaching moment.

## Versions (Unsloth Studio venv, Python 3.11.14)

- torch: 2.10.0+rocm7.0 (swapped from +cpu)
- torchvision: 0.25.0+rocm7.0
- torchaudio: 2.10.0+rocm7.0
- ROCm wheel family: rocm7.0 (download.pytorch.org/whl/rocm7.0)
- unsloth, unsloth-zoo, bitsandbytes, trl, transformers: installed by install.sh
- llama.cpp: prebuilt CPU bundle (b9940-mix); GGUF export path is CPU

## Verification bar (per user)

A version string is NOT proof. Must show:
- torch.cuda.is_available() True, device_count >= 1, get_device_name = W7900
- a real fp16 matmul with measured TFLOP/s
- a real QLoRA train with the loss actually dropping + measured peak VRAM

## Pending / TODO

- [ ] Confirm torch 2.10.0+rocm7.0 imports + sees the W7900 (device_count>0)
- [ ] fp16 matmul TFLOP/s baseline
- [ ] Run qwen3_qlora_smoketest.ipynb end to end (loss drop + peak VRAM)
- [ ] Record measured numbers here for slides

## MEASURED RESULTS (2026-07-10, W7900, SMOKE=1 / 30 steps)

Full smoke test PASSED end to end. All numbers from qwen3_qlora_smoketest_EXECUTED.ipynb.

- torch: 2.10.0+rocm7.0, hip 7.0.51831, ROCm Toolkit 7.0.51831
- GPU seen by Unsloth: AMD gfx1100, Num GPUs = 1, Max memory 44.984 GB, Bfloat16 = TRUE
- fp16 matmul (8192^3): 16.03 ms/iter = 68.6 TFLOP/s
- bitsandbytes: 0.50.0.dev0 (continuous-release_main, PR #1887); 4-bit nf4 round-trip
  clean (no NaN/Inf), gemv_4bit clean
- Model: unsloth/Qwen3-4B-unsloth-bnb-4bit, loaded as Qwen3ForCausalLM
- LoRA: r=16, 7 target modules, trainable 33,030,144 / 2,541,616,640 (1.30%)
- Train: 30 steps, eff batch 16 (1 x 16), seq 1024, FineTome 1k slice
  - runtime: 297.0 s (~9.9 s/step incl. torch inductor compile on early steps)
  - peak reserved VRAM: 5.56 GB (fits easily in the 48 GB card)
  - loss: 1.844 -> 0.813 (delta 1.031) -> real learning, not a no-op
  - GPU utilization observed pinned at 88-100% during training
- Inference (post-train, native path): "In one sentence, QLoRA is a technique that
  enables the training of large language models on devices with limited resources." (correct)
- Adapter saved: adapter_config.json + adapter_model.safetensors + tokenizer files

### Non-fatal warnings (safe to explain away on stage)
- `expandable_segments not supported on this platform` -> ROCm HIP allocator ignores it;
  harmless, VRAM still fits.
- `Could not detect ROCm GPU architecture: rocminfo not found` -> no ROCm userspace on box;
  bnb still works via the gfx1100 kernels in the pre-release wheel. Set BNB_ROCM_ARCH=gfx1100
  to silence. Installing ROCm userspace (rocminfo/amd-smi) would remove ALL these warnings
  AND fix the installer auto-detection (see GOTCHA #1).
- `/opt/amdgpu/share/libdrm/amdgpu.ids: No such file` -> cosmetic libdrm id lookup.
- `IProgress not found` (tqdm) -> cosmetic, just ipywidgets not installed.

### Workshop takeaways
1. RDNA3 (W7900) runs Unsloth 4-bit QLoRA cleanly under ROCm 7.0 / torch 2.10.
2. A 4B model QLoRA needs only ~5.6 GB VRAM; the 48 GB card can go far larger.
3. Biggest setup traps on a bare box: (a) render group, (b) installer misdetecting the
   GPU as CPU-only without ROCm userspace, (c) the bnb pre-release for the 4-bit AMD fix.
4. Installing ROCm userspace up front avoids all three auto-detection issues.

## Artifacts on box (~/unsloth-demo/)
- install.sh, install.log            (Unsloth installer + its log)
- force_torch.sh, rocm_torch_force.log (CPU->ROCm torch swap)
- bnb_rocm.log                        (ROCm bitsandbytes + nbconvert install)
- qwen3_qlora_smoketest.ipynb          (the notebook)
- qwen3_qlora_smoketest_EXECUTED.ipynb (executed, with outputs)
- nbrun.log                            (execution log, NBRUN_RC=0)
- qwen3_4b_qlora_smoketest_adapter/    (saved LoRA adapter)
- hf_cache/                            (HF model cache, ~3.4 GB)
