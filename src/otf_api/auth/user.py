from logging import getLogger

import attrs

from otf_api.auth.auth import HttpxCognitoAuth, OtfCognito
from otf_api.auth.utils import get_username_password
from otf_api.exceptions import NoCredentialsError, OtfError

LOGGER = getLogger(__name__)


def _create_cognito(username: str | None, password: str | None, **kwargs: str | None) -> OtfCognito:
    # OtfCognito maps and logs its own Cognito/botocore failures; only errors it leaves unmapped are logged here.
    try:
        return OtfCognito(username=username, password=password, **kwargs)
    except OtfError:
        raise
    except Exception:
        LOGGER.exception("Failed to authenticate with Cognito")
        raise


@attrs.define(init=False)
class OtfUser:
    """OtfUser is a thin wrapper around OtfCognito, meant to hide all of the gory details from end users."""

    cognito_id: str
    member_uuid: str
    email_address: str
    cognito: OtfCognito
    httpx_auth: HttpxCognitoAuth

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        id_token: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ):
        """Create a User instance.

        Args:
            username (str, optional): User Pool username
            password (str, optional): User Pool password
            id_token (str, optional): ID Token returned by authentication
            access_token (str, optional): Access Token returned by authentication
            refresh_token (str, optional): Refresh Token returned by authentication

        Raises:
            NoCredentialsError: If neither username/password nor id/access tokens are provided.
            OtfAuthenticationError: If Cognito rejects the login or token refresh.
            OtfTransportError: If a connectivity, timeout, or endpoint failure occurs.
            OtfConfigurationError: If a boto3/botocore configuration or validation failure occurs.
        """
        try:
            self.cognito = _create_cognito(
                username=username,
                password=password,
                id_token=id_token,
                access_token=access_token,
                refresh_token=refresh_token,
            )
        except NoCredentialsError:
            LOGGER.debug("No credentials provided, attempting to get them from environment or prompt user")
            username, password = get_username_password()
            self.cognito = _create_cognito(username=username, password=password)

        self.cognito_id = self.cognito.access_claims["sub"]
        self.member_uuid = self.cognito.id_claims["cognito:username"]
        self.email_address = self.cognito.id_claims["email"]

        self.httpx_auth = HttpxCognitoAuth(cognito=self.cognito)
