#!/usr/bin/env python3
"""Shared content for the Unsloth Studio landing notebooks.

There are two landing notebooks that must stay in sync:

  - model-finetuning-unsloth-radeon.ipynb    (Radeon / RDNA, Radeon Cloud)
  - model-finetuning-unsloth-instinct.ipynb  (Instinct MI300X, AMD Dev Cloud)

The GENERIC teaching content (Part 1 concepts, Part 3 Studio workflow, dataset
guidance, next steps) lives here ONCE and is shared by both. Only the
hardware / access specific bits are parameterized through a per-target `cfg`
dict (see build_landing_notebook.py). This makes the sync rule mechanical:
edit the generic content here and both notebooks regenerate together.

No em dashes anywhere (repo style rule).
"""
import base64
import os


def md(*lines):
    """Markdown cell. Each arg is a line; we add newlines between them."""
    src = "\n".join(lines)
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": src.splitlines(keepends=True) or [""],
    }


def code(*lines):
    src = "\n".join(lines)
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": src.splitlines(keepends=True) or [""],
    }


ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    os.pardir,
    "notebooks",
    "unsloth",
    "assets",
)


def img(name, alt, caption=None):
    """Markdown cell embedding a diagram from assets/ as a base64 data URI.

    The PNG bytes are inlined directly into the markdown as a
    `data:image/png;base64,...` URI. This makes the notebook fully
    self-contained: it renders in JupyterLab and GitHub's notebook viewer
    with no external file dependency, which is required for a PRIVATE repo
    where relative `assets/...` paths 404. Unlike notebook `attachments`,
    a data URI cannot desync from its reference.
    """
    png_path = os.path.join(ASSETS_DIR, f"{name}.png")
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    lines = [f"![{alt}](data:image/png;base64,{b64})"]
    if caption:
        lines += ["", f"*{caption}*"]
    return md(*lines)


def build_cells(cfg):
    """Return the full list of notebook cells for one target.

    `cfg` supplies the hardware / access specific strings. Everything else is
    generic and shared between the Radeon and Instinct notebooks.

    Required cfg keys:
      platform        display name of the environment (e.g. "Radeon Cloud")
      gpu_display     display name of the GPU (e.g. "AMD Instinct MI300X")
      title           full first-line H1 for the title cell
      launch_heading  H1 for the Part 2 launch section
      part2_intro     list of lines for the Part 2 intro paragraph
      step1_terminal  list of lines for "Step 1: Open a terminal"
      vram_note       list of lines for the QLoRA hardware sentence(s)
      studio_note     list of lines: closing note in "Step 2: Start Studio"
      env_check_hint  short string printed by the env-check cell
      troubleshoot_env_fix  fix text for the "command not found" table row
      working_nb_bullet     list of lines for the next-steps working-nb bullet
    """
    cells = []

    # ------------------------------------------------------------ title
    cells.append(md(
        cfg["title"],
        "",
        "Welcome. This is the landing notebook for the workshop. If you have never",
        "fine-tuned a language model before, you are in the right place. By the end",
        "you will understand what fine-tuning is, the main techniques (SFT, LoRA,",
        "QLoRA, GRPO), what training data looks like, and you will have launched",
        "**Unsloth Studio**, a friendly point-and-click app, on a real AMD GPU in",
        "the cloud.",
        "",
        "No prior deep-learning experience is required. Read top to bottom, run the",
        "occasional cell, and follow the boxed steps.",
        "",
        "---",
        "",
        "## What you will do",
        "",
        "1. Learn the core ideas of fine-tuning (a short, plain-English tour).",
        f"2. Launch Unsloth Studio on your {cfg['platform']} GPU session.",
        "3. Open the Studio in your browser through a secure Cloudflare link.",
        "4. Run your first fine-tune, all from a visual interface.",
        "",
        "The step-by-step launch instructions are in the section",
        "**\"Launch Unsloth Studio\"** further down. If you just want to get going,",
        "jump there. If you want to understand *what* you are doing first, keep reading.",
    ))

    # ------------------------------------------------------- part 1 concepts
    cells.append(md(
        "---",
        "",
        "# Part 1: The Concepts (plain English)",
        "",
        "## What is a large language model (LLM)?",
        "",
        "An LLM is a neural network trained on a huge amount of text so that it can",
        "predict the next word (technically, the next *token*) given what came before.",
        "That simple skill, done at scale, is enough to produce models that can chat,",
        "summarize, write code, and reason.",
        "",
        "Models you download from the Hugging Face Hub (Llama, Qwen, Mistral, and",
        "friends) are called **base** or **instruct** models. They are generalists.",
        "",
        "## What is fine-tuning, and why do it?",
        "",
        "Fine-tuning means taking one of those pre-trained models and continuing to",
        "train it a little more on **your** data, so it adapts to **your** task,",
        "domain, tone, or format.",
        "",
        "You fine-tune when you want the model to:",
        "",
        "- Speak in a specific style or persona (your brand voice, a support agent).",
        "- Know a specific domain (legal, medical, your product docs).",
        "- Follow a strict output format (always return JSON, always cite sources).",
        "- Do a narrow task extremely well and cheaply on a smaller model.",
        "",
        "Fine-tuning is often cheaper and more reliable than stuffing everything into",
        "a giant prompt, and it lets a small model punch above its weight.",
    ))

    cells.append(img(
        "01-finetuning-overview",
        "Fine-tuning takes a pre-trained base model, adds your data, and produces a model specialized to your task",
        "Fine-tuning: a general base model plus your data becomes a specialist.",
    ))

    cells.append(md(
        "## The two big families of fine-tuning",
        "",
        "### 1. Supervised Fine-Tuning (SFT)",
        "",
        "You show the model **examples of the right answer**. Each training example is",
        "an input (a question or instruction) paired with the ideal output. The model",
        "learns to imitate those outputs. This is the workhorse of fine-tuning and",
        "where almost everyone starts.",
        "",
        "Think of it as: *\"Here are 1,000 questions and the exact answers I want. Learn",
        "to answer like this.\"*",
        "",
        "### 2. Reinforcement / preference methods (GRPO, DPO, PPO)",
        "",
        "Instead of one gold answer, you steer the model with a **reward signal** or",
        "**preferences** (this answer is better than that one). The model explores and",
        "is nudged toward higher-reward behavior.",
        "",
        "**GRPO** (Group Relative Policy Optimization) is a modern, efficient RL method",
        "popularized by the DeepSeek work. It is great for teaching **reasoning**: the",
        "model generates several candidate answers, they are scored by a reward",
        "function (for example, \"did it get the math right?\"), and the model is pushed",
        "toward the better ones. No human-written gold answer needed for every case,",
        "just a way to score outputs.",
        "",
        "Rule of thumb: **start with SFT.** Reach for GRPO when you want to improve",
        "reasoning or optimize for a reward you can measure, after you have a decent",
        "SFT baseline.",
    ))

    cells.append(img(
        "02-sft-vs-grpo",
        "SFT learns from gold input-output examples; GRPO scores several candidate answers and rewards the best",
        "The two families: SFT imitates gold answers; GRPO rewards the best of several tries.",
    ))

    cells.append(md(
        "## Full fine-tuning vs LoRA vs QLoRA (the memory trick)",
        "",
        "Modern models have billions of parameters. Updating **all** of them (\"full",
        "fine-tuning\") needs a lot of GPU memory and time. Two ideas make this",
        "practical on a single GPU:",
        "",
        "### LoRA (Low-Rank Adaptation)",
        "",
        "Instead of updating the whole model, LoRA **freezes** the original weights and",
        "injects tiny trainable \"adapter\" matrices into a few layers. You train only",
        "those small adapters, often less than 2 percent of the parameters. You get",
        "most of the quality of full fine-tuning for a fraction of the memory, and the",
        "adapter file is small (a few tens of MB) and easy to share.",
        "",
        "### QLoRA (Quantized LoRA)",
        "",
        "QLoRA goes one step further: it **quantizes** the frozen base model to 4-bit",
        "(so it takes roughly a quarter of the memory) and then trains LoRA adapters on",
        "top. This is what lets you fine-tune surprisingly large models on a single",
        "consumer or workstation GPU.",
        "",
        *cfg["vram_note"],
        "",
        "| Method | Trains | Memory | When to use |",
        "| --- | --- | --- | --- |",
        "| Full fine-tune | 100 % of weights | Very high | You have big GPUs and lots of data |",
        "| LoRA | Small adapters (~1-2 %) | Medium | Great default, adapters are portable |",
        "| QLoRA | Adapters on a 4-bit base | Low | Best for single-GPU / limited VRAM |",
    ))

    cells.append(img(
        "03-full-lora-qlora",
        "Full fine-tuning trains all weights (high memory); LoRA freezes the base and trains small adapters; QLoRA quantizes the base to 4-bit then trains adapters (low memory)",
        "The memory trick: freeze the base (LoRA) and quantize it to 4-bit (QLoRA) to fit on one GPU.",
    ))

    cells.append(md(
        "## What does training data look like?",
        "",
        "For **SFT**, the most common shape is a list of examples, each with an",
        "instruction, an optional input, and the desired output. This is the classic",
        "\"Alpaca\" format:",
        "",
        "```json",
        "{\"instruction\": \"Translate to French.\", \"input\": \"Good morning\", \"output\": \"Bonjour\"}",
        "{\"instruction\": \"Summarize in one line.\", \"input\": \"<article text>\", \"output\": \"<summary>\"}",
        "```",
        "",
        "Chat-style datasets instead use a list of messages with roles:",
        "",
        "```json",
        "{\"messages\": [",
        "  {\"role\": \"user\", \"content\": \"What is QLoRA?\"},",
        "  {\"role\": \"assistant\", \"content\": \"QLoRA is 4-bit quantization plus LoRA adapters...\"}",
        "]}",
        "```",
        "",
        "For **GRPO**, you mainly need prompts plus a **reward function** that scores",
        "generated answers (for example, +1 if the final number matches the known",
        "answer). The gold text is optional.",
        "",
        "Quality beats quantity. A few hundred to a few thousand clean, consistent",
        "examples usually beats a huge, noisy pile. In Unsloth Studio you can point at",
        "a Hugging Face dataset or upload your own JSON/JSONL in these shapes.",
    ))

    cells.append(md(
        "## Where Unsloth fits",
        "",
        "[Unsloth](https://github.com/unslothai/unsloth) is a library that makes",
        "fine-tuning **much faster and much lighter on memory** through hand-optimized",
        "kernels, with no loss in accuracy. It supports LoRA and QLoRA out of the box",
        "for popular model families.",
        "",
        "**Unsloth Studio** is the graphical app on top of it. Instead of writing",
        "training code, you:",
        "",
        "1. Pick a model.",
        "2. Pick or upload a dataset.",
        "3. Choose SFT or GRPO and set a few sliders (LoRA rank, steps, learning rate).",
        "4. Click **Train** and watch the loss curve live.",
        "5. Chat with your fine-tuned model to compare it against the base.",
        "",
        "That is the whole loop, and you will do it yourself in a few minutes. Under",
        "the hood it is the exact same SFT / LoRA / QLoRA you just read about.",
    ))

    # -------------------------------------------------------- part 2 launch
    cells.append(md(
        "---",
        "",
        cfg["launch_heading"],
        "",
        *cfg["part2_intro"],
        "",
        "The launch is just two moves: **run one command in a terminal**, then **open",
        "the secure link it prints**.",
    ))

    cells.append(img(
        "05-launch-flow",
        "Run unsloth studio in a terminal, copy the secure Cloudflare link it prints, and open it in your browser",
        "Two moves: run the command, then open the secure Cloudflare link it prints.",
    ))

    cells.append(md(
        "## Step 1: Open a terminal",
        "",
        *cfg["step1_terminal"],
    ))

    cells.append(md(
        "## Step 2: Start Unsloth Studio",
        "",
        "In that terminal, run this single command:",
        "",
        "```bash",
        "unsloth studio -H 0.0.0.0 -p 8888",
        "```",
        "",
        "What the flags mean:",
        "",
        "- `-H 0.0.0.0` tells the app to listen on all network interfaces (needed so",
        "  it can be reached from outside the container).",
        "- `-p 8888` runs it on port 8888.",
        "",
        *cfg["studio_note"],
    ))

    cells.append(md(
        "## Step 3: Open the secure Cloudflare link",
        "",
        "Once Studio is running, it prints a couple of URLs in the terminal. Look for",
        "the line that offers a **secure Cloudflare** address, something like:",
        "",
        "> `Use the secure link access via Cloudflare instead: https://<random-words>.trycloudflare.com`",
        "",
        "**Click that `https://...trycloudflare.com` link** (or copy it into a new",
        "browser tab). That Cloudflare tunnel is the reliable way to reach the Studio",
        "UI from your laptop; prefer it over the raw `0.0.0.0:8888` address, which is",
        "internal to the machine.",
        "",
        "If the browser shows a login screen, enter the password shown in your session",
        "instructions. You should then land on the Unsloth Studio dashboard.",
        "",
        "> Tip: the Cloudflare tunnel can take 10-20 seconds to become reachable, and",
        "> a cold model load on the first request may briefly time out. If the page",
        "> does not load immediately, wait a few seconds and refresh once.",
    ))

    cells.append(md(
        "## Optional: run it in the background",
        "",
        "If you would rather keep the terminal free, you can launch Studio inside",
        "`tmux` so it keeps running even if the terminal tab closes:",
        "",
        "```bash",
        "tmux new -s studio    # start a named session",
        "unsloth studio -H 0.0.0.0 -p 8888",
        "# detach with:  Ctrl-b  then  d",
        "# reattach later with:  tmux attach -t studio",
        "```",
        "",
        "The cell below is a quick sanity check you can run from *this* notebook to",
        "confirm the `unsloth` command exists and the GPU is visible before you head",
        "to the terminal.",
    ))

    cells.append(code(
        "# Quick environment check (safe to run). This does NOT start the Studio;",
        "# it just confirms the tools and GPU are present.",
        "import shutil, subprocess",
        "",
        "unsloth_bin = shutil.which('unsloth')",
        "print('unsloth CLI found at:', unsloth_bin or 'NOT FOUND (check your session image)')",
        "",
        "try:",
        "    import torch",
        "    print('torch:', torch.__version__)",
        "    print('GPU available:', torch.cuda.is_available())",
        "    if torch.cuda.is_available():",
        "        print('GPU:', torch.cuda.get_device_name(0))",
        "except Exception as e:",
        "    print('torch not importable in this kernel:', e)",
        "",
        "print()",
        "print('Now open a terminal and run:  unsloth studio -H 0.0.0.0 -p 8888')",
    ))

    # ---------------------------------------------- part 3 workflow in studio
    cells.append(md(
        "---",
        "",
        "# Part 3: Your first fine-tune inside the Studio",
        "",
        "Once the Studio UI is open, here is the flow to follow. Everything maps back",
        "to the concepts in Part 1.",
    ))

    cells.append(img(
        "04-studio-loop",
        "The Studio loop: pick a model, pick data, choose SFT or QLoRA, train and watch the loss drop, then compare against the base",
        "The whole loop in the Studio UI, the same SFT / LoRA / QLoRA under the hood.",
    ))

    cells.append(md(
        "1. **Choose a model.** Start small, for example a 4-bit Qwen3-4B or a Llama",
        "   3.x 8B instruct. Small models train fast and are perfect for learning.",
        "",
        "2. **Choose a dataset.** Either search the Hugging Face Hub from the UI or",
        "   upload your own JSON/JSONL in the Alpaca or chat format from Part 1. A",
        "   small slice (500 to 1,000 rows) is plenty for a first run.",
        "",
        "3. **Pick the method.** For your first run choose **SFT** with **LoRA/QLoRA**",
        "   (QLoRA is the memory-friendly default). Try **GRPO** later once SFT feels",
        "   familiar.",
        "",
        "4. **Set a few knobs.** Sensible starting points: LoRA rank `r=16`, a short",
        "   run of 30 to 60 steps for a demo, learning rate around `2e-4`. Defaults in",
        "   the Studio are usually fine.",
        "",
        "5. **Click Train.** Watch the **loss curve** go down. A falling loss means the",
        "   model is actually learning from your data (not a no-op).",
        "",
        "6. **Test it.** Use the chat / compare panel to talk to your fine-tuned model",
        "   and compare it against the base model on the same prompt. This is the",
        "   payoff: you can *see* the behavior change.",
        "",
        "7. **Save / export.** Save the LoRA adapter (small, portable) or export a",
        "   merged model / GGUF if you want to run it elsewhere.",
        "",
        "That is a complete fine-tuning cycle. Congratulations, you just trained a",
        "model on an AMD GPU.",
    ))

    # -------------------------------------------------- choosing a dataset
    cells.append(md(
        "---",
        "",
        "## How to choose your dataset (Train > Datasets)",
        "",
        "The Datasets picker bundles **two separate decisions**: *where* the data",
        "comes from (the source) and *what task and format* it is for (which decides",
        "what your fine-tune actually learns). Get both right and training just works.",
        "",
        "### Decision 1: the source (where it loads from)",
        "",
        "- **Hugging Face Hub** : search and pull a public dataset by name (for",
        "  example `mlabonne/FineTome-100k`). Best when a well-known dataset already",
        f"  fits your task. Two gotchas on {cfg['platform']}: the search box is *debounced*,",
        "  so type a real keystroke and wait a moment for results; and the instance",
        "  may be in Hugging Face *offline* mode, so a non-cached dataset can fail with",
        "  `OfflineModeIsEnabled`. If that happens, switch to Local.",
        "- **Local / Upload** : upload your own `JSON` / `JSONL` file. This is the",
        f"  reliable path on {cfg['platform']} and the one to use for your own data.",
        "",
        "### Decision 2: the task and format (what you are teaching)",
        "",
        "This is the part that matters most. Match the dataset shape to the method:",
        "",
        "| Goal | Method | Dataset type | Row format |",
        "| --- | --- | --- | --- |",
        "| Answer in your style / format, or teach domain Q and A | SFT | Instruction (Alpaca) | `{instruction, input, output}` |",
        "| Better general multi-turn chat assistant | SFT | Chat / conversation (ShareGPT) | `{messages: [{role, content}, ...]}` |",
        "| Improve step-by-step reasoning / math | GRPO | Prompts + reward function | prompts (gold answer optional) |",
        "",
        "- **Instruction (Alpaca) format** is the simplest to build yourself. `input`",
        "  can be empty. Great default for a first custom fine-tune.",
        "- **Chat (ShareGPT) format** preserves system / user / assistant roles; use it",
        "  for multi-turn assistants. `FineTome-100k` is a popular example.",
        "- **GRPO** needs mainly prompts plus a way to *score* answers (for example, +1",
        "  if the final number is correct, as with GSM8K). Reach for it after SFT.",
    ))

    cells.append(md(
        "### Quick decision shortcut",
        "",
        "- Want the model to answer in your style / format, or learn your domain Q and",
        "  A -> **SFT + Alpaca** (upload your own JSONL). Start here.",
        "- Want a better general chat assistant -> **SFT + a chat dataset** like",
        "  `FineTome-100k`.",
        "- Want stronger reasoning / math -> **GRPO + a scorable dataset**.",
        "- Just want to see it work end to end -> pick the small preset / example",
        "  dataset (or a 500 to 1,000 row slice). You only need enough to watch the",
        "  loss drop.",
        "",
        "### The one critical rule",
        "",
        "**The format must match the method.** An SFT run expects instruction/output or",
        "messages rows; feed it the wrong shape and training either errors out or",
        "learns nothing (a flat loss curve). If you upload your own file for SFT, keep",
        "it to the exact Alpaca fields:",
        "",
        "```json",
        '{"instruction": "Summarize in one line.", "input": "<article text>", "output": "<summary>"}',
        '{"instruction": "Translate to French.", "input": "Good morning", "output": "Bonjour"}',
        "```",
        "",
        "One JSON object per line for JSONL. `input` may be an empty string when the",
        "instruction is self-contained.",
    ))

    cells.append(md(
        "## Good first experiments",
        "",
        "- **Style transfer:** fine-tune on 300 examples written in a specific tone",
        "  and watch the model adopt it.",
        "- **Format enforcement:** train it to always answer in strict JSON.",
        "- **Tiny domain expert:** feed it Q and A pairs from your product docs.",
        "- **Reasoning with GRPO:** once comfortable, try a math dataset with a reward",
        "  that checks the final answer.",
        "",
        "## Troubleshooting",
        "",
        "| Symptom | Fix |",
        "| --- | --- |",
        "| Cloudflare link does not open | Wait 10-20 s, refresh once; the tunnel needs a moment. |",
        "| First chat response times out | Cold model load. Retry; the warm model responds fast. |",
        "| Out-of-memory during training | Use a smaller model, enable QLoRA (4-bit), lower batch size or sequence length. |",
        "| Loss not decreasing | Raise learning rate a little, train more steps, or check that your dataset format is correct. |",
        f"| `unsloth: command not found` | {cfg['troubleshoot_env_fix']} |",
    ))

    # ---------------------------------------------------------- next steps
    cells.append(md(
        "---",
        "",
        "## Learn more",
        "",
        "- Unsloth: https://github.com/unslothai/unsloth",
        "- Unsloth docs: https://docs.unsloth.ai",
        "- LoRA paper: https://arxiv.org/abs/2106.09685",
        "- QLoRA paper: https://arxiv.org/abs/2305.14314",
        "- GRPO / DeepSeekMath: https://arxiv.org/abs/2402.03300",
        "",
        "Happy fine-tuning.",
    ))

    for i, c in enumerate(cells):
        c["id"] = f"cell-{i:02d}"

    return cells
