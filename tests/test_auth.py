from instagrapi.exceptions import BadPassword, ChallengeRequired, TwoFactorRequired

from src import auth


class FakeClient:
    """Mimics only the instagrapi.Client surface attempt_login() touches."""

    def __init__(self, last_json=None, raise_on_login=None, raise_on_sessionid=None):
        self.last_json = last_json or {}
        self._raise_on_login = raise_on_login
        self._raise_on_sessionid = raise_on_sessionid
        self.bloks_calls = []
        self.sessionid_used = None

    def login(self, username, password, verification_code=""):
        if self._raise_on_login is not None:
            raise self._raise_on_login
        return True

    def login_by_sessionid(self, sessionid):
        if self._raise_on_sessionid is not None:
            raise self._raise_on_sessionid
        self.sessionid_used = sessionid
        return True

    def bloks_two_step_verification_entrypoint(self, context):
        self.bloks_calls.append(("entrypoint", context))

    def bloks_two_step_verification_method_picker(self, context):
        self.bloks_calls.append(("method_picker", context))

    def bloks_two_step_verification_select_method(self, context, selected_method):
        self.bloks_calls.append(("select_method", context, selected_method))


def test_should_return_success_when_login_succeeds():
    client = FakeClient()
    result = auth.attempt_login("user", "pass", client=client)
    assert result.status == "success"
    assert result.client is client


def test_should_request_sms_when_two_factor_required_with_bloks_context():
    last_json = {"step_data": {"two_step_verification_context": "ctx-123"}}
    client = FakeClient(last_json=last_json, raise_on_login=TwoFactorRequired())
    result = auth.attempt_login("user", "pass", client=client)
    assert result.status == "two_factor_required"
    assert result.error is None
    assert client.bloks_calls == [
        ("entrypoint", "ctx-123"),
        ("method_picker", "ctx-123"),
        ("select_method", "ctx-123", "sms"),
    ]


def test_should_not_resend_sms_on_retry_with_wrong_code():
    last_json = {"two_step_verification_context": "ctx-123"}
    client = FakeClient(last_json=last_json, raise_on_login=TwoFactorRequired())
    result = auth.attempt_login("user", "pass", verification_code="000000", client=client)
    assert result.status == "two_factor_required"
    assert client.bloks_calls == []


def test_should_flag_legacy_unsupported_when_no_bloks_context():
    client = FakeClient(last_json={"two_factor_info": {"two_factor_identifier": "abc"}}, raise_on_login=TwoFactorRequired())
    result = auth.attempt_login("user", "pass", client=client)
    assert result.status == "two_factor_required"
    assert result.error == "legacy_unsupported"
    assert client.bloks_calls == []


def test_should_report_bad_credentials():
    client = FakeClient(raise_on_login=BadPassword())
    result = auth.attempt_login("user", "wrong", client=client)
    assert result.status == "bad_credentials"


def test_should_report_challenge_required():
    client = FakeClient(raise_on_login=ChallengeRequired())
    result = auth.attempt_login("user", "pass", client=client)
    assert result.status == "challenge_required"


def test_find_two_step_context_should_locate_nested_value():
    data = {"a": [{"b": {}}, {"two_step_verification_context": "  deep-ctx  "}]}
    assert auth._find_two_step_context(data) == "deep-ctx"


def test_find_two_step_context_should_return_none_when_absent():
    assert auth._find_two_step_context({"a": {"b": 1}}) is None


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
