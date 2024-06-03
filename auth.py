from typing import Optional, Union, Callable, Dict
from urllib.parse import urljoin
import requests
from requests import Response
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError


class Auth:
    def __init__(
        self,
        host: str,
        token: Optional[Dict[str, str]] = None,
        client_id: str = None,
        token_updater: Optional[Callable[[str], None]] = None,
    ):
        self.host = host
        self.config = self.fetch_openid_config(host)
        self.client_id = client_id
        self.token_updater = token_updater

        extra = {"client_id": self.client_id}

        self._oauth = OAuth2Session(
            auto_refresh_kwargs=extra,
            client_id=client_id,
            token=token,
            token_updater=token_updater,
        )

    def refresh_tokens(self) -> Dict[str, Union[str, int]]:
        """Refresh and return new tokens."""
        token = self._oauth.refresh_token(
            self.config["https://transaviafr.okta-emea.com/oauth2/v1/token"]
        )

        if self.token_updater is not None:
            self.token_updater(token)

        return token

    def request(self, method: str, path: str, **kwargs) -> Response:
        """Make a request.

        We don't use the built-in token refresh mechanism of OAuth2 session because
        we want to allow overriding the token refresh logic.
        """
        url = f"{self.host}/{path}"
        try:
            return getattr(self._oauth, method)(url, **kwargs)
        except TokenExpiredError:
            self._oauth.token = self.refresh_tokens()

            return self.request(method, path, **kwargs)

    @staticmethod
    def fetch_openid_config(host: str):
        well_known_config_url = urljoin(host, "/.well-known/openid-configuration")

        return requests.get(well_known_config_url).json()
