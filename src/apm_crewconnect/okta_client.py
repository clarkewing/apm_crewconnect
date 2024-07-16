from os import environ
import time
from typing import Callable, Optional, Union
from urllib.parse import urljoin
import requests
from requests_oauthlib import OAuth2Session

from .exceptions import OktaClientException


class OktaClient:
    scope = ["openid", "profile", "offline_access"]
    redirect_uri = "com.apm.crewconnect:/callback"

    def __init__(
        self,
        host: str,
        client_id: str,
        token=None,
        token_updater: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self.host = host
        self.client_id = client_id
        self.token_updater = token_updater
        self.token = token or {}

        self._setup_oauth()
        self._init_session()

    @property
    def token(self) -> dict[str, str | int] | None:
        return getattr(self, "_token", None)

    @token.setter
    def token(self, value) -> None:
        self._token = value
        self._populate_token_attributes(value)

        if self.token_updater is not None:
            self.token_updater(value)

    @property
    def user_info(self) -> dict[str, str | int]:
        if not self.authorized:
            raise OktaClientException("You must be authenticated to access user_info")

        if not hasattr(self, "_user_info"):
            self._user_info = self.session.get(self.config["userinfo_endpoint"]).json()

        return getattr(self, "_user_info")

    @property
    def authorized(self) -> bool:
        return (
            hasattr(self, "session")
            and self.session.authorized
            and self.introspect()["active"]
        )

    @property
    def config(self) -> dict:
        if not self.host:
            raise OktaClientException("Host is required to retrieve OpenID config")

        if not hasattr(self, "_config"):
            self._config = requests.get(
                self.build_url("/.well-known/openid-configuration")
            ).json()

        return self._config

    def generate_auth_url(self) -> str:
        authorization_url, state = self.session.authorization_url(
            self.config["authorization_endpoint"],
            access_type="offline",
        )

        return authorization_url

    def fetch_token_from_redirect(self, redirect) -> dict:
        if not isinstance(self.session, OAuth2Session):
            raise OktaClientException(
                "Okta session must be instantiated before attempting to retrieve a token."
            )

        self.token = self.session.fetch_token(
            self.config["token_endpoint"],
            authorization_response=redirect,
            include_client_id=True,
        )

        return self.token

    def refresh_token(self) -> dict[str, Union[str, int]]:
        """Refresh and return a new token."""

        self.token = self.session.refresh_token(
            self.config["token_endpoint"],
            client_id=self.client_id,
        )

        return self.token

    def introspect(self) -> dict:
        return requests.post(
            self.config["introspection_endpoint"],
            data={
                "token": self.access_token,
                "token_type_hint": "access_token",
                "client_id": self.client_id,
            },
        ).json()

    def build_url(self, path: str) -> str:
        return urljoin(self.host, path)

    @staticmethod
    def _setup_oauth() -> None:
        # Allow insecure transport to enable insecure redirect_uri
        # This is necessary to ensure our custom app protocol can be used
        environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    def _init_session(self):
        if self.token:
            self.session = OAuth2Session(
                self.client_id,
                token=self.token,
            )
        else:
            self.session = OAuth2Session(
                self.client_id,
                scope=self.scope,
                redirect_uri=self.redirect_uri,
                pkce="S256",
            )

    def _populate_token_attributes(self, response):
        """Add attributes from a token exchange response to self."""

        if "access_token" in response:
            self.access_token = response.get("access_token")

        if "token_type" in response:
            self.token_type = response.get("token_type")

        if "expires_in" in response:
            self.expires_in = response.get("expires_in")
            self._expires_at = time.time() + int(self.expires_in)

        if "expires_at" in response:
            try:
                self._expires_at = int(response.get("expires_at"))
            except:
                self._expires_at = None
