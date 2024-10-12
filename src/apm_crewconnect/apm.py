from datetime import UTC, date, datetime, timedelta
import json
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError, MismatchingStateError
import re
import statistics
from typing import Callable, List, Optional

from .models.activity import Activity
from .models.roster import Roster

from .apm_client import ApmClient
from .exceptions import InvalidAuthRedirectException

from .interfaces.token_manager_interface import TokenManagerInterface
from .models.duty_period import DutyPeriod
from .models.flight import Flight
from .models.pairing import Pairing
from .utils import dates_in_range


class Apm:
    roster = {}

    def __init__(
        self,
        host: str,
        token_manager: Optional[TokenManagerInterface] = None,
        manual_auth: bool = False,
    ):
        self.host = host
        self.token_manager = token_manager
        self.manual_auth = manual_auth

        self._setup_client(host)

    @property
    def user_id(self) -> str:
        return self.client.user_id

    def get_roster(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Roster:
        if start_date is None:
            start_date = date.today()

        if end_date is None:
            end_date = start_date + timedelta(days=30)

        if isinstance(start_date, date):
            start_date = datetime.combine(start_date, datetime.min.time(), UTC)

        if isinstance(end_date, date):
            end_date = datetime.combine(end_date, datetime.max.time(), UTC)
            end_date = end_date.replace(microsecond=0)

        response = self.client.request(
            "get",
            f"/api/crews/{self.user_id}/roster-calendars",
            params={
                "dateFrom": start_date.isoformat(),
                "dateTo": (end_date + timedelta(days=1)).isoformat(),
                "zoneOffset": "Z",
            },
        ).json()

        return Roster(
            user_id=self.user_id,
            start=datetime.fromisoformat(response["utcCalendar"][0]["day"]).date(),
            end=datetime.fromisoformat(response["utcCalendar"][-1]["day"]).date(),
            activities=list(
                {
                    activity.id: activity
                    for calendar_day in response["utcCalendar"]
                    for activity in map(
                        Activity.from_roster,
                        calendar_day["crewActivities"],
                    )
                    if activity is not None
                }.values()
            ),
        )

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
        without_bidders: Optional[str] = None,
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

        page = 1

        while page == 1 or "_embedded" in response:
            response = self.client.request(
                "get",
                f"/api/crews/{self.user_id}/pairing-requests",
                params={
                    "referenceDate": reference_date.strftime("%Y-%m-%dT%H:%MZ"),
                    "isLocal": True,
                    "page": page,
                }
                | filters,
            )

            if "error" in response.json():
                raise Exception(response.json()["error"])

            response = response.json()

            if "_embedded" in response:
                pairing_options += [
                    Pairing.from_dict(pairing_option)
                    for pairing_option in response["_embedded"]["pairingRequestDtoList"]
                ]

                print("Retrieved results page " + str(page))

            page += 1

        # while "_links" in response and "next" in response["_links"]:
        #     response = self.client.request(
        #         "get",
        #         response["_links"]["next"]["href"],
        #     ).json()

        #     if "_embedded" in response:
        #         pairing_options += [
        #             Pairing.from_dict(pairing_option)
        #             for pairing_option in response["_embedded"]["pairingRequestDtoList"]
        #         ]

        #     print(
        #         "Retrieved results page "
        #         + re.search("page=([0-9]*)", response["_links"]["self"]["href"]).group(
        #             1
        #         )
        #     )

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
                if len(
                    [
                        pairing_request_crews["crewRequestCrewDtos"]
                        for pairing_request_crews in response[
                            "pairingRequestCrewByRoleDtos"
                        ]
                        if pairing_request_crews["roleCode"] == without_bidders
                    ]
                )
                == 0
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

            if (
                self.token_manager.has("apm")
                and self.token_manager.has("okta")
                and self.token_manager.get("apm")
                and self.token_manager.get("okta")
            ):
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

                if not self.manual_auth:
                    self._authenticate_client()
        else:
            self.client = ApmClient(host)
            self.client.setup_okta_client()

            if not self.manual_auth:
                self._authenticate_client()

    def _authenticate_client(self):
        print("Please go here and authorize:")
        print(self.generate_auth_url())
        print()

        redirect = input("Paste in the full redirect URL: ")
        print()

        self.authenticate_from_redirect(redirect)

    def generate_auth_url(self) -> str:
        return self.client.okta_client.generate_auth_url()

    def authenticate_from_redirect(self, redirect: str) -> None:
        try:
            self.client.okta_client.fetch_token_from_redirect(redirect)
            self.client.fetch_token()
        except (InvalidGrantError, MismatchingStateError):
            raise InvalidAuthRedirectException
