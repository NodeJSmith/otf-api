from logging import getLogger

import attrs

from otf_api.auth.auth import CRED_CACHE, NoCredentialsError, OtfCognito
from otf_api.auth.utils import HttpxCognitoAuth, can_provide_input, prompt_for_username_and_password

LOGGER = getLogger(__name__)


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
        """
        try:
            self.cognito = OtfCognito(
                username=username,
                password=password,
                id_token=id_token,
                access_token=access_token,
                refresh_token=refresh_token,
            )
        except NoCredentialsError:
            if not can_provide_input():
                LOGGER.error("Unable to prompt for credentials in a non-interactive shell")
                raise

            username, password = prompt_for_username_and_password()
            self.cognito = OtfCognito(username=username, password=password)

        self.cognito_id = self.cognito.access_claims["sub"]
        self.member_uuid = self.cognito.id_claims["cognito:username"]
        self.email_address = self.cognito.id_claims["email"]

        self.httpx_auth = HttpxCognitoAuth(cognito=self.cognito)

    @staticmethod
    def clear_cache():
        """Clear the cached credentials."""
        CRED_CACHE.clear_cache()
