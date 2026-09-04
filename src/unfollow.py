"""Unfollow selected users with the same jittered throttling as the scanner."""
import random
import time
from collections.abc import Callable, Iterator

from instagrapi import Client

from .timings import Timings

UnfollowProgress = Callable[[dict, bool, str | None, int, int], None]


def unfollow_users(
    client: Client,
    users: list[dict],
    timings: Timings,
    on_progress: UnfollowProgress,
    on_long_pause: Callable[[float], None],
) -> Iterator[tuple[dict, bool, str | None]]:
    """Unfollow each user one by one, yielding (user, success, error) as it goes."""
    total = len(users)
    for index, user in enumerate(users, start=1):
        error = None
        try:
            success = client.user_unfollow(user["id"])
        except Exception as e:  # noqa: BLE001 - any instagrapi/network failure is reported, not fatal
            success = False
            error = str(e)

        on_progress(user, success, error, index, total)
        yield user, success, error

        if index == total:
            break

        jitter = timings.between_unfollows_ms * random.uniform(1.0, 1.2)
        time.sleep(jitter / 1000)

        if index % timings.unfollow_long_pause_every == 0:
            pause_seconds = timings.unfollow_long_pause_minutes * 60
            on_long_pause(timings.unfollow_long_pause_minutes)
            time.sleep(pause_seconds)
