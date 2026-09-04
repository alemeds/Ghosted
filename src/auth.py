"""Instagram login via instagrapi.

Credentials and the resulting session live only in Streamlit's
`session_state` (process memory) for the duration of the browser tab. They
are never written to disk, environment variables, or logs.

Login is a two-step flow because Instagram may require a 2FA code:
1. `attempt_login(username, password)` -> may return "two_factor_required".
2. `attempt_login(username, password, verification_code=code)` to finish.
"""
from dataclasses import dataclass

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


def attempt_login(username: str, password: str, verification_code: str = "") -> LoginResult:
    client = new_client()
    try:
        client.login(username, password, verification_code=verification_code)
        return LoginResult(status="success", client=client)
    except TwoFactorRequired:
        return LoginResult(status="two_factor_required")
    except ChallengeRequired:
        return LoginResult(status="challenge_required")
    except BadPassword:
        return LoginResult(status="bad_credentials")
    except PleaseWaitFewMinutes as e:
        return LoginResult(status="rate_limited", error=str(e))
    except Exception as e:  # noqa: BLE001 - surface any other instagrapi/network failure to the UI
        return LoginResult(status="error", error=str(e))
