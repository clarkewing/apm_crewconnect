import sys

sys.path.append("./src")

import dataclasses
from datetime import date, datetime, time, timedelta, timezone
from email.policy import default
import json
import statistics
from typing import Any

from apm_crewconnect import Apm, utils
import requests_cache

from file_token_manager import FileTokenManager

# requests_cache.install_cache("apm")


apm = Apm("https://crewmobile.to.aero", FileTokenManager())


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "to_dict"):
            return o.to_dict()

        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)

        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, date):
            return o.isoformat()

        if isinstance(o, time):
            return o.isoformat()

        if isinstance(o, timedelta):
            return utils.timedelta_to_str(o)

        if isinstance(o, timezone):
            return utils.timezone_to_offset_str(o)

        return super().default(o)


with open(".storage/roster.json", "w+") as file:
    # roster = apm.get_roster(date.today(), date.today() + timedelta(days=30))
    roster = apm.get_roster(date(2024, 11, 1), date(2024, 12, 31))

    file.write(json.dumps(roster, cls=EnhancedJSONEncoder))

# with open(".storage/schedule.json", "w+") as file:
#     flight_schedule = apm.get_flight_schedule(date.today())

#     # flight_schedule = [
#     #     flight for flight in flight_schedule if flight.aircraft_registration == "FHUYE"
#     # ]

#     file.write(json.dumps(flight_schedule, cls=EnhancedJSONEncoder))

# with open(".storage/test.json", "w+") as file:
#     output = apm.client.request("GET", "/api/airports/ORY")

#     print(output)

#     file.write(json.dumps(output.json(), cls=EnhancedJSONEncoder))

# flights = apm.get_flight_schedule(date(2024, 7, 22))

# flights_with_missing_crew_members = [
#     flight
#     for flight in flights
#     if flight.aircraft_type == "73H" and flight.is_missing_crew_members("OPL")
# ]

# flights_with_missing_crew_members.sort(
#     key=lambda flight: flight.departure_time.isoformat()
# )

# print(f"Found {len(flights_with_missing_crew_members)} unstaffed flights.")

# with open(".storage/schedule.json", "w+") as file:
#     file.write(json.dumps(flights_with_missing_crew_members, cls=EnhancedJSONEncoder))

# pairing_options = apm.get_pairing_options(
#     date(2024, 11, 1),
#     sort_by=lambda pairing_option: (
#         statistics.mean(
#             [
#                 rest_period["duration"].total_seconds()
#                 for rest_period in pairing_option.rest_periods
#             ]
#             or [0]
#         ),
#         pairing_option.total_on_days,
#     ),
#     excluded_dates=(
#         [date(2024, 11, 15), date(2024, 11, 16)]
#         + utils.date_range(date(2024, 11, 25), date(2024, 11, 29))
#     ),
#     stopovers=["PGF"],
#     # excluded_stopovers=["NTE", "LYS", "MRS"],
#     minimum_on_days=2,
#     without_bidders="OPL",
# )

# print(f"Found {len(pairing_options)} pairing options.")

# with open(".storage/pairing-options.json", "w+") as file:
#     file.write(json.dumps(pairing_options, cls=EnhancedJSONEncoder))
