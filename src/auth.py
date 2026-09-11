"""Instagram login via instagrapi, cookie-only.

The session lives only in Streamlit's `session_state` (process memory) for
the duration of the browser tab. It is never written to disk, environment
variables, or logs.

Only cookie-based login (`attempt_login_with_cookie`) is supported: it
sidesteps Instagram's 2FA/challenge flows and instagrapi's device-fingerprint
issues entirely, by reusing a session the user already authenticated in
their own browser.
"""
import json
import re
from dataclasses import dataclass

from instagrapi import Client


@dataclass
class LoginResult:
    status: str  # "success" | "error"
    client: Client | None = None
    error: str | None = None


def new_client() -> Client:
    return Client()


def _extract_sessionid(pasted: str) -> str | None:
    """Pull Instagram's `sessionid` cookie value out of whatever a user
    pastes: a full cookie-export JSON (EditThisCookie, Cookie-Editor and
    similar extensions all export a list of cookie objects with "name"/
    "value" fields, or occasionally a single object), a raw
    "sessionid=VALUE" cookie-header fragment, or just the bare value.
    """
    text = pasted.strip()
    if not text:
        return None

    try:
        data = json.loads(text)
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("name") == "sessionid" and item.get("value"):
                return str(item["value"]).strip()
    except (json.JSONDecodeError, TypeError):
        pass

    match = re.search(r"sessionid=([^;\s\"']+)", text)
    if match:
        return match.group(1).strip()

    # Bare value: Instagram sessionids start with the numeric account id,
    # then a (url-encoded or literal) colon.
    if re.match(r"^\d+(%3A|:)", text):
        return text

    return None


def attempt_login_with_cookie(pasted: str, client: Client | None = None) -> LoginResult:
    """Log in by reusing an already-authenticated Instagram browser session."""
    sessionid = _extract_sessionid(pasted)
    if not sessionid:
        return LoginResult(status="error", error="cookie_not_found")
    client = client or new_client()
    try:
        client.login_by_sessionid(sessionid)
        return LoginResult(status="success", client=client)
    except AssertionError:
        return LoginResult(status="error", error="cookie_invalid")
    except Exception as e:  # noqa: BLE001 - surface any other instagrapi/network failure to the UI
        return LoginResult(status="error", error=str(e))
