import pytest

from src import whitelist

USER_A = {"id": "1", "username": "alice"}
USER_B = {"id": "2", "username": "bob"}


def test_should_add_users_when_not_already_whitelisted():
    state = {}
    result = whitelist.add(state, [USER_A, USER_B])
    assert result == [USER_A, USER_B]


def test_should_not_duplicate_users_when_already_whitelisted():
    state = {"whitelist": [USER_A]}
    result = whitelist.add(state, [USER_A, USER_B])
    assert result == [USER_A, USER_B]


def test_should_remove_users_when_ids_match():
    state = {"whitelist": [USER_A, USER_B]}
    result = whitelist.remove(state, {"1"})
    assert result == [USER_B]


def test_should_clear_whitelist():
    state = {"whitelist": [USER_A]}
    result = whitelist.clear(state)
    assert result == []


def test_should_merge_without_duplicates():
    result = whitelist.merge([USER_A], [USER_A, USER_B])
    assert result == [USER_A, USER_B]


def test_should_parse_valid_import():
    parsed = whitelist.parse_import([USER_A, USER_B])
    assert parsed == [USER_A, USER_B]


def test_should_reject_import_when_not_a_list():
    with pytest.raises(ValueError):
        whitelist.parse_import({"id": "1"})


def test_should_reject_import_when_missing_required_fields():
    with pytest.raises(ValueError):
        whitelist.parse_import([{"id": "1"}])
