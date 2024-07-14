from typing import Any

from pycognito import AWSSRP, Cognito, MFAChallengeException
from pydantic import Field
from pydantic.config import ConfigDict

from otf_api.models.base import OtfItemBase

CLIENT_ID = "65knvqta6p37efc2l3eh26pl5o"  # from otlive
USER_POOL_ID = "us-east-1_dYDxUeyL1"


class OtfCognito(Cognito):
    device_metadata: dict[str, Any]

    def _set_tokens(self, tokens: dict[str, Any]):
        """Set the tokens and device metadata from the response.

        Args:
            tokens (dict): The response from the Cognito service.
        """
        super()._set_tokens(tokens)

        if new_metadata := tokens["AuthenticationResult"].get("NewDeviceMetadata"):
            self.device_metadata = new_metadata
        elif not hasattr(self, "device_metadata"):
            self.device_metadata = {}

    def authenticate(self, password: str, client_metadata: dict[str, Any] | None = None):
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

        # Confirm the device so we can use the refresh token
        aws.confirm_device(tokens)

    def renew_access_token(self):
        """Sets a new access token on the User using the cached refresh token and device metadata."""
        auth_params = {"REFRESH_TOKEN": self.refresh_token}
        self._add_secret_hash(auth_params, "SECRET_HASH")

        if self.device_metadata:
            auth_params["DEVICE_KEY"] = self.device_metadata["DeviceKey"]

        refresh_response = self.client.initiate_auth(
            ClientId=self.client_id, AuthFlow="REFRESH_TOKEN_AUTH", AuthParameters=auth_params
        )
        self._set_tokens(refresh_response)


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

    @classmethod
    def login(cls, username: str, password: str) -> "OtfUser":
        """Login and return a User instance.

        Args:
            username (str): The username to login with.
            password (str): The password to login with.

        Returns:
            OtfUser: The logged in user.
        """
        cognito_user = OtfCognito(USER_POOL_ID, CLIENT_ID, username=username)
        cognito_user.authenticate(password)
        cognito_user.check_token()
        user = cls(cognito=cognito_user)
        return user

    @classmethod
    def from_token(cls, access_token: str, id_token: str) -> "OtfUser":
        """Create a User instance from an id token.

        Args:
            access_token (str): The access token.
            id_token (str): The id token.

        Returns:
            OtfUser: The user instance
        """
        cognito_user = OtfCognito(USER_POOL_ID, CLIENT_ID, access_token=access_token, id_token=id_token)
        cognito_user.verify_tokens()
        cognito_user.check_token()

        return cls(cognito=cognito_user)

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
