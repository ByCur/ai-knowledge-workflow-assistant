import httpx

from google import genai
from google.genai import types

from .config import settings


def _conversation_to_text(
    messages: list[dict],
) -> str:
    parts = []

    for message in messages:
        role = message.get(
            "role",
            "user",
        )

        content = message.get(
            "content",
            "",
        )

        parts.append(
            f"{role.upper()}:\n"
            f"{content}"
        )

    return "\n\n".join(parts)


def generate_chat(
    messages: list[dict],
    json_mode: bool = False,
) -> str:

    provider = (
        settings.ai_provider
        .strip()
        .lower()
    )

    if provider == "ollama":
        return _generate_with_ollama(
            messages=messages,
            json_mode=json_mode,
        )

    if provider == "gemini":
        return _generate_with_gemini(
            messages=messages,
            json_mode=json_mode,
        )

    raise RuntimeError(
        f"Unsupported AI provider: "
        f"{settings.ai_provider}"
    )


def _generate_with_ollama(
    messages: list[dict],
    json_mode: bool,
) -> str:

    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "messages": messages,
        "options": {
            "temperature": 0,
        },
    }

    if json_mode:
        payload["format"] = "json"

    response = httpx.post(
        f"{settings.ollama_url}/api/chat",
        json=payload,
        timeout=120.0,
    )

    response.raise_for_status()

    return (
        response.json()
        ["message"]
        ["content"]
    )


def _generate_with_gemini(
    messages: list[dict],
    json_mode: bool,
) -> str:

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is required "
            "when AI_PROVIDER=gemini"
        )

    client = genai.Client(
        api_key=settings.gemini_api_key
    )

    conversation = (
        _conversation_to_text(
            messages
        )
    )

    config = (
        types.GenerateContentConfig(
            temperature=0,
            response_mime_type=(
                "application/json"
                if json_mode
                else "text/plain"
            ),
        )
    )

    response = (
        client.models.generate_content(
            model=settings.gemini_model,
            contents=conversation,
            config=config,
        )
    )

    return response.text or ""