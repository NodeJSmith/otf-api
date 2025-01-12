import platform
import typing
from logging import getLogger
from pathlib import Path
from typing import Any, ClassVar

import requests
from boto3 import Session
from botocore import UNSIGNED
from botocore.config import Config
from pycognito import AWSSRP, Cognito
from pycognito.aws_srp import generate_hash_device

from otf_api.utils import CacheableData

if typing.TYPE_CHECKING:
    from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
    from mypy_boto3_cognito_idp.type_defs import InitiateAuthResponseTypeDef

LOGGER = getLogger(__name__)
CLIENT_ID = "1457d19r0pcjgmp5agooi0rb1b"  # from android app
USER_POOL_ID = "us-east-1_dYDxUeyL1"
REGION = "us-east-1"

BOTO_CONFIG = Config(region_name=REGION, signature_version=UNSIGNED)
CRED_CACHE = CacheableData("creds", Path("~/.otf-api"))

DEVICE_KEYS_NO_PWD = ["device_key", "device_group_key"]
DEVICE_KEYS = [*DEVICE_KEYS_NO_PWD, "device_password"]
TOKEN_KEYS = ["access_token", "id_token", "refresh_token"]


class NoCredentialsError(Exception):
    """Raised when no credentials are found."""


class OtfCognito(Cognito):
    """A subclass of the pycognito Cognito class that adds the device_key to the auth_params. Without this
    being set the renew_access_token call will always fail with NOT_AUTHORIZED."""

    user_pool_id: ClassVar[str] = USER_POOL_ID
    client_id: ClassVar[str] = CLIENT_ID
    user_pool_region: ClassVar[str] = REGION

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        id_token: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ):
        """

        Args:
            username (str, optional): User Pool username
            password (str, optional): User Pool password
            id_token (str, optional): ID Token returned by authentication
            access_token (str, optional): Access Token returned by authentication
            refresh_token (str, optional): Refresh Token returned by authentication
        """

        self.username = username
        self.id_token = id_token
        self.access_token = access_token
        self.refresh_token = refresh_token

        self.client_secret: str | None = None
        self.token_type: str | None = None
        self.id_claims: dict[str, Any] = None  # type: ignore
        self.access_claims: dict[str, Any] = None  # type: ignore
        self.custom_attributes: dict[str, Any] | None = None
        self.base_attributes: dict[str, Any] | None = None
        self.pool_jwk: dict[str, Any] | None = None
        self.mfa_tokens: dict[str, Any] | None = None
        self.pool_domain_url: str | None = None

        dd = CRED_CACHE.get_cached_data(DEVICE_KEYS)

        self.device_name: str = platform.node()
        self.device_key: str | None = dd.get("device_key")
        self.device_group_key: str | None = dd.get("device_group_key")
        self.device_password: str | None = dd.get("device_password")

        self.client: CognitoIdentityProviderClient = Session().client(
            "cognito-idp", config=BOTO_CONFIG, region_name=REGION
        )

        token_cache = CRED_CACHE.get_cached_data(TOKEN_KEYS)

        if not (username and password) and not (id_token and access_token) and not token_cache:
            raise NoCredentialsError("Must provide username/password or id/access tokens, or have cached tokens")

        if username and password:
            self.login(password)
        elif token_cache and not (id_token and access_token):
            LOGGER.debug("Using cached tokens")
            self.id_token = token_cache["id_token"]
            self.access_token = token_cache["access_token"]
            self.refresh_token = token_cache["refresh_token"]

        self.validate_cognito_tokens()

    def validate_cognito_tokens(self) -> None:
        """Validate the Cognito tokens. Will refresh the tokens if necessary."""
        self.check_token()
        self.verify_tokens()

        CRED_CACHE.write_to_cache(self.tokens)

    @property
    def cognito_idp_url(self) -> str:
        return f"https://cognito-idp.{self.user_pool_region}.amazonaws.com/"

    @property
    def tokens(self) -> dict[str, str]:
        tokens = {
            "access_token": self.access_token,
            "id_token": self.id_token,
            "refresh_token": self.refresh_token,
        }
        return {k: v for k, v in tokens.items() if v}

    def login(self, password: str) -> None:
        """Called when logging in with a username and password. Will set the tokens and device metadata."""

        LOGGER.debug("Logging in with username and password...")

        aws = AWSSRP(
            username=self.username,
            password=password,
            pool_id=USER_POOL_ID,
            client_id=CLIENT_ID,
            client=self.client,
        )
        tokens: InitiateAuthResponseTypeDef = aws.authenticate_user()
        self._set_tokens(tokens)
        self.handle_device_setup()

    def handle_device_setup(self) -> None:
        """Handles device setup, including confirming the device and updating the device status."""
        if not self.device_key:
            LOGGER.debug("Skipping device setup")
            return

        try:
            _ = self._send_confirm_device()
            _ = self._send_update_device_status()
        except Exception:
            LOGGER.exception("Failed to confirm device")
            return

        try:
            dd = {
                "device_key": self.device_key,
                "device_group_key": self.device_group_key,
                "device_password": self.device_password,
            }
            CRED_CACHE.write_to_cache(dd)
        except Exception:
            LOGGER.exception("Failed to write device key cache")

    def forget_device(self) -> None:
        """Forgets the device by sending a request to the Cognito service and clearing the device metadata cache."""
        try:
            self._send_forget_device()
            CRED_CACHE.clear_cache(DEVICE_KEYS)
        except Exception:
            LOGGER.exception("Failed to forget device")

    ##### OVERRIDEN METHODS #####

    def renew_access_token(self) -> None:
        """Sets a new access token on the User using the cached refresh token and device metadata.

        Overriden to add the device key to the auth_params if it is set. Without this all calls to renew_access_token
        will fail with NOT_AUTHORIZED.

        """
        auth_params = {"REFRESH_TOKEN": self.refresh_token}
        self._add_secret_hash(auth_params, "SECRET_HASH")

        if self.device_key:
            auth_params["DEVICE_KEY"] = self.device_key

        refresh_response = self.client.initiate_auth(
            ClientId=self.client_id, AuthFlow="REFRESH_TOKEN_AUTH", AuthParameters=auth_params
        )
        self._set_tokens(refresh_response)

    def _set_tokens(self, tokens: "InitiateAuthResponseTypeDef") -> None:
        """Helper function to verify and set token attributes based on a Cognito AuthenticationResult.

        Overriden to cache the tokens and set/cache the device metadata.
        """
        auth_result = tokens["AuthenticationResult"]
        device_metadata = auth_result.get("NewDeviceMetadata", {})

        # tokens
        self.verify_token(auth_result["AccessToken"], "access_token", "access")
        self.verify_token(auth_result["IdToken"], "id_token", "id")
        self.refresh_token = auth_result.get("RefreshToken", self.refresh_token)
        self.token_type = auth_result["TokenType"]
        CRED_CACHE.write_to_cache(self.tokens)

        # device metadata
        self.device_key = device_metadata.get("DeviceKey", self.device_key)
        self.device_group_key = device_metadata.get("DeviceGroupKey", self.device_group_key)
        if self.device_key and self.device_group_key:
            CRED_CACHE.write_to_cache({"device_key": self.device_key, "device_group_key": self.device_group_key})

    ##### REPLACED METHODS #####

    def _send_forget_device(self) -> Any:
        """Sends a request to the Cognito service to forget the device.

        Replaces `forget_device` on the AWSSRP class, which requires a username and password to instantiate, even though
        this call does not require them.

        """

        headers = self._get_headers("ForgetDevice")
        data = {"AccessToken": self.access_token, "DeviceKey": self.device_key}
        response = requests.post(self.cognito_idp_url, headers=headers, json=data, timeout=30)
        return response.json()

    def _send_confirm_device(self) -> Any:
        """Sends a request to the Cognito service to confirm the device.

        Replaces `confirm_device` on the AWSSRP class.

        """

        self.device_password, device_secret_verifier_config = generate_hash_device(
            self.device_group_key, self.device_key
        )

        headers = self._get_headers("ConfirmDevice")
        data = {
            "AccessToken": self.access_token,
            "DeviceKey": self.device_key,
            "DeviceName": self.device_name,
            "DeviceSecretVerifierConfig": device_secret_verifier_config,
        }
        response = requests.post(self.cognito_idp_url, headers=headers, json=data, timeout=30)
        return response.json()

    def _send_update_device_status(self) -> Any:
        """Sends a request to the Cognito service to update the device status.

        Replaces `update_device_status` on the AWSSRP class.
        """

        headers = self._get_headers("UpdateDeviceStatus")
        data = {"AccessToken": self.access_token, "DeviceKey": self.device_key, "DeviceRememberedStatus": "remembered"}
        response = requests.post(self.cognito_idp_url, headers=headers, json=data, timeout=30)
        return response.json()

    def _get_headers(self, target: str) -> dict[str, str]:
        """Get the headers for a Cognito API request."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": f"AWSCognitoIdentityProviderService.{target}",
        }
