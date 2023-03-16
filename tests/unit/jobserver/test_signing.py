import json
import secrets
from datetime import timedelta

import pytest
from django.utils import timezone
from pydantic import ValidationError
from pydantic.json import pydantic_encoder

from jobserver import signing


@pytest.fixture
def secret_key():
    return secrets.token_hex(32)


def create_raw_token(value, key, salt=None):
    """To be used to create bad tokens that AuthToken won't let you create."""
    signer = signing.create_signer(key, salt)
    if isinstance(value, dict | list):
        value = json.dumps(value, default=pydantic_encoder)
    return signer.sign(value).decode("utf8")


def test_token_sign_verify_roundtrip(secret_key):
    token1 = signing.AuthToken(
        url="https://example.com/url",
        user="user",
        expiry=timezone.now() + timedelta(minutes=1),
    )
    token_string = token1.sign(secret_key, "salt")

    token2 = signing.AuthToken.verify(token_string, secret_key, "salt")
    assert token1 == token2


def test_token_object_url_invalid():
    with pytest.raises(ValidationError):
        signing.AuthToken(
            url="bad",
            user="user",
            expiry=timezone.now() + timedelta(minutes=1),
        )


def test_token_object_expired():
    with pytest.raises(signing.AuthToken.Expired):
        signing.AuthToken(
            url="https://example.com/url",
            user="user",
            expiry=timezone.now() - timedelta(minutes=1),
        )


def test_token_verify_mismatched_secrets():
    payload = dict(
        url="https://example.com/url",
        user="user",
        expiry=timezone.now() + timedelta(minutes=1),
    )
    token = create_raw_token(payload, "secret1" * 10)

    with pytest.raises(ValidationError):
        signing.AuthToken.verify(token, "secret2" * 10)


def test_token_verify_bad_payload_format(secret_key):
    payload = "not a json object"

    token = create_raw_token(payload, secret_key)
    with pytest.raises(ValidationError):
        signing.AuthToken.verify(token, secret_key)


def test_token_verify_expired(secret_key):
    payload = dict(
        url="https://example.com/url",
        user="user",
        expiry=timezone.now() - timedelta(minutes=1),
    )
    token = create_raw_token(payload, secret_key)
    with pytest.raises(signing.AuthToken.Expired):
        signing.AuthToken.verify(token, secret_key)


def test_token_verify_wrong_all_the_things(secret_key):
    payload = dict(
        url="bad url",
        # missing user
        expiry=timezone.now() - timedelta(minutes=1),
    )
    token = create_raw_token(payload, secret_key)
    with pytest.raises(ValidationError) as exc_info:
        signing.AuthToken.verify(token, secret_key)

    errors = {e["loc"][0]: e for e in exc_info.value.errors()}
    assert "url" in errors
    assert "user" in errors
    assert "expiry" in errors
