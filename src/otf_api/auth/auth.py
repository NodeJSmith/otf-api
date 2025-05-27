# pyright: reportTypedDictNotRequiredAccess=none
import platform
import typing
from collections.abc import Generator
from datetime import datetime
from logging import getLogger
from time import sleep
from typing import Any, ClassVar

import httpx
import jwt
from boto3 import Session
from botocore import UNSIGNED
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.config import Config
from botocore.credentials import Credentials
from botocore.exceptions import ClientError
from pycognito import AWSSRP, Cognito
from pycognito.aws_srp import generate_hash_device

from otf_api.cache import get_cache

if typing.TYPE_CHECKING:
    from mypy_boto3_cognito_identity import CognitoIdentityClient
    from mypy_boto3_cognito_identity.type_defs import CredentialsTypeDef
    from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
    from mypy_boto3_cognito_idp.type_defs import InitiateAuthResponseTypeDef

LOGGER = getLogger(__name__)

CLIENT_ID = "1457d19r0pcjgmp5agooi0rb1b"  # from android app
REGION = "us-east-1"
USER_POOL_ID = "us-east-1_dYDxUeyL1"
ID_POOL_ID = f"{REGION}:4943c880-fb02-4fd7-bc37-2f4c32ecb2a3"
PROVIDER_KEY = f"cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"
BOTO_CONFIG = Config(region_name=REGION, signature_version=UNSIGNED)
CACHE = get_cache()


class NoCredentialsError(Exception):
    """Raised when no credentials are found."""


class OtfCognito(Cognito):
    """A subclass of the pycognito Cognito class that adds the device_key to the auth_params.

    Without this being set the renew_access_token call will always fail with NOT_AUTHORIZED.
    """

    user_pool_id: ClassVar[str] = USER_POOL_ID
    client_id: ClassVar[str] = CLIENT_ID
    user_pool_region: ClassVar[str] = REGION
    client_secret: ClassVar[str] = ""

    id_token: str
    access_token: str
    device_key: str
    device_group_key: str
    device_password: str
    device_name: str

    @property
    def expiration_seconds(self) -> int:
        """Returns the expiration time of the access token in seconds.

        This is useful for checking if the access token is still valid.

        Returns:
            int: The expiration time of the access token in seconds.
        """
        if not self.access_token:
            raise AttributeError("Access Token Required to Check Token")
        return self.get_decoded_access_token()["exp"] - int(datetime.now().timestamp())  # noqa: DTZ005

    @property
    def acces_token_expiration(self) -> int:
        """Returns the expiration time of the access token in seconds."""
        return datetime.fromtimestamp(self.get_decoded_access_token()["exp"])  # type: ignore # noqa: DTZ006

    @property
    def tokens(self) -> dict[str, str]:
        """Returns the tokens as a dictionary."""
        tokens = {
            "access_token": self.access_token,
            "id_token": self.id_token,
            "refresh_token": self.refresh_token,
        }
        return {k: v for k, v in tokens.items() if v}

    @property
    def device_metadata(self) -> dict[str, str]:
        """Returns the device metadata as a dictionary."""
        dm = {
            "device_key": self.device_key,
            "device_group_key": self.device_group_key,
            "device_password": self.device_password,
        }
        return {k: v for k, v in dm.items() if v}

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        id_token: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ):
        self.username = username
        self.id_token = id_token  # type: ignore
        self.access_token = access_token  # type: ignore
        self.refresh_token = refresh_token

        self.id_claims: dict[str, Any] = {}
        self.access_claims: dict[str, Any] = {}
        self.custom_attributes: dict[str, Any] = {}
        self.base_attributes: dict[str, Any] = {}
        self.pool_jwk: dict[str, Any] = {}
        self.mfa_tokens: dict[str, Any] = {}
        self.pool_domain_url: str | None = None

        self.idp_client: CognitoIdentityProviderClient = Session().client(
            "cognito-idp", config=BOTO_CONFIG, region_name=REGION
        )  # type: ignore

        self.id_client: CognitoIdentityClient = Session().client(
            "cognito-identity", config=BOTO_CONFIG, region_name=REGION
        )  # type: ignore

        self.handle_login(password)

    def handle_login(self, password: str | None = None) -> None:
        """Handles the login process for the user.

        This will set the tokens and device metadata.
        If the user is not logged in, it will attempt to login with the provided username and password.
        If the user is already logged in, it will check the tokens and refresh them if necessary.

        Args:
            password (str, optional): The password to use for login. If not provided, the user will be prompted for it.
        """
        self.set_attributes_from_cache()

        if not (self.username and password) and not (self.id_token and self.access_token):
            raise NoCredentialsError("No credentials provided and no tokens cached, cannot authenticate")

        if self.username and password:
            self.login_with_password(password)
            return

        # at this point we have tokens, so let's hand it off to the proper method
        self.authenticate_with_saved_tokens()

    def set_attributes_from_cache(self) -> None:
        """Sets the attributes from the cache.

        This is useful for initializing the Cognito instance with tokens that have been previously cached.
        It will read the tokens and device metadata from the cache and set the instance attributes accordingly.
        """
        token_cache = CACHE.read_token_data_from_cache()
        self.id_token = self.id_token or token_cache.get("id_token")  # type: ignore
        self.access_token = self.access_token or token_cache.get("access_token")  # type: ignore
        self.refresh_token = self.refresh_token or token_cache.get("refresh_token")  # type: ignore

        dd_cache = CACHE.read_device_data_from_cache()
        self.device_key = dd_cache.get("device_key") or ""
        self.device_group_key = dd_cache.get("device_group_key") or ""
        self.device_password = dd_cache.get("device_password") or ""

    def get_identity_credentials(self) -> "CredentialsTypeDef":
        """Get the AWS credentials for the user using the Cognito Identity Pool.

        This is used to access AWS resources using the Cognito Identity Pool.

        Returns:
            CredentialsTypeDef: The AWS credentials for the user.
        """
        cognito_id = self.id_client.get_id(IdentityPoolId=ID_POOL_ID, Logins={PROVIDER_KEY: self.id_token})
        creds = self.id_client.get_credentials_for_identity(
            IdentityId=cognito_id["IdentityId"], Logins={PROVIDER_KEY: self.id_token}
        )
        return creds["Credentials"]

    def get_decoded_access_token(self) -> dict[str, Any]:
        """Decodes the access token without verifying the signature.

        This is useful for checking the expiration time of the access token.

        Returns:
            dict[str, Any]: The decoded access token.
        """
        if not self.access_token:
            raise AttributeError("Access Token Required to Check Token")
        dec_access_token = jwt.decode(self.access_token, options={"verify_signature": False})
        return dec_access_token

    def authenticate_with_saved_tokens(self) -> None:
        """Authenticate using saved tokens from the cache.

        This method is useful for initializing the Cognito instance with tokens that have been previously cached.
        It will verify the tokens and set the device metadata if available.
        """
        self.check_token()
        self.verify_tokens()

    def login_with_password(self, password: str) -> None:
        """Called when logging in with a username and password. Will set the tokens and device metadata."""
        LOGGER.debug("Logging in with username and password...")

        aws = AWSSRP(
            username=self.username,
            password=password,
            pool_id=USER_POOL_ID,
            client_id=CLIENT_ID,
            client=self.idp_client,
        )
        try:
            tokens: InitiateAuthResponseTypeDef = aws.authenticate_user()
        except ClientError as e:
            code = e.response["Error"]["Code"]
            msg = e.response["Error"]["Message"]
            if "UserLambdaValidationException" in msg or "UserLambdaValidation" in code:
                sleep(5)
                tokens = aws.authenticate_user()
            else:
                raise

        self._set_tokens(tokens)
        self._handle_device_setup()

    def _handle_device_setup(self) -> None:
        """Confirms the device with Cognito and caches the device metadata.

        Devices are not remembered at this time, as OTF does not have MFA set up currently. Without MFA setup, there
        is no benefit to remembering the device. Additionally, it does not appear that the OTF app remembers devices,
        so this matches the behavior of the app.
        """
        dd = CACHE.read_device_data_from_cache()
        self.device_key = dd.get("device_key") or ""
        self.device_group_key = dd.get("device_group_key") or ""
        self.device_password = dd.get("device_password") or ""
        self.device_name = platform.node()

        if not self.device_key:
            raise ValueError("Device key not set - device key is required by this Cognito pool")

        self.device_password, device_secret_verifier_config = generate_hash_device(
            self.device_group_key, self.device_key
        )

        self.idp_client.confirm_device(
            AccessToken=self.access_token,
            DeviceKey=self.device_key,
            DeviceSecretVerifierConfig=device_secret_verifier_config,  # type: ignore (pycognito is untyped)
            DeviceName=self.device_name,
        )

        try:
            CACHE.write_device_data_to_cache(self.device_metadata)
        except Exception:
            LOGGER.exception("Failed to write device key cache")

    ##### OVERRIDDEN METHODS #####

    def verify_tokens(self) -> None:
        """Verifies the current id_token and access_token.

        This method will also write the tokens to the cache if they are valid.
        It is useful to call this method after creating a Cognito instance where you've provided
        externally-remembered token values.
        """
        self.verify_token(self.id_token, "id_token", "id")
        self.verify_token(self.access_token, "access_token", "access")
        CACHE.write_token_data_to_cache(self.tokens, self.expiration_seconds)

    def check_token(self, renew: bool = True) -> bool:
        """Checks the exp attribute of the access_token and refreshes it if it has expired and renew is True.

        Args:
            renew (bool): whether to refresh on expiration

        Raises:
            AttributeError: If access_token is not set
            NoCredentialsError: If refresh token has expired

        Returns:
            bool: True if the access_token has expired, False otherwise
        """
        try:
            return super().check_token(renew=renew)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NotAuthorizedException":
                LOGGER.warning("Tokens expired, attempting to login with username and password")
                CACHE.clear()
                raise NoCredentialsError("Cached tokens expired, please login again") from e
            raise

    def renew_access_token(self) -> None:
        """Sets a new access token on the User using the cached refresh token and device metadata.

        Overridden to add the device key to the auth_params if it is set. Without this all calls to renew_access_token
        will fail with NOT_AUTHORIZED. Also skips the call to _add_secret_hash since we don't have a client secret.

        # https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_InitiateAuth.html#CognitoUserPools-InitiateAuth-request-AuthFlow

        """
        if not self.device_key:
            raise ValueError("Device key not set - device key is required by this Cognito pool")

        if not self.refresh_token:
            raise ValueError("No refresh token set - cannot renew access token")

        refresh_response = self.idp_client.initiate_auth(
            ClientId=self.client_id,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": self.refresh_token, "DEVICE_KEY": self.device_key},
        )
        self._set_tokens(refresh_response)

    def _set_tokens(self, tokens: "InitiateAuthResponseTypeDef") -> None:
        """Helper function to verify and set token attributes based on a Cognito AuthenticationResult.

        Overridden to cache the tokens and set/cache the device metadata.
        """
        auth_result = tokens["AuthenticationResult"]
        device_metadata = auth_result.get("NewDeviceMetadata", {})

        assert "AccessToken" in auth_result, "AccessToken not found in AuthenticationResult"
        assert "IdToken" in auth_result, "IdToken not found in AuthenticationResult"

        # tokens - refresh token defaults to existing value if not present
        # note: verify_token also sets the token attribute
        self.verify_token(auth_result["AccessToken"], "access_token", "access")
        self.verify_token(auth_result["IdToken"], "id_token", "id")
        self.refresh_token = auth_result.get("RefreshToken", self.refresh_token)
        CACHE.write_token_data_to_cache(self.tokens, self.expiration_seconds)

        # device metadata - default to existing values if not present
        self.device_key = device_metadata.get("DeviceKey", self.device_key)
        self.device_group_key = device_metadata.get("DeviceGroupKey", self.device_group_key)
        CACHE.write_device_data_to_cache(self.device_metadata)


class HttpxCognitoAuth(httpx.Auth):
    http_header: str = "Authorization"
    http_header_prefix: str = "Bearer "

    def __init__(self, cognito: OtfCognito):
        """HTTPX Authentication extension for Cognito User Pools.

        Args:
            cognito (Cognito): A Cognito instance.
        """
        self.cognito = cognito

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, Any, None]:
        """Add the Cognito access token to the request headers."""
        self.cognito.check_token(renew=True)

        token = self.cognito.id_token

        assert isinstance(token, str), "Token is not a string"

        request.headers[self.http_header] = self.http_header_prefix + token

        # If the request has the SIGV4AUTH_REQUIRED header, sign the request
        # used by very few endpoints, but I expect that may change in the future
        if request.headers.get("SIGV4AUTH_REQUIRED"):
            del request.headers["SIGV4AUTH_REQUIRED"]
            yield from self.sign_httpx_request(request)
            return

        yield request

    def sign_httpx_request(self, request: httpx.Request) -> Generator[httpx.Request, Any, None]:
        """Sign an HTTP request using AWS SigV4 for use with httpx."""
        headers = request.headers.copy()

        # ensure this header is not included, it will break the signature
        headers.pop("connection", None)

        body = b"" if request.method in ("GET", "HEAD") else request.content or b""

        if hasattr(body, "read"):
            raise ValueError("Streaming bodies are not supported in signed requests")

        creds = self.cognito.get_identity_credentials()

        credentials = Credentials(
            access_key=creds["AccessKeyId"], secret_key=creds["SecretKey"], token=creds["SessionToken"]
        )

        aws_request = AWSRequest(method=request.method, url=str(request.url), data=body, headers=headers)

        SigV4Auth(credentials, "execute-api", REGION).add_auth(aws_request)

        signed_headers = dict(aws_request.headers.items())

        # Return a brand new request object with signed headers
        signed_request = httpx.Request(
            method=request.method,
            url=request.url,
            headers=signed_headers,
            content=body,
        )

        yield signed_request
