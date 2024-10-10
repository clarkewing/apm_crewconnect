from dataclasses import dataclass
import dataclasses
from datetime import date, datetime
from functools import reduce
import operator
from typing import List, Optional
import humps

from .duty_period import DutyPeriod


@dataclass
class Pairing:
    id: int
    key: int
    scheduled_departure_date: date
    scheduled_arrival_date: date
    check_in: datetime
    check_out: datetime
    end_of_rest_after: datetime
    scheduled_departure_date_local: date
    scheduled_arrival_date_local: date
    check_in_local: datetime
    check_out_local: datetime
    end_of_rest_after_local: datetime
    routing: str
    flight_numbers: List[str]
    stopover_airports: List[str]
    consecutive_stopover_nights: List[str]
    total_on_days: int
    total_on_days_local: int
    total_rest_days: int
    total_rest_days_local: int
    duty_periods: Optional[List[DutyPeriod]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Pairing":
        data = humps.decamelize(data)

        return cls(
            id=data["pairing_id"],
            key=data["key"],
            scheduled_departure_date=date.fromisoformat(
                data["schedule_departure_date"][:10]
            ),
            scheduled_arrival_date=date.fromisoformat(
                data["scheduled_arrival_date"][:10]
            ),
            check_in=datetime.fromisoformat(data["check_in"]),
            check_out=datetime.fromisoformat(data["check_out"]),
            end_of_rest_after=datetime.fromisoformat(data["end_of_rest_after"]),
            scheduled_departure_date_local=date.fromisoformat(
                data["schedule_departure_date_local"][:10]
            ),
            scheduled_arrival_date_local=date.fromisoformat(
                data["scheduled_arrival_date_local"][:10]
            ),
            check_in_local=datetime.fromisoformat(data["check_in_local"]),
            check_out_local=datetime.fromisoformat(data["check_out_local"]),
            end_of_rest_after_local=datetime.fromisoformat(
                data["end_of_rest_after_local"]
            ),
            routing=data["routing"],
            flight_numbers=data["flight_numbers"],
            stopover_airports=data["stopover_airports"],
            consecutive_stopover_nights=data["consecutive_night_stopover"],
            total_on_days=data["total_overlapping_utc_days"],
            total_on_days_local=data["total_overlapping_local_days"],
            total_rest_days=data["number_of_rest_days"],
            total_rest_days_local=data["number_of_rest_days_local"],
        )

    @property
    def rest_periods(self) -> Optional[list[dict]]:
        if self.duty_periods is None:
            return None

        return [
            {
                "stopover": duty.components[-1].component_airport[-3:],
                "duration": next_duty.check_in - duty.check_out,
            }
            for duty, next_duty in zip(self.duty_periods, self.duty_periods[1:])
        ]

    @property
    def total_block(self) -> Optional[list[dict]]:
        if not self.duty_periods:
            return None

        return reduce(operator.add, (duty.block for duty in self.duty_periods))

    def to_dict(self):
        return dataclasses.asdict(self) | {
            "rest_periods": self.rest_periods,
            "total_block": self.total_block,
        }
