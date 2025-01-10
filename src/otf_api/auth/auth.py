import socket
import typing
from logging import getLogger
from pathlib import Path
from typing import ClassVar, Literal

import attrs
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pycognito import AWSSRP, Cognito

from otf_api.auth.utils import CognitoTokens
from otf_api.utils import CacheableData

if typing.TYPE_CHECKING:
    from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
    from mypy_boto3_cognito_idp.type_defs import AuthenticationResultTypeTypeDef

LOGGER = getLogger(__name__)
CLIENT_ID = "1457d19r0pcjgmp5agooi0rb1b"  # from android app
USER_POOL_ID = "us-east-1_dYDxUeyL1"
REGION = "us-east-1"

BOTO_CONFIG = Config(region_name=REGION, signature_version=UNSIGNED)
CRED_CACHE = CacheableData("creds", Path("~/.otf-api"))

DEVICE_KEYS_NO_PWD = ["device_key", "device_group_key"]
DEVICE_KEYS = [*DEVICE_KEYS_NO_PWD, "device_password"]
TOKEN_KEYS = ["access_token", "id_token", "refresh_token"]


class OtfCognito(Cognito):
    """A subclass of the pycognito Cognito class that adds the device_key to the auth_params. Without this
    being set the renew_access_token call will always fail with NOT_AUTHORIZED."""

    auth: "OTF_AUTH_TYPE"
    client: "CognitoIdentityProviderClient"

    def renew_access_token(self) -> None:
        """Sets a new access token on the User using the cached refresh token and device metadata."""
        auth_params = {"REFRESH_TOKEN": self.refresh_token}
        self._add_secret_hash(auth_params, "SECRET_HASH")

        if dd := CRED_CACHE.get_cached_data():
            auth_params["DEVICE_KEY"] = dd["device_key"]

        refresh_response = self.client.initiate_auth(
            ClientId=self.client_id, AuthFlow="REFRESH_TOKEN_AUTH", AuthParameters=auth_params
        )
        self._set_tokens(refresh_response)

        CRED_CACHE.write_to_cache(self.tokens)

    @property
    def tokens(self) -> dict[str, str]:
        tokens = {
            "access_token": self.access_token,
            "id_token": self.id_token,
            "refresh_token": self.refresh_token,
        }
        return {k: v for k, v in tokens.items() if v}


class OtfAuth:
    auth_type: ClassVar[Literal["basic", "token", "cognito"]]

    cognito: OtfCognito

    @property
    def access_token(self) -> str:
        if hasattr(self, "cognito") and self.cognito.access_token:
            return self.cognito.access_token
        raise AttributeError("No access token found")

    @property
    def id_token(self) -> str:
        if hasattr(self, "cognito") and self.cognito.id_token:
            return self.cognito.id_token
        raise AttributeError("No id token found")

    @property
    def refresh_token(self) -> str:
        if hasattr(self, "cognito") and self.cognito.refresh_token:
            return self.cognito.refresh_token
        raise AttributeError("No refresh token found")

    @staticmethod
    def has_cached_credentials() -> bool:
        """Check if there are cached credentials.

        Returns:
            bool: True if there are cached credentials, False otherwise.
        """

        return bool(CRED_CACHE.get_cached_data())

    @staticmethod
    def from_cache() -> "OtfTokenAuth":
        """Attempt to get an authentication object from the cache. If no tokens are found, raise a ValueError.

        If config is not provided the default configuration will be used, with plaintext token caching enabled.

        Raises:
            ValueError: If no tokens are found in the cache.
        """

        tokens = CRED_CACHE.get_cached_data()
        if not tokens:
            raise ValueError("No tokens found in cache")

        return OtfTokenAuth(
            access_token=tokens["access_token"], id_token=tokens["id_token"], refresh_token=tokens.get("refresh_token")
        )

    @staticmethod
    def create(
        username: str | None = None,
        password: str | None = None,
        id_token: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        cognito: OtfCognito | None = None,
    ) -> "OTF_AUTH_TYPE":
        """Create an authentication object.

        Accepts either username/password, id/access tokens, or a Cognito object.

        Raises a ValueError if none of the required parameters are provided.
        """

        if username and password:
            return OtfBasicAuth(username=username, password=password)
        if id_token and access_token:
            return OtfTokenAuth(id_token=id_token, access_token=access_token, refresh_token=refresh_token)
        if cognito:
            return OtfCognitoAuth(cognito=cognito)

        raise ValueError("Must provide username/password or id/access tokens or cognito object")

    def clear_cache(self) -> None:
        """Clear the cached device data and tokens."""
        self.clear_cached_device_data()
        self.clear_cached_tokens()

    def clear_cached_tokens(self) -> None:
        """Clear the cached tokens."""
        CRED_CACHE.clear_cache(TOKEN_KEYS)

    def clear_cached_device_data(self) -> None:
        """Clear the cached device data."""
        CRED_CACHE.clear_cache(DEVICE_KEYS)

    def authenticate(self) -> None:
        raise NotImplementedError

    def setup_cognito(self, tokens: CognitoTokens) -> None:
        self.cognito = OtfCognito(
            USER_POOL_ID,
            CLIENT_ID,
            access_token=tokens.access_token,
            id_token=tokens.id_token,
            refresh_token=tokens.refresh_token,
            botocore_config=BOTO_CONFIG,
        )

        self.validate_cognito_tokens()

    def validate_cognito_tokens(self) -> None:
        """Validate the Cognito tokens. Will refresh the tokens if necessary."""
        self.cognito.check_token()
        self.cognito.verify_tokens()

        CRED_CACHE.write_to_cache(self.cognito.tokens)

        # ensure the cognito instance has the auth object
        # we'll need this for the device key during refresh
        self.cognito.auth = self


@attrs.define
class OtfBasicAuth(OtfAuth):
    auth_type: ClassVar[Literal["basic", "token", "cognito"]] = "basic"

    username: str
    password: str

    def get_awssrp(self) -> AWSSRP:
        # this is to avoid boto3 trying to find credentials in the environment/local machine
        # when those credentials are not desired and may slow down the sign in process (sometimes by a lot)
        # https://github.com/boto/botocore/issues/1395#issuecomment-902244525

        kwargs = {
            "pool_id": USER_POOL_ID,
            "client_id": CLIENT_ID,
            "client": boto3.client("cognito-idp", config=BOTO_CONFIG),
        }

        dd = CRED_CACHE.get_cached_data(DEVICE_KEYS)

        kwargs = kwargs | dd | {"username": self.username, "password": self.password}

        aws = AWSSRP(**kwargs)
        return aws

    def authenticate(self) -> None:
        tokens = self.get_awssrp().authenticate_user()
        auth_result: AuthenticationResultTypeTypeDef = tokens["AuthenticationResult"]
        ndm = auth_result.get("NewDeviceMetadata", {})

        cognito_tokens = CognitoTokens(
            id_token=auth_result["IdToken"],
            access_token=auth_result["AccessToken"],
            refresh_token=auth_result.get("RefreshToken"),
            device_key=ndm.get("DeviceKey"),
            device_group_key=ndm.get("DeviceGroupKey"),
        )

        self.handle_device_setup(cognito_tokens)

        self.setup_cognito(cognito_tokens)

    def handle_device_setup(self, tokens: CognitoTokens) -> None:
        """Confirms the device with AWS and caches the device data for future use.

        Args:
            tokens (dict): The tokens from the AWS SRP instance.
        """
        if CRED_CACHE.get_cached_data():
            LOGGER.debug("Skipping device setup")

        try:
            hostname = socket.gethostname()
            device_name = f"{hostname}-otf-api"
        except Exception:
            LOGGER.exception("Failed to get device name")
            return

        if not tokens.device_key:
            LOGGER.debug("No new device metadata")
            return

        aws = self.get_awssrp()

        try:
            aws_tokens = {"AuthenticationResult": tokens.to_aws_format()}
            _, device_password = aws.confirm_device(tokens=aws_tokens, device_name=device_name)
            _ = aws.update_device_status(True, tokens.access_token, tokens.device_key)
        except Exception:
            LOGGER.exception("Failed to confirm device")
            return

        try:
            dd = {
                "device_key": tokens.device_key,
                "device_group_key": tokens.device_group_key,
                "device_password": device_password,
            }
            CRED_CACHE.write_to_cache(dd)
        except Exception:
            LOGGER.exception("Failed to write device key cache")
            return

    def forget_device(self) -> None:
        """Forget the device from AWS and delete the device key cache."""

        access_token = self.cognito.access_token
        dd = CRED_CACHE.get_cached_data()
        if not dd:
            LOGGER.debug("No device data to forget")
            return

        device_key = dd["device_key"]

        resp = self.get_awssrp().forget_device(access_token=access_token, device_key=device_key)
        LOGGER.debug(resp)

        self.clear_cached_device_data()


@attrs.define
class OtfTokenAuth(OtfAuth):
    auth_type: ClassVar[Literal["basic", "token", "cognito"]] = "token"

    _access_token: str
    _id_token: str
    _refresh_token: str | None = None

    def authenticate(self) -> None:
        dd = CRED_CACHE.get_cached_data(DEVICE_KEYS_NO_PWD)
        tokens = CognitoTokens(
            access_token=self._access_token, id_token=self._id_token, refresh_token=self._refresh_token, **dd
        )
        self.setup_cognito(tokens)

        self._access_token = None
        self._id_token = None
        self._refresh_token = None

    @property
    def access_token(self) -> str:
        if hasattr(self, "cognito") and self.cognito.access_token:
            return self.cognito.access_token
        return self._access_token

    @property
    def id_token(self) -> str:
        if hasattr(self, "cognito") and self.cognito.id_token:
            return self.cognito.id_token
        return self._id_token

    @property
    def refresh_token(self) -> str:
        if hasattr(self, "cognito") and self.cognito.refresh_token:
            return self.cognito.refresh_token
        return self._refresh_token


@attrs.define
class OtfCognitoAuth(OtfAuth):
    auth_type: ClassVar[Literal["basic", "token", "cognito"]] = "cognito"

    cognito: OtfCognito

    def authenticate(self) -> None:
        self.cognito.check_token(renew=True)
        self.cognito.verify_tokens()


OTF_AUTH_TYPE = OtfBasicAuth | OtfTokenAuth | OtfCognitoAuth
