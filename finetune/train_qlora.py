"""
QLoRA fine-tuning of Qwen3-8B on the agent's three LLM tasks (classify,
extract, SQL), and the first check: base vs tuned accuracy on validation.

Sized for one NVIDIA T4 (16 GB), e.g. an AWS g4dn.xlarge. The T4 has no
bfloat16, so everything runs in float16.

    # 1. token lengths only — tokenizer, no GPU, no torch needed
    python train_qlora.py prepare --train questions_v1_train.jsonl --val questions_v1_val.jsonl

    # 2. score the BASE model on validation (the "before" number)
    python train_qlora.py eval --val questions_v1_val.jsonl --tag base

    # 3. train the adapter
    python train_qlora.py train --train questions_v1_train.jsonl --val questions_v1_val.jsonl \
                                --out adapters/qwen3-8b-v1

    # 4. score the TUNED model on validation (the "after" number)
    python train_qlora.py eval --val questions_v1_val.jsonl --adapter adapters/qwen3-8b-v1 --tag tuned

How an example becomes training data: the prompt is the system + user message
rendered by Qwen3's own chat template with enable_thinking=False — exactly the
prompt the model gets at inference — and the target is the assistant answer
plus <|im_end|>. Loss is computed on the target only, never on the prompt.
Examples longer than --max-len are skipped and reported, never truncated
(truncating would cut the answer off).
"""
from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

MODEL = "Qwen/Qwen3-8B"
END = "<|im_end|>"
MAX_NEW_TOKENS = {"classify": 32, "extract": 384, "sql": 512}


# ═══════════════════════════════════════════════════════════════════════════
# Data — no torch needed
# ═══════════════════════════════════════════════════════════════════════════

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def render_prompt(tokenizer, messages: List[Dict[str, str]]) -> str:
    """System + user, rendered the way inference will render them."""
    return tokenizer.apply_chat_template(messages[:2], tokenize=False, add_generation_prompt=True,
                                         enable_thinking=False)


def encode(tokenizer, example: Dict[str, Any]) -> Dict[str, List[int]]:
    prompt_ids = tokenizer(render_prompt(tokenizer, example["messages"]), add_special_tokens=False).input_ids
    answer_ids = tokenizer(example["messages"][2]["content"] + END, add_special_tokens=False).input_ids
    return {"input_ids": prompt_ids + answer_ids,
            "labels": [-100] * len(prompt_ids) + answer_ids}


def encode_all(tokenizer, examples: List[Dict[str, Any]], max_len: int, name: str) -> List[Dict[str, List[int]]]:
    encoded, too_long, lengths = [], Counter(), defaultdict(list)
    for ex in examples:
        item = encode(tokenizer, ex)
        task = ex.get("meta", {}).get("task", "?")
        lengths[task].append(len(item["input_ids"]))
        if len(item["input_ids"]) > max_len:
            too_long[task] += 1
            continue
        encoded.append(item)
    print(f"{name}: {len(examples)} examples, {len(encoded)} kept (max-len {max_len})")
    for task, ls in sorted(lengths.items()):
        print(f"    {task:<9} n={len(ls):<4} tokens mean {sum(ls) // len(ls):<5} max {max(ls):<5}"
              f" skipped {too_long[task]}")
    return encoded


def load_tokenizer(name: str):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    return tok


# ═══════════════════════════════════════════════════════════════════════════
# Model
# ═══════════════════════════════════════════════════════════════════════════

def load_model_4bit(name: str):
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
                             bnb_4bit_compute_dtype=torch.float16)        # T4: no bfloat16
    return AutoModelForCausalLM.from_pretrained(name, quantization_config=bnb, device_map={"": 0},
                                                dtype=torch.float16, attn_implementation="sdpa")


def collate(pad_id: int):
    import torch

    def fn(batch):
        width = max(len(b["input_ids"]) for b in batch)
        ids = [b["input_ids"] + [pad_id] * (width - len(b["input_ids"])) for b in batch]
        labels = [b["labels"] + [-100] * (width - len(b["labels"])) for b in batch]
        mask = [[1] * len(b["input_ids"]) + [0] * (width - len(b["input_ids"])) for b in batch]
        return {"input_ids": torch.tensor(ids), "labels": torch.tensor(labels), "attention_mask": torch.tensor(mask)}
    return fn


def train(args) -> None:
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import Trainer, TrainingArguments

    tok = load_tokenizer(args.model)
    train_set = encode_all(tok, load_jsonl(args.train), args.max_len, "train")
    val_set = encode_all(tok, load_jsonl(args.val), args.max_len, "val")

    model = load_model_4bit(args.model)
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(model, LoraConfig(
        r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.05, task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
    model.print_trainable_parameters()

    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=args.out, num_train_epochs=args.epochs, learning_rate=args.lr,
            per_device_train_batch_size=1, per_device_eval_batch_size=1, gradient_accumulation_steps=8,
            lr_scheduler_type="cosine", warmup_ratio=0.05, weight_decay=0.0,
            fp16=True, optim="paged_adamw_8bit",
            gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
            logging_steps=5, eval_strategy="epoch", save_strategy="epoch", save_total_limit=2,
            load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False,
            remove_unused_columns=False, report_to="none", seed=42),
        train_dataset=train_set, eval_dataset=val_set, data_collator=collate(tok.pad_token_id))

    started = time.time()
    trainer.train()
    trainer.save_model(args.out)                    # the best epoch, by validation loss
    tok.save_pretrained(args.out)
    print(f"\nTrained in {(time.time() - started) / 60:.1f} min. Best adapter saved to {args.out}")
    for row in trainer.state.log_history:
        if "eval_loss" in row:
            print(f"    epoch {row['epoch']:.0f}: eval_loss {row['eval_loss']:.4f}")


# ═══════════════════════════════════════════════════════════════════════════
# Evaluation — greedy decoding, compare with the gold answer
# ═══════════════════════════════════════════════════════════════════════════

def _strip(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def _sql_key(sql: str) -> str:
    return " ".join(sql.split()).rstrip(";").lower()


def score(task: str, gold: str, pred: str) -> Dict[str, bool]:
    """valid = the answer parses as JSON; correct = it matches the gold answer.
    SQL is compared after normalising whitespace and case, so a statement that
    is correct but written differently counts as wrong here — run it against
    the database for the real check."""
    try:
        p = json.loads(pred)
    except json.JSONDecodeError:
        return {"valid": False, "correct": False}
    g = json.loads(gold)
    if task == "sql":
        return {"valid": isinstance(p, dict) and "sql" in p,
                "correct": isinstance(p, dict) and _sql_key(str(p.get("sql", ""))) == _sql_key(g["sql"])}
    return {"valid": True, "correct": p == g}


def evaluate(args) -> None:
    import torch

    tok = load_tokenizer(args.model)
    model = load_model_4bit(args.model)
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter)
    model.eval()
    end_id = tok.convert_tokens_to_ids(END)

    try:                                            # SQL safety check, if the agent code is importable
        from agent1.retrieval.sql_writer import validate_sql
    except Exception:                               # noqa: BLE001
        validate_sql = None

    examples = load_jsonl(args.val)
    results, totals = [], defaultdict(Counter)
    for i, ex in enumerate(examples, 1):
        task = ex["meta"]["task"]
        prompt = tok(render_prompt(tok, ex["messages"]), return_tensors="pt", add_special_tokens=False).to(0)
        started = time.time()
        with torch.no_grad():
            out = model.generate(**prompt, max_new_tokens=MAX_NEW_TOKENS[task], do_sample=False,
                                 eos_token_id=end_id, pad_token_id=tok.pad_token_id)
        seconds = time.time() - started
        pred = _strip(tok.decode(out[0][prompt["input_ids"].shape[1]:], skip_special_tokens=True))
        s = score(task, ex["messages"][2]["content"], pred)
        if task == "sql" and validate_sql and s["valid"]:
            try:
                validate_sql(json.loads(pred)["sql"])
                s["safe"] = True
            except Exception:                       # noqa: BLE001
                s["safe"] = False
        totals[task].update({"n": 1, **{k: int(v) for k, v in s.items()}})
        totals[task]["seconds"] += seconds
        results.append({"line": i, **ex["meta"], "gold": ex["messages"][2]["content"], "pred": pred,
                        **s, "seconds": round(seconds, 2)})
        print(f"  [{i}/{len(examples)}] {task:<8} {'ok ' if s['correct'] else 'BAD'} {seconds:5.1f}s")

    out_path = Path(args.val).with_name(f"eval_{args.tag}.jsonl")
    out_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n", encoding="utf-8")
    print(f"\n{args.tag}: {args.adapter or args.model}")
    print(f"  {'task':<9}{'n':>4}{'valid JSON':>12}{'correct':>10}{'safe SQL':>10}{'s/answer':>10}")
    for task in ("classify", "extract", "sql"):
        t = totals.get(task)
        if not t:
            continue
        safe = f"{t['safe'] / t['n']:.0%}" if task == "sql" and validate_sql else "-"
        print(f"  {task:<9}{t['n']:>4}{t['valid'] / t['n']:>12.0%}{t['correct'] / t['n']:>10.0%}"
              f"{safe:>10}{t['seconds'] / t['n']:>10.1f}")
    print(f"  every answer, gold vs predicted: {out_path}")


# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "train", "eval"):
        p = sub.add_parser(name)
        p.add_argument("--model", default=MODEL)
        p.add_argument("--val", required=True)
        p.add_argument("--max-len", type=int, default=2048)
        if name in ("prepare", "train"):
            p.add_argument("--train", required=True)
        if name == "train":
            p.add_argument("--out", required=True)
            p.add_argument("--epochs", type=float, default=3)
            p.add_argument("--lr", type=float, default=2e-4)
            p.add_argument("--rank", type=int, default=16)
        if name == "eval":
            p.add_argument("--adapter", default=None)
            p.add_argument("--tag", default="base")
    args = ap.parse_args()

    if args.cmd == "prepare":
        tok = load_tokenizer(args.model)
        encode_all(tok, load_jsonl(args.train), args.max_len, "train")
        encode_all(tok, load_jsonl(args.val), args.max_len, "val")
        sample = load_jsonl(args.val)[0]
        print("\nOne example as the model sees it (prompt end + target):\n")
        print("..." + render_prompt(tok, sample["messages"])[-300:] + sample["messages"][2]["content"] + END)
    elif args.cmd == "train":
        train(args)
    else:
        evaluate(args)


if __name__ == "__main__":
    main()
