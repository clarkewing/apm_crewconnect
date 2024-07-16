from typing import Callable, Mapping, Optional, Union
from urllib.parse import urljoin
import requests

from .exceptions import ApmClientException
from .okta_client import OktaClient


class ApmClient:
    def __init__(
        self,
        host: str,
        token=None,
        token_updater: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self.host = host
        self.token_updater = token_updater
        self.token = token or {}

    @property
    def token(self):
        return getattr(self, "_token", None)

    @token.setter
    def token(self, value) -> None:
        self._token = value
        self._populate_token_attributes(value)

        if self.token_updater is not None:
            self.token_updater(value)

    @property
    def authorized(self) -> bool:
        return hasattr(self, "access_token") and self.introspect()["active"]

    @property
    def config(self) -> dict:
        if not hasattr(self, "_config"):
            self._config = requests.get(self.build_url("/api/config")).json()

        return self._config

    def fetch_token(self) -> dict[str, Union[str, int]]:
        if "okta" not in self.config["ssoConfiguration"]["baseUrl"]:
            raise ApmClientException(
                f"Authentication mode not implemented: {self.config["ssoConfiguration"]["baseUrl"]}"
            )

        credentials = {
            "userId": self.okta_client.user_info["crewCode"],
            "accessToken": self.okta_client.token.get("access_token"),
        }

        response = requests.post(
            self.build_url("/login"),
            json=credentials,
        )

        if response.status_code == 403:
            raise ApmClientException("APM login failed.")

        self.token = response.json()

        return self.token

    def refresh_token(self) -> dict[str, Union[str, int]]:
        """Refresh and return a new token."""

        if not self.okta_client:
            raise ApmClientException("An Okta Client must be provided to proceed")

        self.okta_client.refresh_token()

        return self.fetch_token()

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        Make a request.

        We don't use the built-in token refresh mechanism of OAuth2 session because
        we want to allow overriding the token refresh logic.
        """
        response = requests.request(
            method,
            self.build_url(path),
            headers={"Authorization": f"Bearer {self.access_token}"},
            **kwargs,
        )

        if response.status_code in (401, 403) and not self.authorized:
            print("APM token expired. Refreshing.")
            self.refresh_token()
            return self.request(method, path, **kwargs)

        return response

    def introspect(self) -> dict:
        return requests.get(
            self.build_url("/api/token/introspect"),
            params={"token": self.access_token},
        ).json()

    def setup_okta_client(self, **kwargs) -> None:
        self.okta_client = OktaClient(
            self.config["ssoConfiguration"]["baseUrl"],
            self.config["ssoConfiguration"]["clientId"],
            **kwargs,
        )

    def build_url(self, path: str) -> str:
        return urljoin(self.host, path)

    def _get_okta_credentials(self) -> Mapping:
        if not self.okta_client:
            raise ApmClientException("An Okta Client must be provided to proceed")

        if not self.okta_client.authorized:
            raise ApmClientException(
                "The provided Okta Client must be authorized to proceed"
            )

        return self.okta_client.token | self.okta_client.user_info  # type: ignore

    def _populate_token_attributes(self, response: dict) -> None:
        """Add attributes from a token exchange response to self."""

        if "userId" in response:
            self.user_id = str(response.get("userId"))

        if "token" in response:
            self.access_token = str(response.get("token"))
