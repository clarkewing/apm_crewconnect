import json
from os import environ
from urllib.parse import urljoin
import requests
from requests_oauthlib import OAuth2Session

from exceptions import OktaClientException


class OktaClient:
    scope = ["openid", "profile", "offline_access"]
    redirect_uri = "com.apm.crewconnect:/callback"

    def __init__(self, host: str, client_id: str) -> None:
        self.client_id = client_id
        self.config = self.fetch_openid_config(host)

        # Set insecure OAuth context so we can use the configured redirect_uri
        environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    @staticmethod
    def fetch_openid_config(host) -> dict:
        return requests.get(urljoin(host, "/.well-known/openid-configuration")).json()

    def generate_auth_url(self) -> str:
        self.session = OAuth2Session(
            self.client_id,
            scope=self.scope,
            redirect_uri=self.redirect_uri,
            pkce="S256",
        )

        authorization_url, state = self.session.authorization_url(
            self.config["authorization_endpoint"],
            access_type="offline",
        )

        return authorization_url

    def retrieve_token_from_redirect(self, redirect) -> dict:
        if not isinstance(self.session, OAuth2Session):
            raise OktaClientException(
                "Okta session must be instantiated before attempting to retrieve a token."
            )

        token = self.session.fetch_token(
            self.config["token_endpoint"],
            authorization_response=redirect,
            include_client_id=True,
        )

        self.store_token(token)

        return token

    def fetch_user_info(self) -> dict[str, str | int]:
        return self.session.get(self.config["userinfo_endpoint"]).json()

    @staticmethod
    def store_token(token: dict):
        pass
