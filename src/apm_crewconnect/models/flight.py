from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import humps

from ..exceptions import UnhandledAircraftTypeException
from .crew_member import CrewMember
from .delay import Delay
from .flight_times import FlightTimes
from .freight_info import FreightInfo
from .passenger_info import PassengerInfo


@dataclass
class Flight:
    leg_id: int
    serie_id: int
    aircraft_registration: str
    aircraft_code: str
    aircraft_type: str
    commercial_flight_number: str
    airline_designator: str
    flight_number: str
    departure_airport_commercial_code: str
    departure_airport_name: str
    arrival_airport_commercial_code: str
    arrival_airport_name: str
    departure_time: datetime
    arrival_time: datetime
    scheduled_departure_time: datetime
    scheduled_arrival_time: datetime
    number_of_passengers: int
    number_of_infants: int
    passenger_info: PassengerInfo
    freight_info: FreightInfo
    flight_times: FlightTimes
    departure_color: str
    arrival_color: str
    delays: List[Delay]
    block_time: str
    crew_members: List[CrewMember]
    icao_departure_airport: str
    icao_arrival_airport: str
    departure_hatched: bool
    arrival_hatched: bool
    pax_overbooking: bool
    pax_underbooking: bool
    _links: Dict[str, Dict[str, str]]
    pax_type: Optional[str] = None
    departure_terminal_code: Optional[str] = None
    arrival_terminal_code: Optional[str] = None
    atc_designator: Optional[str] = None
    atc_flight_number: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Flight":
        data = humps.decamelize(data)

        passenger_info = PassengerInfo(**data["passenger_info_dto"])
        freight_info = FreightInfo(**data["freight_info_dto"])
        flight_times = FlightTimes(
            departure_estimated=data["flight_times"]["departure_estimated"],
            arrival_estimated=data["flight_times"]["arrival_estimated"],
            block_out=(
                datetime.fromisoformat(data["flight_times"]["out"])
                if "out" in data["flight_times"]
                else None
            ),
            block_off=(
                datetime.fromisoformat(data["flight_times"]["off"])
                if "off" in data["flight_times"]
                else None
            ),
            block_on=(
                datetime.fromisoformat(data["flight_times"]["on"])
                if "on" in data["flight_times"]
                else None
            ),
            block_in=(
                datetime.fromisoformat(data["flight_times"]["in"])
                if "in" in data["flight_times"]
                else None
            ),
        )
        delays = [Delay(**delay) for delay in data["delays"]]
        crew_members = [CrewMember(**member) for member in data["crew_members"]]

        return cls(
            leg_id=data["leg_id"],
            serie_id=data["serie_id"],
            aircraft_registration=data["aircraft_registration"],
            aircraft_code=data["aircraft_code"],
            aircraft_type=data["aircraft_type"],
            commercial_flight_number=data["commercial_flight_number"],
            airline_designator=data["airline_designator"],
            flight_number=data["flight_number"],
            atc_designator=data.get("atc_designator", None),
            atc_flight_number=data.get("atc_flight_number", None),
            departure_airport_commercial_code=data["departure_airport_commercial_code"],
            departure_airport_name=data["departure_airport_name"],
            departure_terminal_code=data.get("departure_terminal_code", None),
            arrival_airport_commercial_code=data["arrival_airport_commercial_code"],
            arrival_airport_name=data["arrival_airport_name"],
            arrival_terminal_code=data.get("arrival_terminal_code", None),
            departure_time=datetime.fromisoformat(data["departure_time"]),
            arrival_time=datetime.fromisoformat(data["arrival_time"]),
            scheduled_departure_time=datetime.fromisoformat(
                data["scheduled_departure_time"]
            ),
            scheduled_arrival_time=datetime.fromisoformat(
                data["scheduled_arrival_time"]
            ),
            pax_type=data.get("pax_type", None),
            number_of_passengers=data["number_of_passengers"],
            number_of_infants=data["number_of_infants"],
            passenger_info=passenger_info,
            freight_info=freight_info,
            flight_times=flight_times,
            departure_color=data["departure_color"],
            arrival_color=data["arrival_color"],
            delays=delays,
            block_time=data["block_time"],
            crew_members=crew_members,
            icao_departure_airport=data["icao_departure_airport"],
            icao_arrival_airport=data["icao_arrival_airport"],
            departure_hatched=data["departure_hatched"],
            arrival_hatched=data["arrival_hatched"],
            pax_overbooking=data["pax_overbooking"],
            pax_underbooking=data["pax_underbooking"],
            _links=data["_links"],
        )

    def is_missing_crew_members(self, role: str | None = None) -> bool:
        required_crew_members = self.required_crew_members()

        # Create role_counts dictionary using dictionary comprehension
        role_counts = {
            role: sum(
                crew_member.role_code == role for crew_member in self.crew_members
            )
            for role in required_crew_members
        }

        # If a specific role is provided, check only that role
        if role:
            if not role in required_crew_members:
                raise ValueError(f"Role '{role}' is not recognized.")

            # Handle the specific case where an OPL isn't required
            # if the flight has both an IPL and a CDB.
            if role == "OPL" and role_counts["IPL"] > 0 and role_counts["CDB"] > 0:
                return False

            return role_counts[role] < required_crew_members[role]

        # Otherwise, check all roles
        return any(
            role_counts[role] < required_crew_members[role]
            for role in required_crew_members
        )

    def required_crew_members(self):
        match self.aircraft_type:
            case "73H" | "32N":
                return {
                    "IPL": 0,
                    "CDB": 1,
                    "OPL": 1,
                    "SUPT": 0,
                    "INS": 0,
                    "CC": 1,
                    "CA": 3,
                    "SUPC": 0,
                    "SOL": 0,
                }

            case _:
                raise UnhandledAircraftTypeException(
                    f"Unhandled aircraft type: {self.aircraft_type}"
                )
