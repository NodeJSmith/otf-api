import typing
from typing import Any

import jwt
import pendulum
from loguru import logger
from pycognito import AWSSRP, Cognito, MFAChallengeException
from pycognito.exceptions import TokenVerificationException
from pydantic import Field
from pydantic.config import ConfigDict

from otf_api.models.base import OtfItemBase

if typing.TYPE_CHECKING:
    from boto3.session import Session
    from botocore.config import Config

CLIENT_ID = "65knvqta6p37efc2l3eh26pl5o"  # from otlive
USER_POOL_ID = "us-east-1_dYDxUeyL1"


class OtfCognito(Cognito):
    _device_key: str | None = None

    def __init__(
        self,
        user_pool_id: str,
        client_id: str,
        user_pool_region: str | None = None,
        username: str | None = None,
        id_token: str | None = None,
        refresh_token: str | None = None,
        access_token: str | None = None,
        client_secret: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        session: "Session|None" = None,
        botocore_config: "Config|None" = None,
        boto3_client_kwargs: dict[str, Any] | None = None,
        device_key: str | None = None,
    ):
        super().__init__(
            user_pool_id,
            client_id,
            user_pool_region=user_pool_region,
            username=username,
            id_token=id_token,
            refresh_token=refresh_token,
            access_token=access_token,
            client_secret=client_secret,
            access_key=access_key,
            secret_key=secret_key,
            session=session,
            botocore_config=botocore_config,
            boto3_client_kwargs=boto3_client_kwargs,
        )
        self.device_key = device_key

    @property
    def device_key(self) -> str | None:
        return self._device_key

    @device_key.setter
    def device_key(self, value: str | None):
        if not value:
            if self._device_key:
                logger.info("Clearing device key")
            self._device_key = value
            return

        redacted_value = value[:4] + "*" * (len(value) - 8) + value[-4:]
        logger.info(f"Setting device key: {redacted_value}")
        self._device_key = value

    def _set_tokens(self, tokens: dict[str, Any]):
        """Set the tokens and device metadata from the response.

        Args:
            tokens (dict): The response from the Cognito service.
        """
        super()._set_tokens(tokens)

        if new_metadata := tokens["AuthenticationResult"].get("NewDeviceMetadata"):
            self.device_key = new_metadata["DeviceKey"]

    def authenticate(self, password: str, client_metadata: dict[str, Any] | None = None, device_key: str | None = None):
        """
        Authenticate the user using the SRP protocol. Overridden to add `confirm_device` call.

        Args:
            password (str): The user's password
            client_metadata (dict, optional): Any additional client metadata to send to Cognito
        """
        aws = AWSSRP(
            username=self.username,
            password=password,
            pool_id=self.user_pool_id,
            client_id=self.client_id,
            client=self.client,
            client_secret=self.client_secret,
        )
        try:
            tokens = aws.authenticate_user(client_metadata=client_metadata)
        except MFAChallengeException as mfa_challenge:
            self.mfa_tokens = mfa_challenge.get_tokens()
            raise mfa_challenge

        # Set the tokens and device metadata
        self._set_tokens(tokens)

        if not device_key:
            # Confirm the device so we can use the refresh token
            aws.confirm_device(tokens)
        else:
            self.device_key = device_key
            try:
                self.renew_access_token()
            except TokenVerificationException:
                logger.error("Failed to renew access token. Confirming device.")
                self.device_key = None
                aws.confirm_device(tokens)

    def check_token(self, renew: bool = True) -> bool:
        """
        Checks the exp attribute of the access_token and either refreshes
        the tokens by calling the renew_access_tokens method or does nothing
        :param renew: bool indicating whether to refresh on expiration
        :return: bool indicating whether access_token has expired
        """
        if not self.access_token:
            raise AttributeError("Access Token Required to Check Token")
        now = pendulum.now()
        dec_access_token = jwt.decode(self.access_token, options={"verify_signature": False})

        exp = pendulum.DateTime.fromtimestamp(dec_access_token["exp"])
        if now > exp.subtract(minutes=15):
            expired = True
            if renew:
                self.renew_access_token()
        else:
            expired = False
        return expired

    def renew_access_token(self):
        """Sets a new access token on the User using the cached refresh token and device metadata."""
        auth_params = {"REFRESH_TOKEN": self.refresh_token}
        self._add_secret_hash(auth_params, "SECRET_HASH")

        if self.device_key:
            logger.info("Using device key for refresh token")
            auth_params["DEVICE_KEY"] = self.device_key

        refresh_response = self.client.initiate_auth(
            ClientId=self.client_id, AuthFlow="REFRESH_TOKEN_AUTH", AuthParameters=auth_params
        )
        self._set_tokens(refresh_response)

    @classmethod
    def from_token(
        cls, access_token: str, id_token: str, refresh_token: str | None = None, device_key: str | None = None
    ) -> "OtfCognito":
        """Create an OtfCognito instance from an id token.

        Args:
            access_token (str): The access token.
            id_token (str): The id token.
            refresh_token (str, optional): The refresh token. Defaults to None.
            device_key (str, optional): The device key. Defaults

        Returns:
            OtfCognito: The user instance
        """
        cognito = OtfCognito(
            USER_POOL_ID,
            CLIENT_ID,
            access_token=access_token,
            id_token=id_token,
            refresh_token=refresh_token,
            device_key=device_key,
        )
        cognito.verify_tokens()
        cognito.check_token()
        return cognito

    @classmethod
    def login(cls, username: str, password: str) -> "OtfCognito":
        """Create an OtfCognito instance from a username and password.

        Args:
            username (str): The username to login with.
            password (str): The password to login with.

        Returns:
            OtfCognito: The logged in user.
        """
        cognito_user = OtfCognito(USER_POOL_ID, CLIENT_ID, username=username)
        cognito_user.authenticate(password)
        cognito_user.check_token()
        return cognito_user


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
    model_config = ConfigDict(arbitrary_types_allowed=True)
    cognito: OtfCognito

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        id_token: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        device_key: str | None = None,
        cognito: OtfCognito | None = None,
    ):
        """Create a User instance.

        Args:
            username (str, optional): The username to login with. Defaults to None.
            password (str, optional): The password to login with. Defaults to None.
            id_token (str, optional): The id token. Defaults to None.
            access_token (str, optional): The access token. Defaults to None.
            refresh_token (str, optional): The refresh token. Defaults to None.
            device_key (str, optional): The device key. Defaults to None.
            cognito (OtfCognito, optional): A Cognito instance. Defaults to None.

        Raises:
            ValueError: Must provide either username and password or id token


        """
        if cognito:
            cognito = cognito
        elif username and password:
            cognito = OtfCognito.login(username, password)
        elif access_token and id_token:
            cognito = OtfCognito.from_token(access_token, id_token, refresh_token, device_key)
        else:
            raise ValueError("Must provide either username and password or id token.")

        super().__init__(cognito=cognito)

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

    @property
    def device_key(self) -> str:
        return self.cognito.device_key
