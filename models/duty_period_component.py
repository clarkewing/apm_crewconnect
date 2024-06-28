from dataclasses import dataclass
from datetime import datetime, time
from typing import List, Optional
import humps


@dataclass
class DutyPeriodComponent:
    id: int
    duty_period_id: int
    departure_time: time
    arrival_time: time
    departure_time_local: time
    arrival_time_local: time
    departure_time_local_device: time
    arrival_time_local_device: time
    component_description: str
    component_airport: str
    hotac_name: Optional[str]
    key: int

    @classmethod
    def from_dict(cls, data: dict) -> "DutyPeriodComponent":
        data = humps.decamelize(data)

        return cls(
            id=data["id"],
            duty_period_id=data["duty_period_id"],
            departure_time=datetime.strptime(data["departure_time"], "%H:%M").time(),
            arrival_time=datetime.strptime(data["arrival_time"], "%H:%M").time(),
            departure_time_local=datetime.strptime(
                data["departure_time_local"], "%H:%M"
            ).time(),
            arrival_time_local=datetime.strptime(
                data["arrival_time_local"], "%H:%M"
            ).time(),
            departure_time_local_device=datetime.strptime(
                data["departure_time_local_device"], "%H:%M"
            ).time(),
            arrival_time_local_device=datetime.strptime(
                data["arrival_time_local_device"], "%H:%M"
            ).time(),
            component_description=data["component_description"],
            component_airport=data["component_airport"],
            hotac_name=data.get("hotac_name"),
            key=data["key"],
        )
