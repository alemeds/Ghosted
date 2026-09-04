"""Whitelist management: accounts the user never wants to unfollow.

Lives only in Streamlit's session_state (in-memory, per session) since this
tool is meant for occasional use, not a persistent multi-run service. Users
who want continuity across sessions can export/import it as JSON.
"""
from typing import Any


def load(session_state) -> list[dict]:
    return session_state.get("whitelist", [])


def save(session_state, whitelist: list[dict]) -> None:
    session_state["whitelist"] = whitelist


def add(session_state, users: list[dict]) -> list[dict]:
    current = load(session_state)
    existing_ids = {u["id"] for u in current}
    merged = current + [u for u in users if u["id"] not in existing_ids]
    save(session_state, merged)
    return merged


def remove(session_state, user_ids: set[str]) -> list[dict]:
    current = [u for u in load(session_state) if u["id"] not in user_ids]
    save(session_state, current)
    return current


def clear(session_state) -> list[dict]:
    save(session_state, [])
    return []


def merge(existing: list[dict], imported: list[dict]) -> list[dict]:
    existing_ids = {u["id"] for u in existing}
    return existing + [u for u in imported if u["id"] not in existing_ids]


def parse_import(raw: Any) -> list[dict]:
    """Validate imported whitelist JSON, raising ValueError with a clear message."""
    if not isinstance(raw, list):
        raise ValueError("expected a JSON array of users")
    for user in raw:
        if not isinstance(user, dict) or not isinstance(user.get("id"), str) or not isinstance(user.get("username"), str):
            raise ValueError("each user needs at least string 'id' and 'username' fields")
    return raw
