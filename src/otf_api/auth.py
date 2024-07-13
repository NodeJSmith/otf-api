import asyncio
import inspect
from collections.abc import Callable

from loguru import logger
from pycognito import Cognito
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


class OtfUser(OtfItemBase):
    cognito: Cognito

    def __init__(self, cognito: Cognito, refresh_callback: Callable[["OtfUser"], None] | None = None):
        """Create a new User instance.

        Args:
            cognito (Cognito): The Cognito instance to use.
            refresh_callback (Callable[[OtfUser], None], optional): The callback to call when the tokens are refreshed.
        """
        self.cognito = cognito

        if refresh_callback:
            if not asyncio.iscoroutinefunction(refresh_callback) and not callable(refresh_callback):
                raise ValueError("refresh_callback must be a callable function.")
            sig = inspect.signature(refresh_callback)
            if len(sig.parameters) != 1:
                raise ValueError("refresh_callback must accept one argument.")

        self.refresh_callback = refresh_callback

        self._refresh_task = asyncio.create_task(self.start_background_refresh())

    @classmethod
    def login(
        cls, username: str, password: str, refresh_callback: Callable[["OtfUser"], None] | None = None
    ) -> "OtfUser":
        """Login and return a User instance.

        Args:
            username (str): The username to login with.
            password (str): The password to login with.
            refresh_callback (Callable[[OtfUser], None], optional): The callback to call when the tokens are refreshed.

        Returns:
            OtfUser: The logged in user.
        """
        cognito_user = Cognito(USER_POOL_ID, CLIENT_ID, username=username)
        cognito_user.authenticate(password)
        cognito_user.check_token()
        user = cls(cognito=cognito_user, refresh_callback=refresh_callback)
        return user

    @classmethod
    def from_token(
        cls, access_token: str, id_token: str, refresh_callback: Callable[["OtfUser"], None] | None = None
    ) -> "OtfUser":
        """Create a User instance from an id token.

        Args:
            access_token (str): The access token.
            id_token (str): The id token.
            refresh_callback (Callable[[OtfUser], None], optional): The callback to call when the tokens are refreshed.
            Callable should accept the user instance as an argument. Defaults to None.

        Returns:
            OtfUser: The user instance
        """
        cognito_user = Cognito(USER_POOL_ID, CLIENT_ID, access_token=access_token, id_token=id_token)
        cognito_user.verify_tokens()
        cognito_user.check_token()

        return cls(cognito=cognito_user, refresh_callback=refresh_callback)

    def refresh_token(self) -> bool:
        """Refresh the user's access token.

        Returns:
            bool: True if the token was refreshed, False otherwise.
        """
        logger.info("Checking tokens...")
        refreshed = self.cognito.check_token()
        if refreshed:
            logger.info("Refreshed tokens")
        return refreshed

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

    async def start_background_refresh(self) -> None:
        """Start the background task for refreshing the token."""
        logger.debug("Starting background task for refreshing token.")
        """Run the refresh token method on a loop to keep the token fresh."""
        try:
            while True:
                await asyncio.sleep(300)
                refreshed = self.refresh_token()
                if refreshed and self.refresh_callback:
                    if asyncio.iscoroutinefunction(self.refresh_callback):
                        await self.refresh_callback(self)
                    elif self.refresh_callback:
                        self.refresh_callback(self)
        except asyncio.CancelledError:
            pass
