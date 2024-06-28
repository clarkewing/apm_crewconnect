from datetime import date, timedelta
import json
import re
import statistics
from typing import Callable, List, Optional

import jsonpickle

from apm_client import ApmClient
from models.duty_period import DutyPeriod
from models.flight import Flight
from models.pairing import Pairing
from token_manager import TokenManager
from utils import dates_in_range


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
        )

        with open(".storage/request.json", "w+") as file:
            file.write(jsonpickle.encode(flight_schedule))
            file.write(json.dumps(flight_schedule.json()))

        flight_schedule = flight_schedule.json()

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

    def get_pairing_options(
        self,
        reference_date: date,
        sort_by: str | set[str] | Callable = "rest",
        airports: List[str] = [],
        stopovers: List[str] = [],
        flight_numbers: List[str] = [],
        total_on_days: Optional[int] = None,
        consecutive_stopover_nights: Optional[int] = None,
        excluded_dates: List[date] = [],
        excluded_stopovers: List[str] = [],
        minimum_on_days: int = 1,
    ) -> list:
        """
        Get the pairing options for a specified reference date.

        :param reference_date: The beginning of the date range.
        :param sort_by: The attribute or callable which should be used to sort the results.
        :param airports: A list of airports to filter the pairing options.
        :param stopovers: A list of stopovers to filter the pairing options.
        :param flight_numbers: A list of flight numbers to filter the pairing options.
        :param total_on_days: The number of ON days to filter the pairing options by.
        :param consecutive_stopover_nights: The number of consecutive stopovers nights
                                            to filter the pairing options by.
        :excluded_dates: A list of dates to be excluded from results.
        :excluded_stopovers: A list of stopovers to be excluded from results.
        :return: The filtered pairing options.
        """

        pairing_options = []
        filters = {}

        if len(airports) > 0:
            filters["airports"] = " ".join(airports)

        if len(stopovers) > 0:
            filters["stopovers"] = " ".join(stopovers)

        if len(flight_numbers) > 0:
            filters["flightNumbers"] = " ".join(flight_numbers)

        if total_on_days is not None:
            filters["totalOverlappingDays"] = total_on_days

        if consecutive_stopover_nights is not None:
            filters["consecutiveNightStopover"] = consecutive_stopover_nights

        response = self.client.request(
            "get",
            f"/api/crews/{self.user_id}/pairing-requests",
            params={
                "referenceDate": reference_date.isoformat(),
                "isLocal": True,
            }
            | filters,
        ).json()

        if "_embedded" in response:
            pairing_options += [
                Pairing.from_dict(pairing_option)
                for pairing_option in response["_embedded"]["pairingRequestDtoList"]
            ]

        print("Retrieved results page 1")

        while "next" in response["_links"]:
            response = self.client.request(
                "get",
                response["_links"]["next"]["href"],
            ).json()

            if "_embedded" in response:
                pairing_options += [
                    Pairing.from_dict(pairing_option)
                    for pairing_option in response["_embedded"]["pairingRequestDtoList"]
                ]

            print(
                "Retrieved results page "
                + re.search("page=([0-9]*)", response["_links"]["self"]["href"]).group(
                    1
                )
            )

        # Exclude unwanted dates
        pairing_options = list(
            filter(
                lambda pairing_option: not dates_in_range(
                    excluded_dates,
                    pairing_option.scheduled_departure_date,
                    pairing_option.scheduled_arrival_date,
                ),
                pairing_options,
            )
        )

        # Exclude unwanted stopovers
        pairing_options = list(
            filter(
                lambda pairing_option: len(
                    set(pairing_option.stopover_airports) - set(excluded_stopovers)
                )
                == len(pairing_option.stopover_airports),
                pairing_options,
            )
        )

        # Include only pairing matching minimum on days
        pairing_options = list(
            filter(
                lambda pairing_option: pairing_option.total_on_days >= minimum_on_days,
                pairing_options,
            )
        )

        for pairing_option in pairing_options:
            response = self.client.request(
                "get",
                f"/api/crews/{self.user_id}/pairing-requests/{pairing_option.id}/details",
                params={"zoneOffset": "+0200"},
            ).json()

            pairing_option.duty_periods = [
                DutyPeriod.from_dict(duty_period_dto)
                for duty_period_dto in response["dutyPeriodRequestDtos"]
            ]

            print("Retrieved duty periods for pairing ID " + str(pairing_option.id))

        # sorters = {
        #     "rest": lambda pairing_option: statistics.mean(
        #         [
        #             rest_period["duration"].total_seconds()
        #             for rest_period in pairing_option.rest_periods
        #         ]
        #     ),
        #     "block": lambda pairing_option: statistics.mean(
        #         [
        #             duty_period.block.total_seconds()
        #             for duty_period in pairing_option.duty_periods
        #         ]
        #     ),
        #     "total_on_days": lambda pairing_option: pairing_option.total_on_days,
        # }

        match sort_by:
            case "rest":
                sort_by = lambda pairing_option: statistics.mean(
                    [
                        rest_period["duration"].total_seconds()
                        for rest_period in pairing_option.rest_periods
                    ]
                )
            case "block":
                sort_by = lambda pairing_option: statistics.mean(
                    [
                        duty_period.block.total_seconds()
                        for duty_period in pairing_option.duty_periods
                    ]
                )
            case "total_on_days":
                sort_by = "total_on_days"

        pairing_options.sort(
            key=sort_by,
            reverse=True,
        )

        return pairing_options

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
