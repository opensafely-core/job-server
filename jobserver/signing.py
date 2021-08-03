import hashlib
from datetime import datetime, timezone

import itsdangerous
from pydantic import BaseModel, Field, ValidationError, root_validator, validator


def create_signer(secret_key, salt):
    """Create a signer configured how we like it.

    The secret_key should be a cyptographically random key.

    The salt should be specific to intend usage of the signature, but does not
    need to be random. It acts to partition signatures between use cases that
    shared the same secret_key.

    The length of secret_key and salt together should be more than the digest
    size, which for sha256 is 32 bytes.

    See https://itsdangerous.palletsprojects.com/en/2.0.x/concepts/ for more info.

    Ideally, we'd use cryptography for this, but that's a much heavier
    dependency than itsdangerous, which is pure python."""
    value = secret_key
    if salt is not None:
        value += salt
    assert len(value.encode("utf8")) > 32, "secret_key+salt needs to be > 32 bytes"
    return itsdangerous.Signer(
        secret_key=secret_key,
        salt=salt,
        key_derivation="hmac",  # would like to use HDKF, but not supported
        digest_method=hashlib.sha256,
    )


class AuthToken(BaseModel):
    """A signed auth token.

    The signed format is a json serialized version of this model, with
    a signature.

    This model includes all the logic needed to generate, sign, parse and
    validate a signed auth token. This is so that we can ensure that it is very
    difficult to create an invalid token by accident, and so in future we can
    share one implementation of this token between projects.

    Note: we sign the full url, rather than including business concepts like
    'workspace' or 'release', and signing those. The assumption here is that
    the url path will include a business scope, e.g.
    `https://example.com/workspaces/MYWORKSPACE`, and that all urls under this
    prefix are valid for this token.

    This gives us a few benefits:

    1) more generic token format that can be used on different parts of the system.
    2) including the full domain prevents cross backend token usage
    3) validating the url makes it easier for web frameworks to automatically
       apply the validation, as they don't need to understand the business logic.

    """

    url: str = Field(
        description="Full url prefix the token is valid for, e.g. http://domain.com/path/arg"
    )
    user: str = Field(decription="The user this token was signed for")
    expiry: datetime = Field(description="UTC datetime after which this token expires")

    class Config:
        # do not allow anyone to set values after instantiation
        allow_mutation = False

    class Expired(Exception):
        pass

    @validator("url")
    def check_url(cls, url):
        """Enforce that we need a fully qualified url."""
        if url.startswith(("http://", "https://")):
            return url
        raise ValueError(f"Invalid url {url}")

    @validator("expiry")
    def check_expiry(cls, expiry):
        """Enforce the token has not expired."""
        if datetime.now(timezone.utc) > expiry:
            raise ValueError(f"token expired on {expiry.isoformat()}")
        return expiry

    @root_validator
    def validate_all(cls, values):
        """If only invalid field is 'expiry',  raise a different exception."""
        # values dict contains all fields that have been validated.
        if "expiry" in values:
            return values
        if all(k in values for k in ["url", "user"]):
            raise cls.Expired()
        return values

    def sign(self, key, salt=None):
        signer = create_signer(key, salt)
        # serialize to json with pydantic, which handles datetimes by default
        return signer.sign(self.json()).decode("utf8")

    @classmethod
    def verify(cls, token_string, key, salt=None):
        signer = create_signer(key, salt)
        try:
            payload = signer.unsign(token_string)
        except itsdangerous.BadSignature:
            raise ValidationError(["bad signature"], cls)

        # Use pydantics json parsing. The individual fields will be validated
        # as normal
        return cls.parse_raw(payload)
