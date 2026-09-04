from src.timings import Timings, default_timings, validate


def test_should_return_sane_defaults():
    timings = default_timings()
    assert timings.between_scan_pages_ms > 0
    assert timings.between_unfollows_ms > 0


def test_should_clamp_values_below_minimum():
    timings = Timings(
        between_scan_pages_ms=0,
        scan_long_pause_every=0,
        scan_long_pause_seconds=0,
        between_unfollows_ms=0,
        unfollow_long_pause_every=0,
        unfollow_long_pause_minutes=0,
    )
    clamped = validate(timings)
    assert clamped.between_scan_pages_ms >= 300
    assert clamped.scan_long_pause_every >= 1
    assert clamped.scan_long_pause_seconds >= 1
    assert clamped.between_unfollows_ms >= 1500
    assert clamped.unfollow_long_pause_every >= 1
    assert clamped.unfollow_long_pause_minutes >= 0.5


def test_should_preserve_values_above_minimum():
    timings = Timings(
        between_scan_pages_ms=2000,
        scan_long_pause_every=10,
        scan_long_pause_seconds=20,
        between_unfollows_ms=6000,
        unfollow_long_pause_every=8,
        unfollow_long_pause_minutes=3,
    )
    assert validate(timings) == timings
