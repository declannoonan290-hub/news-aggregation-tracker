from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from .config import MODEL_NAME, USE_SAFETENSORS, SentimentResult
from .util import clean_text


# Lazy globals
_TOKENIZER = None
_MODEL = None
_MODEL_ID2LABEL = None
_USING_FALLBACK = False


def _try_load_finbert() -> bool:
    global _TOKENIZER, _MODEL, _MODEL_ID2LABEL, _USING_FALLBACK
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        _TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME)
        _MODEL = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME,
            use_safetensors=USE_SAFETENSORS,
        )
        _MODEL.eval()
        _MODEL_ID2LABEL = dict(_MODEL.config.id2label)
        _USING_FALLBACK = False
        return True
    except Exception:
        _TOKENIZER = None
        _MODEL = None
        _MODEL_ID2LABEL = None
        _USING_FALLBACK = True
        return False


def _ensure_model_loaded() -> None:
    global _TOKENIZER, _MODEL
    if _TOKENIZER is not None and _MODEL is not None:
        return
    _try_load_finbert()


def _vader(text: str) -> SentimentResult:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text).get("compound", 0.0)
    # map to 3-class
    if score >= 0.05:
        return SentimentResult("Positive", float(min(1.0, abs(score))))
    if score <= -0.05:
        return SentimentResult("Negative", float(min(1.0, abs(score))))
    return SentimentResult("Neutral", float(1.0 - abs(score)))


def predict_sentiment(text: str) -> SentimentResult:
    text = clean_text(text)
    if not text:
        return SentimentResult("Neutral", 0.0)

    _ensure_model_loaded()

    if _TOKENIZER is None or _MODEL is None:
        return _vader(text)

    import torch

    with torch.no_grad():
        inputs = _TOKENIZER(text, return_tensors="pt", truncation=True, max_length=256)
        outputs = _MODEL(**inputs)
        logits = outputs.logits.detach().cpu().numpy().reshape(-1)
        probs = np.exp(logits - np.max(logits))
        probs = probs / probs.sum()

        idx = int(probs.argmax())
        conf = float(probs[idx])

        label_raw = _MODEL_ID2LABEL.get(idx, str(idx)) if _MODEL_ID2LABEL else str(idx)
        label = str(label_raw).strip().capitalize()
        # normalize common variants
        if label.lower().startswith("pos"):
            label = "Positive"
        elif label.lower().startswith("neg"):
            label = "Negative"
        elif label.lower().startswith("neu"):
            label = "Neutral"

        return SentimentResult(label, conf)
