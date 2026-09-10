"""Instagram login via instagrapi.

Credentials and the resulting session live only in Streamlit's
`session_state` (process memory) for the duration of the browser tab. They
are never written to disk, environment variables, or logs.

Login is a two-step flow because Instagram may require a 2FA code:
1. `attempt_login(username, password)` -> may return "two_factor_required".
2. `attempt_login(username, password, verification_code=code)` to finish.
"""
from dataclasses import dataclass
from typing import Any

from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword,
    ChallengeRequired,
    PleaseWaitFewMinutes,
    TwoFactorRequired,
)


@dataclass
class LoginResult:
    status: str  # "success" | "two_factor_required" | "challenge_required" | "bad_credentials" | "rate_limited" | "error"
    client: Client | None = None
    error: str | None = None


def new_client() -> Client:
    return Client()


def _find_two_step_context(data: Any) -> str | None:
    """Dig through instagrapi's raw login response for the Bloks
    `two_step_verification_context` token, wherever it's nested.

    instagrapi keeps this lookup private (`Client._extract_two_step_verification_context`),
    so it's duplicated here rather than reaching into the library's internals.
    """
    if isinstance(data, dict):
        value = data.get("two_step_verification_context")
        if isinstance(value, str) and value.strip():
            return value.strip()
        for v in data.values():
            found = _find_two_step_context(v)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_two_step_context(item)
            if found:
                return found
    return None


def _request_sms_code(client: Client, context: str) -> None:
    """Drive Instagram's Bloks 2FA flow to explicitly ask for an SMS code.

    instagrapi's own login() only selects "sms" as a side effect of
    *submitting* a code (see `_infer_bloks_two_factor_challenge` in
    instagrapi/mixins/auth.py) - it never proactively asks Instagram to
    send one. This replays the same entrypoint -> method_picker ->
    select_method sequence the Instagram app sends when the user taps
    "Send code via SMS", which is the step that was missing.
    """
    client.bloks_two_step_verification_entrypoint(context)
    client.bloks_two_step_verification_method_picker(context)
    client.bloks_two_step_verification_select_method(context, selected_method="sms")


def attempt_login(
    username: str,
    password: str,
    verification_code: str = "",
    client: Client | None = None,
) -> LoginResult:
    """Attempt an Instagram login.

    `client` MUST be the same instance returned from a prior
    "two_factor_required" result when submitting the verification code.
    A fresh Client() generates a new device fingerprint (uuid/phone_id/
    device_id); Instagram does not associate that fingerprint with the
    pending 2FA challenge, so the code is silently rejected or never
    delivered again.
    """
    client = client or new_client()
    try:
        client.login(username, password, verification_code=verification_code)
        return LoginResult(status="success", client=client)
    except TwoFactorRequired:
        # Only act on the FIRST hit (no code submitted yet) - a retry with a
        # wrong code re-raises this too, and re-triggering the SMS send on
        # every failed attempt would spam the user.
        if verification_code:
            return LoginResult(status="two_factor_required", client=client)

        context = _find_two_step_context(getattr(client, "last_json", None))
        if context is None:
            # Legacy accounts (`accounts/two_factor_login/`): instagrapi
            # hardcodes verification_method="3" there, which is not SMS or
            # WhatsApp on the current Instagram API - no code is ever sent.
            # There's no supported way in this instagrapi version to
            # request a specific channel on that endpoint; an authenticator
            # app or backup code still works if the account has one.
            return LoginResult(
                status="two_factor_required",
                client=client,
                error="legacy_unsupported",
            )

        try:
            _request_sms_code(client, context)
        except Exception as e:  # noqa: BLE001 - don't block the code-entry screen on a failed proactive send
            return LoginResult(status="two_factor_required", client=client, error=str(e))
        return LoginResult(status="two_factor_required", client=client)
    except ChallengeRequired:
        return LoginResult(status="challenge_required")
    except BadPassword:
        return LoginResult(status="bad_credentials")
    except PleaseWaitFewMinutes as e:
        return LoginResult(status="rate_limited", error=str(e))
    except Exception as e:  # noqa: BLE001 - surface any other instagrapi/network failure to the UI
        return LoginResult(status="error", error=str(e))
