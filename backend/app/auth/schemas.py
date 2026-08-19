"""Auth request/response schemas."""

from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def _validate_email(value: str) -> str:
    # Same checks as pydantic's EmailStr, but test_environment=True allows the
    # .test TLD — RFC 2606's reserved TLD for exactly this: local/seeded accounts.
    try:
        return validate_email(value, test_environment=True).normalized
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc


Email = Annotated[str, AfterValidator(_validate_email)]


class RegisterIn(BaseModel):
    email: Email
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: Email
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_admin: bool
