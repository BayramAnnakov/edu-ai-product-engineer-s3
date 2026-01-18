"""LLM helper utilities for provider configuration."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL_MAP = {
    "gpt-5-mini": "openai/gpt-4o-mini",
    "gpt-5.2": "openai/gpt-4o",
}


def _resolve_model(model: str) -> str:
    if os.getenv("OPENROUTER_API_KEY"):
        return OPENROUTER_MODEL_MAP.get(model, model)
    return model


def get_chat_model(model: str, temperature: float = 0) -> ChatOpenAI:
    """Create a ChatOpenAI client configured for OpenAI or OpenRouter."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")

    if os.getenv("OPENROUTER_API_KEY"):
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = base_url or OPENROUTER_BASE_URL

    if not api_key:
        raise ValueError(
            "Missing API key. Set OPENAI_API_KEY or OPENROUTER_API_KEY in your environment."
        )

    return ChatOpenAI(
        model=_resolve_model(model),
        temperature=temperature,
        api_key=api_key,
        base_url=base_url,
    )
