"""
The language model behind the agent's three LLM calls — classify, extract and
SQL — chosen per question.

The selectable models are listed in config/settings.yaml (`llm.models`): each
has a provider (OpenAI, Anthropic, or the openweight-llm service for Qwen3-8B
with and without the QLoRA adapter). A /query request picks one with "llm";
the controller makes it current for that request with `using()`, so every
call inside — including the SQL steps far down in retrieval/ — runs on the
same model. Without a choice, LLM_DEFAULT (.env) or `llm.default` is used.

    with llm.using("qwen3-8b-lora"):
        text, tokens = llm.complete(messages, max_tokens=500)
"""
from __future__ import annotations

import os
import re
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Iterator, List, Optional, Tuple

from ..settings import LLM_DEFAULT, LLM_MODELS

# The model of the request being answered (None: the default).
_current: ContextVar[Optional[str]] = ContextVar("llm_choice", default=None)

# What each provider needs from .env before its models are offered: every
# entry is required, and any one name of an entry will do (the Claude key may
# be called ANTHROPIC_API_KEY, as the Anthropic SDK expects, or CLAUDE_API_KEY).
_CREDENTIALS = {
    "openai":     (("OPENAI_API_KEY",),),
    "anthropic":  (("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),),
    "openweight": (("QWEN_HOST",), ("QWEN_API_KEY",)),
}


def credential(*names: str) -> Optional[str]:
    """The value of the first of these environment variables that is set."""
    return next((os.getenv(n) for n in names if os.getenv(n)), None)


class UnknownModel(ValueError):
    """A request named a model that config/settings.yaml does not list."""


def default_model() -> str:
    choice = os.getenv("LLM_DEFAULT") or LLM_DEFAULT
    if choice not in LLM_MODELS:
        raise UnknownModel(f"LLM_DEFAULT {choice!r} is not listed under llm.models in config/settings.yaml")
    return choice


def current() -> str:
    """The model id the current request uses."""
    return _current.get() or default_model()


def entry(choice: Optional[str] = None) -> Dict[str, Any]:
    """The settings.yaml entry of a model id (the current one by default)."""
    choice = choice or current()
    if choice not in LLM_MODELS:
        raise UnknownModel(f"unknown model {choice!r} — choose one of {sorted(LLM_MODELS)}")
    return {"id": choice, **LLM_MODELS[choice]}


def configured(choice: str) -> bool:
    """Whether the credentials this model needs are in the environment."""
    return all(credential(*names) for names in _CREDENTIALS[LLM_MODELS[choice]["provider"]])


def options() -> List[Dict[str, Any]]:
    """Every selectable model, for the front end (GET /llms)."""
    return [{"id": m, "label": spec["label"], "provider": spec["provider"], "available": configured(m)}
            for m, spec in LLM_MODELS.items()]


@contextmanager
def using(choice: Optional[str]) -> Iterator[str]:
    """Make `choice` the model for everything inside (None: the default).
    An unknown id raises UnknownModel before anything runs."""
    chosen = entry(choice or default_model())["id"]
    token = _current.set(chosen)
    try:
        yield chosen
    finally:
        _current.reset(token)


def clean(text: str) -> str:
    """Drop a <think> block and a ```json fence if a model adds one — the
    callers expect the bare JSON answer."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()
    fenced = re.match(r"^```[a-zA-Z]*\s*(.*?)\s*```$", text, flags=re.S)
    return fenced.group(1).strip() if fenced else text


def complete(messages: List[Dict[str, str]], max_tokens: int, client: Any = None,
             stage: str = "llm", **meta: Any) -> Tuple[str, int]:
    """Send one chat (system + user messages) to the current model and return
    (answer text, total tokens). `client` is an OpenAI client to reuse, used
    only by OpenAI models. `stage` (classify / extract / sql) and `meta` go into
    the evaluation trace with the tokens and time (agent1/evaluation/trace)."""
    from ..evaluation import trace
    spec = entry()
    provider = spec["provider"]
    started = time.perf_counter()
    if provider == "openai":
        from . import openai_provider as p
        text, inp, out = p.complete(spec, messages, max_tokens, client)
    elif provider == "anthropic":
        from . import anthropic_provider as p
        text, inp, out = p.complete(spec, messages, max_tokens)
    else:
        from . import openweight_provider as p
        text, inp, out = p.complete(spec, messages, max_tokens)
    trace.record_llm(stage, spec["id"], inp, out, (time.perf_counter() - started) * 1000, **meta)
    return clean(text), inp + out
