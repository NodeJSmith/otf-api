from logging import getLogger

import attrs
from botocore.exceptions import ClientError

from otf_api.auth.auth import HttpxCognitoAuth, OtfCognito
from otf_api.auth.utils import get_username_password
from otf_api.exceptions import NoCredentialsError, OtfAuthenticationError

LOGGER = getLogger(__name__)


def _log_initial_auth_error(e: ClientError, username: str | None) -> None:
    code = e.response.get("Error", {}).get("Code", "")
    if code == "NotAuthorizedException":
        LOGGER.warning("Authentication failed — incorrect password for %s", username)
    elif code == "UserNotFoundException":
        LOGGER.warning("Authentication failed — no account found for %s", username)
    else:
        LOGGER.exception("Failed to authenticate with Cognito")


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
            LOGGER.debug("No credentials provided, attempting to get them from environment or prompt user")
            username, password = get_username_password()
            try:
                self.cognito = OtfCognito(username=username, password=password)
            except ClientError as e:
                _log_initial_auth_error(e, username)
                raise OtfAuthenticationError(str(e)) from e
            except Exception:
                LOGGER.exception("Failed to authenticate with Cognito")
                raise
        except ClientError as e:
            _log_initial_auth_error(e, username)
            raise OtfAuthenticationError(str(e)) from e
        except Exception:
            LOGGER.exception("Failed to authenticate with Cognito")
            raise

        self.cognito_id = self.cognito.access_claims["sub"]
        self.member_uuid = self.cognito.id_claims["cognito:username"]
        self.email_address = self.cognito.id_claims["email"]

        self.httpx_auth = HttpxCognitoAuth(cognito=self.cognito)
