from src import auth


class FakeClient:
    """Mimics only the instagrapi.Client surface attempt_login_with_cookie() touches."""

    def __init__(self, raise_on_sessionid=None):
        self._raise_on_sessionid = raise_on_sessionid
        self.sessionid_used = None

    def login_by_sessionid(self, sessionid):
        if self._raise_on_sessionid is not None:
            raise self._raise_on_sessionid
        self.sessionid_used = sessionid
        return True


def test_extract_sessionid_should_read_value_from_cookie_export_list():
    export = '[{"name": "csrftoken", "value": "abc"}, {"name": "sessionid", "value": "123:XYZ:1"}]'
    assert auth._extract_sessionid(export) == "123:XYZ:1"


def test_extract_sessionid_should_read_value_from_single_cookie_object():
    export = '{"name": "sessionid", "value": "123:XYZ:1"}'
    assert auth._extract_sessionid(export) == "123:XYZ:1"


def test_extract_sessionid_should_read_cookie_header_fragment():
    assert auth._extract_sessionid("csrftoken=abc; sessionid=123:XYZ:1; ds_user_id=123") == "123:XYZ:1"


def test_extract_sessionid_should_accept_bare_value():
    assert auth._extract_sessionid("  123%3AXYZ%3A1  ") == "123%3AXYZ%3A1"


def test_extract_sessionid_should_return_none_when_not_found():
    assert auth._extract_sessionid('[{"name": "csrftoken", "value": "abc"}]') is None
    assert auth._extract_sessionid("not a cookie at all") is None
    assert auth._extract_sessionid("") is None


def test_should_log_in_with_cookie_when_sessionid_found():
    client = FakeClient()
    result = auth.attempt_login_with_cookie('[{"name": "sessionid", "value": "123:XYZ:1"}]', client=client)
    assert result.status == "success"
    assert client.sessionid_used == "123:XYZ:1"


def test_should_fail_with_cookie_not_found_when_no_sessionid_in_pasted_text():
    client = FakeClient()
    result = auth.attempt_login_with_cookie('[{"name": "csrftoken", "value": "abc"}]', client=client)
    assert result.status == "error"
    assert result.error == "cookie_not_found"


def test_should_fail_with_cookie_invalid_when_sessionid_malformed():
    client = FakeClient(raise_on_sessionid=AssertionError("Invalid sessionid"))
    result = auth.attempt_login_with_cookie("123:XYZ:1", client=client)
    assert result.status == "error"
    assert result.error == "cookie_invalid"
