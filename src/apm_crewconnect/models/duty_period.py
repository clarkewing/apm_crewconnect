from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional
import humps

from .duty_period_component import DutyPeriodComponent


@dataclass
class DutyPeriod:
    id: int
    pairing_id: int
    key: int
    departure_date: date
    departure_date_local: date
    departure_date_local_device: date
    check_in: datetime
    check_out: datetime
    end_of_rest_after: datetime
    check_in_local: datetime
    check_out_local: datetime
    end_of_rest_after_local: datetime
    check_in_local_device: datetime
    check_out_local_device: datetime
    end_of_rest_after_local_device: datetime
    block: timedelta
    duty: timedelta
    flight_duty_period: timedelta
    maximum_flight_duty_period: timedelta
    flight: bool
    deadhead: bool
    ground: bool
    hotac: bool
    hotac_name: Optional[str]
    components: List[DutyPeriodComponent]

    @classmethod
    def from_dict(cls, data: dict) -> "DutyPeriod":
        data = humps.decamelize(data)

        departure_date = date.fromisoformat(data["departure_date"])
        departure_date_local = date.fromisoformat(data["departure_date_local"])
        departure_date_local_device = date.fromisoformat(
            data["departure_date_local_device"]
        )

        return cls(
            id=data["id"],
            pairing_id=data["pairing_id"],
            key=data["key"],
            departure_date=departure_date,
            departure_date_local=departure_date_local,
            departure_date_local_device=departure_date_local,
            check_in=datetime.combine(
                departure_date, datetime.strptime(data["check_in"], "%H:%M").time()
            ),
            check_out=datetime.combine(
                departure_date
                + timedelta(days=data["number_of_days_between_check_in_and_check_out"]),
                datetime.strptime(data["check_out"], "%H:%M").time(),
            ),
            end_of_rest_after=datetime.combine(
                departure_date
                + timedelta(
                    days=data["number_of_days_between_check_in_and_end_of_rest"]
                ),
                datetime.strptime(data["end_of_rest_after"], "%H:%M").time(),
            ),
            check_in_local=datetime.combine(
                departure_date_local,
                datetime.strptime(data["check_in_local"], "%H:%M").time(),
            ),
            check_out_local=datetime.combine(
                departure_date_local
                + timedelta(
                    days=data["number_of_days_between_check_in_and_check_out_local"]
                ),
                datetime.strptime(data["check_out_local"], "%H:%M").time(),
            ),
            end_of_rest_after_local=datetime.combine(
                departure_date_local
                + timedelta(
                    days=data["number_of_days_between_check_in_and_end_of_rest_local"]
                ),
                datetime.strptime(data["end_of_rest_after_local"], "%H:%M").time(),
            ),
            check_in_local_device=datetime.combine(
                departure_date_local_device,
                datetime.strptime(data["check_in_local_device"], "%H:%M").time(),
            ),
            check_out_local_device=datetime.combine(
                departure_date_local_device
                + timedelta(
                    days=data[
                        "number_of_days_between_check_in_and_check_out_local_device"
                    ]
                ),
                datetime.strptime(data["check_out_local_device"], "%H:%M").time(),
            ),
            end_of_rest_after_local_device=datetime.combine(
                departure_date_local_device
                + timedelta(
                    days=data[
                        "number_of_days_between_check_in_and_end_of_rest_local_device"
                    ]
                ),
                datetime.strptime(
                    data["end_of_rest_after_local_device"], "%H:%M"
                ).time(),
            ),
            block=timedelta(
                hours=int(data["block"][:2]),
                minutes=int(data["block"][-2:]),
            ),
            duty=timedelta(
                hours=int(data["duty"][:2]),
                minutes=int(data["duty"][-2:]),
            ),
            flight_duty_period=timedelta(
                hours=int(data["flight_duty_period"][:2]),
                minutes=int(data["flight_duty_period"][-2:]),
            ),
            maximum_flight_duty_period=timedelta(
                hours=int(data["maximum_flight_duty_period"][:2]),
                minutes=int(data["maximum_flight_duty_period"][-2:]),
            ),
            flight=bool(data.get("flight")),
            deadhead=bool(data.get("deadhead")),
            ground=bool(data.get("ground")),
            hotac=bool(data.get("hotac")),
            hotac_name=data.get("hotac_name"),
            components=[
                DutyPeriodComponent.from_dict(item)
                for item in data["duty_period_components"]
            ],
        )
