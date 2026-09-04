"""Scan followers/following and compute who doesn't follow back.

Uses instagrapi's cursor-based private-API chunk methods
(`user_following_v1_chunk` / `user_followers_v1_chunk`) so we control the
delay between each page ourselves, the same throttling approach the
original browser-based InstagramUnfollowers tool uses.
"""
import random
import time
from collections.abc import Callable, Iterator

from instagrapi import Client
from instagrapi.types import UserShort

from .timings import Timings

PAGE_SIZE = 100

ProgressCallback = Callable[[str, int], None]
SleepCallback = Callable[[int], None]


def _user_to_dict(user: UserShort) -> dict:
    return {
        "id": str(user.pk),
        "username": user.username,
        "full_name": user.full_name or "",
        "profile_pic_url": str(user.profile_pic_url) if user.profile_pic_url else "",
        "is_private": bool(user.is_private),
        "is_verified": bool(user.is_verified),
    }


def _paginate(
    client: Client,
    user_id: str,
    method_name: str,
    timings: Timings,
    on_progress: ProgressCallback,
    label: str,
) -> Iterator[dict]:
    method = getattr(client, method_name)
    cursor = ""
    page = 0
    seen = 0
    while True:
        chunk, cursor = method(user_id, max_amount=PAGE_SIZE, max_id=cursor)
        for user in chunk:
            seen += 1
            yield _user_to_dict(user)
        page += 1
        on_progress(label, seen)

        if not cursor:
            break

        jitter = timings.between_scan_pages_ms * random.uniform(0.5, 1.0)
        time.sleep(jitter / 1000)

        if page % timings.scan_long_pause_every == 0:
            on_progress("long_pause", timings.scan_long_pause_seconds)
            time.sleep(timings.scan_long_pause_seconds)


def scan_non_followers(
    client: Client,
    timings: Timings,
    on_progress: ProgressCallback,
) -> dict:
    """Return {"following": [...], "non_followers": [...]}."""
    user_id = str(client.user_id)

    following = list(_paginate(client, user_id, "user_following_v1_chunk", timings, on_progress, "following"))
    follower_ids = {
        u["id"] for u in _paginate(client, user_id, "user_followers_v1_chunk", timings, on_progress, "followers")
    }

    non_followers = [u for u in following if u["id"] not in follower_ids]
    return {"following": following, "non_followers": non_followers}
