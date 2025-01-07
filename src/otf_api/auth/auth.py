import socket
import typing
from logging import getLogger
from typing import ClassVar, Literal

import attrs
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pycognito import AWSSRP, Cognito

from otf_api.auth.config import OtfAuthConfig
from otf_api.auth.utils import CognitoTokens

if typing.TYPE_CHECKING:
    from mypy_boto3_cognito_idp.type_defs import AuthenticationResultTypeTypeDef

LOGGER = getLogger(__name__)
CLIENT_ID = "1457d19r0pcjgmp5agooi0rb1b"  # from android app
USER_POOL_ID = "us-east-1_dYDxUeyL1"


class OtfAuth:
    auth_type: ClassVar[Literal["basic", "token", "cognito"]]

    cognito: Cognito
    config: OtfAuthConfig

    def __attrs_post_init__(self) -> None:
        if not hasattr(self, "config"):
            self.config = OtfAuthConfig()

    @staticmethod
    def has_cached_credentials(config: OtfAuthConfig | None = None) -> bool:
        """Check if there are cached credentials.

        Args:
            config (OtfAuthConfig, optional): The configuration. Defaults to None.

        Returns:
            bool: True if there are cached credentials, False otherwise.
        """
        config = config or OtfAuthConfig()
        return bool(config.token_cache.get_cached_data())

    @staticmethod
    def from_cache(config: OtfAuthConfig | None = None) -> "OtfTokenAuth":
        """Attempt to get an authentication object from the cache. If no tokens are found, raise a ValueError.

        If config is not provided the default configuration will be used, with plaintext token caching enabled.

        Args:
            config (OtfAuthConfig, optional): The configuration. Defaults to None.

        Raises:
            ValueError: If no tokens are found in the cache.
        """

        config = config or OtfAuthConfig(cache_tokens_plaintext=True)
        tokens = config.token_cache.get_cached_data()
        if not tokens:
            raise ValueError("No tokens found in cache")

        return OtfTokenAuth(
            access_token=tokens["access_token"],
            id_token=tokens["id_token"],
            refresh_token=tokens.get("refresh_token"),
            auth_config=config,
        )

    @staticmethod
    def create(
        username: str | None = None,
        password: str | None = None,
        id_token: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        cognito: Cognito | None = None,
        config: OtfAuthConfig | None = None,
    ) -> "OTF_AUTH_TYPE":
        """Create an authentication object.

        Accepts either username/password, id/access tokens, or a Cognito object.

        Raises a ValueError if none of the required parameters are provided.
        """
        config = config or OtfAuthConfig()

        if username and password:
            return OtfBasicAuth(username=username, password=password, config=config)
        if id_token and access_token:
            return OtfTokenAuth(
                id_token=id_token, access_token=access_token, refresh_token=refresh_token, auth_config=config
            )
        if cognito:
            return OtfCognitoAuth(cognito=cognito, auth_config=config)

        raise ValueError("Must provide username/password or id/access tokens or cognito object")

    def clear_cache(self) -> None:
        """Clear the cached device data and tokens."""
        self.clear_cached_device_data()
        self.clear_cached_tokens()

    def clear_cached_tokens(self) -> None:
        """Clear the cached tokens."""
        self.config.token_cache.clear_cache()

    def clear_cached_device_data(self) -> None:
        """Clear the cached device data."""
        self.config.dd_cache.clear_cache()

    def authenticate(self) -> None:
        raise NotImplementedError

    def setup_cognito(self, tokens: CognitoTokens) -> None:
        self.cognito = Cognito(
            USER_POOL_ID,
            CLIENT_ID,
            access_token=tokens.access_token,
            id_token=tokens.id_token,
            refresh_token=tokens.refresh_token,
            botocore_config=Config(signature_version=UNSIGNED),
        )

        self.validate_cognito_tokens()

    def validate_cognito_tokens(self) -> None:
        """Validate the Cognito tokens. Will refresh the tokens if necessary."""
        self.cognito.check_token()
        self.cognito.verify_tokens()

        if self.config.cache_tokens_plaintext:
            tokens = {
                "access_token": self.cognito.access_token,
                "id_token": self.cognito.id_token,
                "refresh_token": self.cognito.refresh_token,
            }
            self.config.token_cache.write_to_cache(tokens)


@attrs.define
class OtfBasicAuth(OtfAuth):
    auth_type: ClassVar[Literal["basic", "token", "cognito"]] = "basic"

    username: str
    password: str
    config: OtfAuthConfig = attrs.field(factory=OtfAuthConfig)

    def get_awssrp(self) -> AWSSRP:
        # this is to avoid boto3 trying to find credentials in the environment/local machine
        # when those credentials are not desired and may slow down the sign in process (sometimes by a lot)
        # https://github.com/boto/botocore/issues/1395#issuecomment-902244525

        kwargs = {
            "pool_id": USER_POOL_ID,
            "client_id": CLIENT_ID,
            "client": boto3.client("cognito-idp", config=Config(signature_version=UNSIGNED)),
        }

        dd = self.config.dd_cache.get_cached_data() if self.config.cache_device_data else {}

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
        if not self.config.cache_device_data or self.config.dd_cache.get_cached_data():
            LOGGER.debug("Skipping device setup")

        try:
            hostname = socket.gethostname()
            device_name = f"{hostname}-otf-api"
        except Exception:
            LOGGER.exception("Failed to get device name")
            return

        try:
            if not tokens.device_key:
                LOGGER.debug("No new device metadata")
                return

        except KeyError:
            LOGGER.error("Failed to get device key and group key")
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
            self.config.dd_cache.write_to_cache(dd)
        except Exception:
            LOGGER.exception("Failed to write device key cache")
            return

    def forget_device(self) -> None:
        """Forget the device from AWS and delete the device key cache."""

        access_token = self.cognito.access_token
        dd = self.config.dd_cache.get_cached_data()
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

    access_token: str
    id_token: str
    refresh_token: str | None = None
    auth_config: OtfAuthConfig = attrs.field(factory=OtfAuthConfig)

    def authenticate(self) -> None:
        dd = self.auth_config.dd_cache.get_cached_data() if self.auth_config.cache_device_data else {}
        dd.pop("device_password", None)  # remove device password, not attribute of CognitoTokens
        tokens = CognitoTokens(
            access_token=self.access_token, id_token=self.id_token, refresh_token=self.refresh_token, **dd
        )
        self.setup_cognito(tokens)


@attrs.define
class OtfCognitoAuth(OtfAuth):
    auth_type: ClassVar[Literal["basic", "token", "cognito"]] = "cognito"

    cognito: Cognito
    auth_config: OtfAuthConfig = attrs.field(factory=OtfAuthConfig)

    def authenticate(self) -> None:
        self.cognito.check_token(renew=True)
        self.cognito.verify_tokens()


OTF_AUTH_TYPE = OtfBasicAuth | OtfTokenAuth | OtfCognitoAuth
