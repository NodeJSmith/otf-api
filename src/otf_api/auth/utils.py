from collections.abc import Generator
from logging import getLogger
from typing import Any

import httpx
from httpx import Request
from pycognito import Cognito

LOGGER = getLogger(__name__)


class HttpxCognitoAuth(httpx.Auth):
    http_header: str = "Authorization"
    http_header_prefix: str = "Bearer "

    def __init__(self, cognito: Cognito):
        """HTTPX Authentication extension for Cognito User Pools.

        Args:
            cognito (Cognito): A Cognito instance.
        """

        self.cognito = cognito

    def auth_flow(self, request: Request) -> Generator[Request, Any, None]:
        self.cognito.check_token(renew=True)

        token = self.cognito.id_token

        request.headers[self.http_header] = self.http_header_prefix + token

        yield request
