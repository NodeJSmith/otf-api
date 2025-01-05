import typing
from collections.abc import Generator
from logging import getLogger
from typing import Any

import attrs
import httpx
from httpx import Request
from pycognito import Cognito

if typing.TYPE_CHECKING:
    from mypy_boto3_cognito_idp.type_defs import AuthenticationResultTypeTypeDef

LOGGER = getLogger(__name__)


class HttpxCognitoAuth(httpx.Auth):
    http_header: str = "Authorization"
    http_header_prefix: str = "Bearer "

    def __init__(self, cognito: Cognito):
        """HTTPX Authentication extension for Cognito User Pools.

        Args:
            cognito (Cognito): A Cognito instance.
        """

        self.cognito_client = cognito

    def auth_flow(self, request: Request) -> Generator[Request, Any, None]:
        self.cognito_client.check_token(renew=True)

        token = self.cognito_client.id_token

        request.headers[self.http_header] = self.http_header_prefix + token

        yield request


@attrs.define
class CognitoTokens:
    access_token: str
    id_token: str
    refresh_token: str | None = None
    device_key: str | None = None
    device_group_key: str | None = None

    def to_aws_format(self) -> "AuthenticationResultTypeTypeDef":
        """Convert the tokens to the format expected by the AWS SRP client."""
        output: AuthenticationResultTypeTypeDef = {"AccessToken": self.access_token, "IdToken": self.id_token}

        if self.refresh_token:
            output["RefreshToken"] = self.refresh_token
        if self.device_key and self.device_group_key:
            output["NewDeviceMetadata"] = {
                "DeviceKey": self.device_key,
                "DeviceGroupKey": self.device_group_key,
            }

        return output
