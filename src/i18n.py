"""Minimal i18n loader for the Streamlit UI.

Translations live in locales/{lang}.json as flat key -> string maps.
"""
import json
from functools import lru_cache
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
SUPPORTED_LANGUAGES = ("es", "en")
DEFAULT_LANGUAGE = "es"


@lru_cache(maxsize=None)
def _load(lang: str) -> dict:
    path = LOCALES_DIR / f"{lang}.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def translator(lang: str):
    """Return a t(key) function bound to the given language, falling back to English."""
    lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    strings = _load(lang)
    fallback = _load("en") if lang != "en" else {}

    def t(key: str, **kwargs) -> str:
        template = strings.get(key, fallback.get(key, key))
        return template.format(**kwargs) if kwargs else template

    return t
