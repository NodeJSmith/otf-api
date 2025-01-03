import json
import socket
from logging import getLogger
from pathlib import Path
from typing import Any, ClassVar

import attrs
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from pycognito import AWSSRP, Cognito

LOGGER = getLogger(__name__)

DEVICE_KEY_CACHE_PATH = Path("~/.otf-api/device_key_cache.json").expanduser()
DEVICE_KEY_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_cached_device_data() -> dict[str, str]:
    keys = ["device_key", "device_group_key", "device_password"]

    try:
        if not DEVICE_KEY_CACHE_PATH.exists():
            return {}

        if DEVICE_KEY_CACHE_PATH.stat().st_size == 0:
            return {}

        device_data: dict[str, str] = json.loads(DEVICE_KEY_CACHE_PATH.read_text())
        if set(device_data.keys()).issuperset(set(keys)):
            return {k: v for k, v in device_data.items() if k in keys}

        return {}
    except Exception:
        LOGGER.exception("Failed to read device key cache")
        return {}


@attrs.define(init=False)
class OtfUser:
    CLIENT_ID: ClassVar[str] = "1457d19r0pcjgmp5agooi0rb1b"  # from android app
    USER_POOL_ID: ClassVar[str] = "us-east-1_dYDxUeyL1"

    cognito: Cognito
    member_id: str
    member_uuid: str
    email_address: str
    aws: AWSSRP

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        id_token: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        cognito: Cognito | None = None,
        cache_device_data: bool = True,
        remember_device: bool = True,
    ):
        """Create a User instance.

        Args:
            username (str, optional): The username to login with. Defaults to None.
            password (str, optional): The password to login with. Defaults to None.
            id_token (str, optional): The id token. Defaults to None.
            access_token (str, optional): The access token. Defaults to None.
            refresh_token (str, optional): The refresh token. Defaults to None.
            cognito (Cognito, optional): A Cognito instance. Defaults to None.
            cache_device_data (bool, optional): Whether to cache the device data. Defaults to True.
            remember_device (bool, optional): Whether to remember the device. Defaults to True. Ignored\
                if cache_device_data is False.

        Raises:
            ValueError: If neither username/password nor id/access tokens are provided.
        """

        self.authenticate(
            username=username,
            password=password,
            id_token=id_token,
            access_token=access_token,
            refresh_token=refresh_token,
            cognito=cognito,
            cache_device_data=cache_device_data,
            remember_device=remember_device,
        )

        self.member_id = self.cognito.id_claims["cognito:username"]
        self.member_uuid = self.cognito.access_claims["sub"]
        self.email_address = self.cognito.id_claims["email"]

    def authenticate(
        self,
        username: str | None = None,
        password: str | None = None,
        id_token: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        cognito: Cognito | None = None,
        cache_device_data: bool = True,
        remember_device: bool = True,
    ) -> None:
        # this is to avoid boto3 trying to find credentials in the environment/local machine
        # when those credentials are not desired and may slow down the sign in process (sometimes by a lot)
        # https://github.com/boto/botocore/issues/1395#issuecomment-902244525
        client = boto3.client("cognito-idp", config=Config(signature_version=UNSIGNED))
        kwargs = {"pool_id": self.USER_POOL_ID, "client_id": self.CLIENT_ID}

        if cognito:
            self.cognito = cognito
            self.validate_cognito_tokens()
            return

        if username and password:
            dd = get_cached_device_data()
            kwargs = kwargs | dd | {"username": username, "password": password}

            self.aws = AWSSRP(**kwargs, client=client)
            tokens = self.aws.authenticate_user()
            auth_result: dict[str, Any] = tokens["AuthenticationResult"]
            if cache_device_data and not dd:
                self.handle_device_setup(remember_device, tokens)

            self.setup_cognito(auth_result["AccessToken"], auth_result["IdToken"], auth_result.get("RefreshToken"))
            return

        if access_token and id_token:
            self.setup_cognito(access_token, id_token, refresh_token)
            return

        raise ValueError("Must provide either username/password or id/access tokens.")

    def setup_cognito(self, access_token: str, id_token: str, refresh_token: str | None = None) -> None:
        """Set up the Cognito instance and validate the tokens.

        Args:
            access_token (str): The access token.
            id_token (str): The id token.
            refresh_token (str, optional): The refresh token. Defaults to None.
        """
        config = Config(signature_version=UNSIGNED)
        self.cognito = Cognito(
            self.USER_POOL_ID,
            self.CLIENT_ID,
            access_token=access_token,
            id_token=id_token,
            refresh_token=refresh_token,
            botocore_config=config,
        )
        self.validate_cognito_tokens()

    def validate_cognito_tokens(self) -> None:
        """Validate the Cognito tokens. Will refresh the tokens if necessary."""
        self.cognito.check_token()
        self.cognito.verify_tokens()

    def handle_device_setup(self, remember_device: bool, tokens: dict[str, Any]) -> None:
        """Confirms the device with AWS and caches the device data for future use.

        Args:
            remember_device (bool): Whether to remember the device.
            tokens (dict): The tokens from the AWS SRP instance.
        """
        try:
            hostname = socket.gethostname()
            device_name = f"{hostname}-otf-api"
        except Exception:
            LOGGER.exception("Failed to get device name")
            return

        try:
            auth_result = tokens["AuthenticationResult"]
            new_device_metadata = auth_result.get("NewDeviceMetadata")
            if not new_device_metadata:
                LOGGER.debug("No new device metadata")
                return

            device_key = new_device_metadata["DeviceKey"]
            device_group_key = new_device_metadata["DeviceGroupKey"]
        except KeyError:
            LOGGER.error("Failed to get device key and group key")
            return

        try:
            _, device_password = self.aws.confirm_device(tokens=tokens, device_name=device_name)
            _ = self.aws.update_device_status(remember_device, auth_result["AccessToken"], device_key)
        except Exception:
            LOGGER.exception("Failed to confirm device")
            return

        try:
            dd = {"device_key": device_key, "device_group_key": device_group_key, "device_password": device_password}
            DEVICE_KEY_CACHE_PATH.write_text(json.dumps(dd, indent=4, default=str))
        except Exception:
            LOGGER.exception("Failed to write device key cache")
            return

    def forget_device(self) -> None:
        """Forget the device from AWS and delete the device key cache."""
        access_token = self.cognito.access_token
        dd = get_cached_device_data()
        if not dd:
            LOGGER.debug("No device data to forget")
            return

        device_key = dd["device_key"]

        resp = self.aws.forget_device(access_token=access_token, device_key=device_key)
        LOGGER.debug(resp)

        DEVICE_KEY_CACHE_PATH.unlink()
        LOGGER.debug("Device key cache deleted")
