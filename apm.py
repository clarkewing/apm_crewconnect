from datetime import date, timedelta
from typing import Callable, Iterable, Optional, Union

from apm_client import ApmClient
from models.flight import Flight
from token_manager import TokenManager


class Apm:
    def __init__(
        self,
        host: str,
        token_manager: Optional[TokenManager] = None,
    ):
        self.host = host
        self.token_manager = token_manager

        self._setup_client(host)

    @property
    def user_id(self) -> str:
        return self.client.user_id

    def get_flight_schedule(
        self,
        start_date: date,
        end_date: date | None = None,
    ) -> list:
        """
        Get the flight schedule for a specified date range.

        :param start_date: The beginning of the date range.
        :param end_date: An optional end for the date range.
                         If not set, only one day of the schedule will be returned.
        :return: The requested flight schedule
        """

        # Set default value for end_date
        end_date = end_date or start_date

        flight_schedule = self.client.request(
            "get",
            f"/api/crews/{self.user_id}/flight-schedule",
            params={
                "from": start_date.isoformat(),
                "to": (end_date + timedelta(days=1)).isoformat(),  # 'to' is exclusive
                "zoneOffset": "Z",
            },
        ).json()

        flights = [
            Flight.from_dict(flight)
            for aircraft_by_date in flight_schedule["_embedded"][
                "companyAircraftByDateDtoList"
            ]
            for aircraft in aircraft_by_date["aircraftList"]["_embedded"][
                "companyAircraftDtoList"
            ]
            for flight in aircraft["sectors"]
        ]

        return flights

    def _setup_client(self, host):
        if self.token_manager:
            apm_token_updater = lambda token: self.token_manager.set(
                key="apm", value=token
            )
            okta_token_updater = lambda token: self.token_manager.set(
                key="okta", value=token
            )

            if self.token_manager.has("apm") and self.token_manager.has("okta"):
                self.client = ApmClient(
                    host,
                    token=self.token_manager.get("apm"),
                    token_updater=apm_token_updater,
                )
                self.client.setup_okta_client(
                    token=self.token_manager.get("okta"),
                    token_updater=okta_token_updater,
                )
            else:
                self.client = ApmClient(host, token_updater=apm_token_updater)
                self.client.setup_okta_client(token_updater=okta_token_updater)

                self._authenticate_client()
        else:
            self.client = ApmClient(host)
            self.client.setup_okta_client()

            self._authenticate_client()

    def _authenticate_client(self):
        authorization_url = self.client.okta_client.generate_auth_url()

        print("Please go here and authorize:")
        print(authorization_url)
        print()

        redirect = input("Paste in the full redirect URL: ")
        print()

        self.client.okta_client.fetch_token_from_redirect(redirect)

        self.client.fetch_token()
