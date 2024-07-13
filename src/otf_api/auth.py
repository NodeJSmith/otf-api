import json
from pathlib import Path
from typing import ClassVar

from loguru import logger
from pycognito import Cognito, TokenVerificationException
from pydantic import Field

from otf_api.models.base import OtfItemBase

CLIENT_ID = "65knvqta6p37efc2l3eh26pl5o"  # from otlive
USER_POOL_ID = "us-east-1_dYDxUeyL1"


class IdClaimsData(OtfItemBase):
    sub: str
    email_verified: bool
    iss: str
    cognito_username: str = Field(alias="cognito:username")
    given_name: str
    locale: str
    home_studio_id: str = Field(alias="custom:home_studio_id")
    aud: str
    event_id: str
    token_use: str
    auth_time: int
    exp: int
    is_migration: str = Field(alias="custom:isMigration")
    iat: int
    family_name: str
    email: str
    koji_person_id: str = Field(alias="custom:koji_person_id")

    @property
    def member_uuid(self) -> str:
        return self.cognito_username

    @property
    def full_name(self) -> str:
        return f"{self.given_name} {self.family_name}"


class AccessClaimsData(OtfItemBase):
    sub: str
    device_key: str
    iss: str
    client_id: str
    event_id: str
    token_use: str
    scope: str
    auth_time: int
    exp: int
    iat: int
    jti: str
    username: str

    @property
    def member_uuid(self) -> str:
        return self.username


class OtfUser:
    token_path: ClassVar[Path] = Path("~/.otf/.tokens").expanduser()
    cognito: Cognito

    def __init__(self, cognito: Cognito):
        self.cognito = cognito

    @classmethod
    def cache_file_exists(cls) -> bool:
        return cls.token_path.exists()

    @classmethod
    def username_from_disk(cls) -> str:
        val: str = json.loads(cls.token_path.read_text())["username"]
        return val

    @classmethod
    def load_from_disk(cls, username: str, password: str) -> "OtfUser":
        """Load a User instance from disk. If the token is invalid, reauthenticate with the provided credentials.

        Args:
            username (str): The username to reauthenticate with.
            password (str): The password to reauthenticate with.

        Returns:
            User: The loaded user.

        """
        attr_dict = json.loads(cls.token_path.read_text())

        cognito_user = Cognito(USER_POOL_ID, CLIENT_ID, **attr_dict)
        try:
            cognito_user.verify_tokens()
            return cls(cognito=cognito_user)
        except TokenVerificationException:
            user = cls.login(username, password)
            return user

    @classmethod
    def login(cls, username: str, password: str) -> "OtfUser":
        """Login and return a User instance. After a successful login, the user is saved to disk.

        Args:
            username (str): The username to login with.
            password (str): The password to login with.

        Returns:
            User: The logged in user.
        """
        cognito_user = Cognito(USER_POOL_ID, CLIENT_ID, username=username)
        cognito_user.authenticate(password)
        cognito_user.check_token()
        user = cls(cognito=cognito_user)
        user.save_to_disk()
        return user

    @classmethod
    def from_token(cls, access_token: str, id_token: str) -> "OtfUser":
        """Create a User instance from an id token."""
        cognito_user = Cognito(USER_POOL_ID, CLIENT_ID, access_token=access_token, id_token=id_token)
        cognito_user.verify_tokens()
        cognito_user.check_token()

        return cls(cognito=cognito_user)

    def refresh_token(self) -> "OtfUser":
        """Refresh the user's access token."""
        logger.info("Checking tokens...")
        if self.cognito.check_token():
            logger.info("Refreshed tokens")
            self.save_to_disk()
        return self

    @property
    def member_id(self) -> str:
        return self.id_claims_data.cognito_username

    @property
    def member_uuid(self) -> str:
        return self.access_claims_data.sub

    @property
    def access_claims_data(self) -> AccessClaimsData:
        return AccessClaimsData(**self.cognito.access_claims)

    @property
    def id_claims_data(self) -> IdClaimsData:
        return IdClaimsData(**self.cognito.id_claims)

    def get_tokens(self) -> dict[str, str]:
        return {
            "id_token": self.cognito.id_token,
            "access_token": self.cognito.access_token,
            "refresh_token": self.cognito.refresh_token,
        }

    def save_to_disk(self) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "username": self.cognito.username,
            "id_token": self.cognito.id_token,
            "access_token": self.cognito.access_token,
            "refresh_token": self.cognito.refresh_token,
        }
        self.token_path.write_text(json.dumps(data))
