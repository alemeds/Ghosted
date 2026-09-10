from types import SimpleNamespace

from src.scanner import scan_non_followers
from src.timings import Timings


def _fake_user(pk, username):
    return SimpleNamespace(
        pk=pk,
        username=username,
        full_name=f"Name {username}",
        profile_pic_url=f"https://example.com/{username}.jpg",
        is_private=False,
        is_verified=False,
    )


class FakeClient:
    """Mimics the two instagrapi chunk methods used by the scanner, paginating in fixed-size pages."""

    def __init__(self, following_ids, follower_ids, user_id="me", page_size=2, fail_followers_after_page=None):
        self.user_id = user_id
        self._following = [_fake_user(i, f"user{i}") for i in following_ids]
        self._followers = [_fake_user(i, f"user{i}") for i in follower_ids]
        self.page_size = page_size
        self._fail_followers_after_page = fail_followers_after_page
        self._followers_pages_served = 0

    def _chunk(self, pool, max_id):
        start = int(max_id) if max_id else 0
        end = start + self.page_size
        page = pool[start:end]
        next_cursor = str(end) if end < len(pool) else ""
        return page, next_cursor

    def user_following_v1_chunk(self, user_id, max_amount=0, max_id=""):
        return self._chunk(self._following, max_id)

    def user_followers_v1_chunk(self, user_id, max_amount=0, max_id=""):
        if self._fail_followers_after_page is not None and self._followers_pages_served >= self._fail_followers_after_page:
            raise RuntimeError("simulated rate limit")
        self._followers_pages_served += 1
        return self._chunk(self._followers, max_id)


FAST_TIMINGS = Timings(
    between_scan_pages_ms=1,
    scan_long_pause_every=1000,
    scan_long_pause_seconds=0,
    between_unfollows_ms=1,
    unfollow_long_pause_every=1000,
    unfollow_long_pause_minutes=0,
)


def test_should_find_no_non_followers_when_everyone_follows_back():
    client = FakeClient(following_ids=[1, 2, 3], follower_ids=[1, 2, 3])
    result = scan_non_followers(client, FAST_TIMINGS, lambda *_: None)
    assert result["non_followers"] == []
    assert len(result["following"]) == 3


def test_should_find_non_followers_across_paginated_results():
    client = FakeClient(following_ids=[1, 2, 3, 4, 5], follower_ids=[2, 4], page_size=2)
    result = scan_non_followers(client, FAST_TIMINGS, lambda *_: None)
    non_follower_ids = {u["id"] for u in result["non_followers"]}
    assert non_follower_ids == {"1", "3", "5"}


def test_should_report_progress_for_each_page():
    client = FakeClient(following_ids=[1, 2, 3, 4], follower_ids=[1], page_size=2)
    progress_calls = []
    scan_non_followers(client, FAST_TIMINGS, lambda label, count: progress_calls.append((label, count)))
    assert ("following", 2) in progress_calls
    assert ("following", 4) in progress_calls


def test_should_keep_partial_results_when_followers_phase_fails():
    client = FakeClient(
        following_ids=[1, 2, 3, 4],
        follower_ids=[1, 2, 3, 4],
        page_size=2,
        fail_followers_after_page=0,
    )
    result = scan_non_followers(client, FAST_TIMINGS, lambda *_: None)
    assert result["error"] == "simulated rate limit"
    assert len(result["following"]) == 4  # completed before the failure
    assert result["following"][0]["username"] == "user1"


def test_should_have_no_error_on_a_clean_scan():
    client = FakeClient(following_ids=[1, 2], follower_ids=[1])
    result = scan_non_followers(client, FAST_TIMINGS, lambda *_: None)
    assert result["error"] is None
