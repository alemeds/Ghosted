"""Timing/delay configuration used to throttle scan and unfollow requests.

Mirrors the rate-limiting approach of the original InstagramUnfollowers
browser tool: jittered pauses between paginated requests, plus a longer
pause every N requests to avoid tripping Instagram's temporary blocks.
"""
from dataclasses import dataclass


@dataclass
class Timings:
    between_scan_pages_ms: int = 1000
    scan_long_pause_every: int = 6
    scan_long_pause_seconds: int = 10

    between_unfollows_ms: int = 4000
    unfollow_long_pause_every: int = 5
    unfollow_long_pause_minutes: float = 5.0


def default_timings() -> Timings:
    return Timings()


def validate(timings: Timings) -> Timings:
    """Clamp values to sane, non-abusive ranges before they're used."""
    return Timings(
        between_scan_pages_ms=max(300, timings.between_scan_pages_ms),
        scan_long_pause_every=max(1, timings.scan_long_pause_every),
        scan_long_pause_seconds=max(1, timings.scan_long_pause_seconds),
        between_unfollows_ms=max(1500, timings.between_unfollows_ms),
        unfollow_long_pause_every=max(1, timings.unfollow_long_pause_every),
        unfollow_long_pause_minutes=max(0.5, timings.unfollow_long_pause_minutes),
    )
