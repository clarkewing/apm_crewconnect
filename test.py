import dataclasses
from datetime import date, datetime, time, timedelta
from email.policy import default
import json
import statistics
from typing import Any

import requests_cache

from apm import Apm
from token_manager import TokenManager

# requests_cache.install_cache("apm")


apm = Apm("https://crewmobile.to.aero", TokenManager())


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
            total_seconds = o.total_seconds()
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            hours = int(hours)
            minutes = int(minutes)
            if minutes < 10:
                minutes = "0{}".format(minutes)
            return "{}:{}".format(hours, minutes)

        return super().default(o)


flights = apm.get_flight_schedule(date(2024, 7, 4))

flights_with_missing_crew_members = [
    flight
    for flight in flights
    if flight.aircraft_type == "73H" and flight.is_missing_crew_members("OPL")
]

print(f"Found {len(flights_with_missing_crew_members)} unstaffed flights.")

with open(".storage/schedule.json", "w+") as file:
    file.write(json.dumps(flights_with_missing_crew_members, cls=EnhancedJSONEncoder))

# pairing_options = apm.get_pairing_options(
#     date(2024, 8, 1),
#     sort_by=lambda pairing_option: (
#         pairing_option.total_on_days,
#         statistics.mean(
#             [
#                 rest_period["duration"].total_seconds()
#                 for rest_period in pairing_option.rest_periods
#             ]
#             or [0]
#         ),
#     ),
#     excluded_dates=[
#         date(2024, 8, 1),
#         date(2024, 8, 2),
#         date(2024, 8, 3),
#         date(2024, 8, 4),
#         date(2024, 8, 5),
#         date(2024, 8, 6),
#         date(2024, 8, 7),
#         date(2024, 8, 11),
#         date(2024, 8, 12),
#         date(2024, 8, 13),
#         date(2024, 8, 14),
#         date(2024, 8, 15),
#         date(2024, 8, 16),
#         date(2024, 8, 17),
#         date(2024, 8, 18),
#         date(2024, 8, 23),
#         date(2024, 8, 24),
#         date(2024, 8, 25),
#         date(2024, 8, 26),
#         date(2024, 8, 27),
#         date(2024, 8, 28),
#         date(2024, 8, 29),
#         date(2024, 8, 30),
#         date(2024, 8, 31),
#     ],
#     excluded_stopovers=["NTE", "LYS", "MRS", "MPL"],
#     minimum_on_days=3,
# )

# print(f"Found {len(pairing_options)} pairing options.")

# with open(".storage/pairing-options.json", "w+") as file:
#     file.write(json.dumps(pairing_options, cls=EnhancedJSONEncoder))
