from operator import itemgetter
from urllib.parse import urljoin
import requests

from exceptions import ApmClientException
from okta_client import OktaClient


class ApmClient:
    def __init__(self, host: str) -> None:
        self.host = host
        self.config = self.fetch_server_config(host)

    @staticmethod
    def fetch_server_config(host: str) -> dict:
        return requests.get(urljoin(host, "/api/config")).json()

    def authenticate(self):
        match self.config["authenticationMode"]:
            case "okta":
                user_id, access_token = itemgetter("crewCode", "access_token")(
                    self.get_okta_credentials()
                )

            case _:
                raise ApmClientException(
                    f"Authentication mode not implemented: {self.config['authenticationMode']}"
                )

        self.credentials = requests.post(
            urljoin(self.host, "/login"),
            json={"userId": user_id, "accessToken": access_token},
        ).json()

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        Make a request.

        We don't use the built-in token refresh mechanism of OAuth2 session because
        we want to allow overriding the token refresh logic.
        """
        url = urljoin(self.host, path)

        return requests.request(
            method,
            url,
            headers={"Authorization": f"Bearer {self.credentials['token']}"},
            **kwargs,
        )

    def get_okta_credentials(self) -> dict[str, str]:
        okta = OktaClient(self.config["discoveryUri"], self.config["clientId"])

        authorization_url = okta.generate_auth_url()

        print("Please go here and authorize:")
        print(authorization_url)
        print()

        redirect = input("Paste in the full redirect URL: ")

        token = okta.retrieve_token_from_redirect(redirect)
        user_info = okta.fetch_user_info()

        return token | user_info
