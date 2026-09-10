from instagrapi.exceptions import BadPassword, ChallengeRequired, TwoFactorRequired

from src import auth


class FakeClient:
    """Mimics only the instagrapi.Client surface attempt_login() touches."""

    def __init__(self, last_json=None, raise_on_login=None):
        self.last_json = last_json or {}
        self._raise_on_login = raise_on_login
        self.bloks_calls = []

    def login(self, username, password, verification_code=""):
        if self._raise_on_login is not None:
            raise self._raise_on_login
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
