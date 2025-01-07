from logging import getLogger

import attrs

from otf_api.auth.auth import OTF_AUTH_TYPE, OtfAuth, OtfAuthConfig, OtfBasicAuth, OtfCognito
from otf_api.auth.utils import HttpxCognitoAuth

LOGGER = getLogger(__name__)


@attrs.define(init=False)
class OtfUser:
    member_id: str
    member_uuid: str
    email_address: str
    httpx_auth: HttpxCognitoAuth
    otf_auth: OTF_AUTH_TYPE

    def __init__(self, auth: OTF_AUTH_TYPE):
        """Create a User instance.

        Args:
            auth (OtfAuth): The authentication method.
            config (OtfAuthConfig, optional): The configuration. Defaults to None.

        Raises:
            ValueError: If neither username/password nor id/access tokens are provided.
        """

        self.otf_auth = auth
        self.otf_auth.authenticate()

        self.member_id = self.cognito.id_claims["cognito:username"]
        self.member_uuid = self.cognito.access_claims["sub"]
        self.email_address = self.cognito.id_claims["email"]

        self.httpx_auth = HttpxCognitoAuth(cognito=self.cognito)

    @property
    def cognito(self) -> OtfCognito:
        """Get the Cognito instance."""
        return self.otf_auth.cognito

    def validate_cognito_tokens(self) -> None:
        """Validate the tokens."""
        self.otf_auth.validate_cognito_tokens()

    def forget_device(self) -> None:
        """Forget the device."""
        if isinstance(self.otf_auth, OtfBasicAuth):
            self.otf_auth.forget_device()
        else:
            LOGGER.warning("Cannot forget device with non-basic auth")
            return

    def clear_cache(self) -> None:
        """Clear the cache."""
        self.otf_auth.clear_cache()

    def clear_cached_tokens(self) -> None:
        """Clear the cached tokens."""
        self.otf_auth.clear_cached_tokens()

    def clear_cached_device_data(self) -> None:
        """Clear the cached device data."""
        self.otf_auth.clear_cached_device_data()

    @classmethod
    def login(cls, username: str, password: str, config: OtfAuthConfig | None = None) -> "OtfUser":
        """Create a User instance from a username and password.

        Args:
            username (str): The username.
            password (str): The password.
            config (OtfAuthConfig, optional): The configuration. Defaults to None.

        Returns:
            OtfUser: The User instance
        """
        auth = OtfAuth.create(username=username, password=password, config=config)
        return cls(auth)

    @classmethod
    def from_tokens(
        cls, access_token: str, id_token: str, refresh_token: str | None = None, config: OtfAuthConfig | None = None
    ) -> "OtfUser":
        """Create a User instance from tokens.

        Args:
            access_token (str): The access token.
            id_token (str): The id token.
            refresh_token (str, optional): The refresh token. Defaults to None.
            config (OtfAuthConfig, optional): The configuration. Defaults to None.

        Returns:
            OtfUser: The User instance
        """

        auth = OtfAuth.create(access_token=access_token, id_token=id_token, refresh_token=refresh_token, config=config)
        return cls(auth)

    @classmethod
    def from_cognito(cls, cognito: OtfCognito, config: OtfAuthConfig | None = None) -> "OtfUser":
        """Create a User instance from a OtfCognito instance.

        Args:
            cognito (OtfCognito): The OtfCognito instance.
            config (OtfAuthConfig, optional): The configuration. Defaults to None.

        Returns:
            OtfUser: The User instance
        """
        auth = OtfAuth.create(cognito=cognito, config=config)
        return cls(auth)

    @classmethod
    def from_cache(cls, config: OtfAuthConfig | None = None) -> "OtfUser":
        """Create a User instance from cached tokens.

        Args:
            config (OtfAuthConfig, optional): The configuration. Defaults to None.

        Returns:
            OtfUser: The User instance
        """
        auth = OtfAuth.from_cache(config)
        return cls(auth)

    @classmethod
    def has_cached_credentials(cls, config: OtfAuthConfig | None = None) -> bool:
        """Check if there are cached credentials.

        Args:
            config (OtfAuthConfig, optional): The configuration. Defaults to None.

        Returns:
            bool: True if there are cached credentials, False otherwise.
        """
        return OtfAuth.has_cached_credentials(config)
