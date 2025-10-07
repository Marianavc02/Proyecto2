# SBDToolBox/ai/descriptions.py

import textwrap

import requests
from django.conf import settings

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # rápido y barato

SYSTEM_PROMPT = (
    "Eres un asistente que escribe mini-descripciones técnicas, claras y concisas "
    "en español colombiano. 40–60 palabras. No inventes datos; usa solo nombre, "
    "SKU, empresa y categoría. Sin precios ni garantías, sin emojis."
)


def _has_key() -> bool:
    return bool(getattr(settings, "GROQ_API_KEY", ""))


def generate_product_blurb(nombre: str, sku: str, empresa: str | None, categoria: str | None) -> str | None:
    """
    Devuelve una mini-descripción o None si no hay API key / error.
    """
    if not _has_key():
        return None

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": textwrap.dedent(
                    f"""
                Nombre: {nombre or '-'}
                SKU: {sku or '-'}
                Empresa: {empresa or '-'}
                Categoría: {categoria or '-'}
                Escribe una mini-descripción (40–60 palabras), 1 párrafo, sin emojis.
            """
                ).strip(),
            },
        ],
        "temperature": 0.3,
        "max_tokens": 120,
    }

    try:
        resp = requests.post(
            GROQ_ENDPOINT,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=5,
        )
        resp.raise_for_status()
        txt = resp.json()["choices"][0]["message"]["content"].strip()
        # Limpieza defensiva y recorte duro:
        return " ".join(txt.split())[:600]
    except Exception:
        return None
