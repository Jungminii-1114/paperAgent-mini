"""LLM wrapper merged from GY/SH assignment code."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from paperagent.config import get_settings

OPENAI_MODEL_NAME = "gpt-4o-mini"
LOCAL_MODEL_NAME = "qwen3:8b"
GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
EXAONE_MODEL_NAME = "exaone"


def ask_llm(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    settings = get_settings()
    provider = settings.llm_provider
    model = model or settings.llm_model or _default_model(provider)

    if provider == "ollama":
        return ask_ollama(system_prompt, user_prompt, model)
    if provider == "openai":
        return ask_openai_compatible(
            system_prompt,
            user_prompt,
            model=model,
            base_url=None,
            api_key=os.getenv("OPENAI_API_KEY"),
            missing_key_name="OPENAI_API_KEY",
        )
    if provider == "lmstudio":
        return ask_openai_compatible(
            system_prompt,
            user_prompt,
            model=model,
            base_url=settings.lmstudio_base_url,
            api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio"),
            missing_key_name="LM_STUDIO_API_KEY",
        )
    if provider == "groq":
        return ask_openai_compatible(
            system_prompt,
            user_prompt,
            model=model,
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
            missing_key_name="GROQ_API_KEY",
        )
    if provider == "exaone":
        return ask_openai_compatible(
            system_prompt,
            user_prompt,
            model=model,
            base_url=settings.exaone_base_url,
            api_key=os.getenv("EXAONE_API_KEY", "exaone-local"),
            missing_key_name="EXAONE_API_KEY",
        )

    raise ValueError("LLM_PROVIDER must be one of: openai, ollama, lmstudio, groq, exaone")


def ask_openai_compatible(
    system_prompt: str,
    user_prompt: str,
    model: str,
    base_url: str | None,
    api_key: str | None,
    missing_key_name: str,
) -> str:
    if not api_key:
        raise RuntimeError(f"{missing_key_name} is required for the selected LLM provider.")

    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key) if base_url else OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def ask_ollama(system_prompt: str, user_prompt: str, model: str) -> str:
    settings = get_settings()
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": 0.2},
    }
    request = urllib.request.Request(
        settings.ollama_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. Start it with `ollama serve` "
            "and make sure your model is pulled."
        ) from exc

    return result.get("message", {}).get("content", "")


def _default_model(provider: str) -> str:
    if provider == "openai":
        return OPENAI_MODEL_NAME
    if provider == "groq":
        return GROQ_MODEL_NAME
    if provider == "exaone":
        return EXAONE_MODEL_NAME
    return LOCAL_MODEL_NAME
