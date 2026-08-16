"""Fast local LLM client for grounded answer generation.

Loads a small instruct model once and serves requests with retry + fallback:
primary model → retry → template-based extractive answer from the top chunk.

The fallback keeps the pipeline alive even when the model hops fail, at the
cost of a lower confidence label (the orchestrator marks the response degraded).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import torch

from backend.app.config import DEVICE, LLM_FALLBACK_MODEL, LLM_MAX_NEW_TOKENS, LLM_MODEL

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a retrieval-grounded question answering assistant. Answer strictly "
    "from the passages provided below. If the passages do not contain the answer, "
    "say you cannot find the answer. Be concise — one or two sentences. English."
)


def _build_prompt(query: str, contexts: List[str]) -> str:
    passages = "\n\n".join(f"[{i + 1}] {text}" for i, text in enumerate(contexts))
    return (
        f"Passages:\n{passages}\n\nQuestion: {query}\nAnswer:"
    )


def _extractive_fallback(query: str, contexts: List[str]) -> str:
    """Deterministic fallback: pull the most query-related sentence."""
    query_tokens = set(query.lower().split())
    best_sentence, best_score = "", 0.0
    for text in contexts:
        for sentence in text.replace("\n", " ").split(". "):
            sentence = sentence.strip().rstrip(".")
            if not sentence:
                continue
            stok = set(sentence.lower().split())
            score = len(query_tokens & stok)
            if len(stok) > 0 and score > best_score:
                best_score, best_sentence = score, sentence
    return best_sentence or (contexts[0] if contexts else "")


class LLMClient:
    def __init__(self) -> None:
        self.model = None
        self.tokenizer = None
        self._primary_ok = True
        self.failed_primary = False

    def _load(self) -> None:
        if self.model is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_id = LLM_MODEL
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if DEVICE.startswith("cuda") else torch.float32,
                device_map=DEVICE,
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
        except Exception as exc:  # fall back to the fallback model
            logger.warning("Primary LLM load failed (%s); trying %s", exc, LLM_FALLBACK_MODEL)
            self.failed_primary = True
            model_id = LLM_FALLBACK_MODEL
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if DEVICE.startswith("cuda") else torch.float32,
                device_map=DEVICE,
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

    def generate(
        self,
        query: str,
        contexts: List[str],
        max_new_tokens: int = LLM_MAX_NEW_TOKENS,
    ) -> Dict[str, Any]:
        """Return {answer, degraded, ms} — never raises."""
        t0 = time.perf_counter()
        try:
            self._load()
            prompt = _build_prompt(query, contexts)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    num_beams=1,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
            answer = self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
            answer = answer.split("Answer:")[-1].strip()
            if not answer:
                raise RuntimeError("empty generation")
            return {"answer": answer, "degraded": False, "ms": int((time.perf_counter() - t0) * 1000)}
        except Exception as exc:
            logger.warning("LLM generation failed (%s); falling back to extractive", exc)
            answer = _extractive_fallback(query, contexts[:3])
            return {"answer": answer, "degraded": True, "ms": int((time.perf_counter() - t0) * 1000)}

    def warmup(self) -> None:
        self._load()


_client: Optional[LLMClient] = None


def get_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client