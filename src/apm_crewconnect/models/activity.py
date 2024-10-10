from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from ..exceptions import UnknownActivityTypeException
from .crew_member import CrewMember


@dataclass(kw_only=True)
class Activity:
    id: int
    pairing_id: Optional[int]
    is_pending: bool
    details: str
    remarks: Optional[str] = None
    start: datetime
    end: datetime
    check_in: datetime
    check_out: datetime
    pre_rest_start: datetime
    post_rest_end: datetime
    crew_members: list[CrewMember]

    @property
    def title(self):
        return self.details

    @classmethod
    def from_roster(
        cls, data: dict[str, Any], force_base: bool = False
    ) -> Union["Activity", None]:
        if force_base:
            return Activity(
                id=data["opsLegCrewId"],
                pairing_id=data.get("crewPairingId"),
                is_pending=data["pendingRequest"],
                details=data["details"],
                remarks=data.get("remarks"),
                start=datetime.fromisoformat(data["start"]),
                end=datetime.fromisoformat(data["end"]),
                check_in=datetime.fromisoformat(data["checkIn"]),
                check_out=datetime.fromisoformat(data["checkOut"]),
                pre_rest_start=datetime.fromisoformat(data["restBefore"]),
                post_rest_end=datetime.fromisoformat(data["restAfter"]),
                crew_members=[
                    CrewMember.from_roster(crew_data) for crew_data in data["crews"]
                ],
            )

        if data["activityType"] == "F":
            return FlightActivity.from_roster(data)

        if data["activityType"] == "S":
            return ShuttleActivity.from_roster(data)

        if data["activityType"] == "T":
            return TrainActivity.from_roster(data)

        if data["activityType"] == "O":
            return DeadheadActivity.from_roster(data)

        if data["activityType"] == "H":
            return HotelActivity.from_roster(data)

        if data["activityType"] == "G":
            if data["groundType"] == "G":
                return GroundActivity.from_roster(data)

            if data["groundType"] == "S":
                return SimulatorActivity.from_roster(data)

            if data["groundType"] == "O":  # Off
                return None

            if data["groundType"] == "N":  # BlancVol
                return None

            if data["groundType"] == "V":  # Vacation
                return None

            if data["groundType"] == "A":  # HS
                return None

        raise UnknownActivityTypeException(data)


@dataclass(kw_only=True)
class GroundActivity(Activity):
    ground_code: str
    description: str

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "GroundActivity":
        return cls(
            **super().from_roster(data, force_base=True).__dict__
            | {
                "ground_code": data["groundCode"],
                "description": data["description"],
            }
        )


@dataclass(kw_only=True)
class SimulatorActivity(GroundActivity):
    @property
    def title(self):
        return "Sim Session: " + self.ground_code

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "SimulatorActivity":
        return cls(**super().from_roster(data).__dict__)


@dataclass(kw_only=True)
class HotelActivity(Activity):
    hotel_name: str
    hotel_address: Optional[str] = None
    hotel_email: Optional[str] = None
    hotel_phone: Optional[str] = None

    @property
    def title(self):
        return "Hotel: " + self.hotel_name

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "HotelActivity":
        return cls(
            **super().from_roster(data, force_base=True).__dict__
            | {
                "hotel_name": data["hotelName"],
                "hotel_address": data.get("hotelAddress"),
                "hotel_email": data.get("hotelEmail"),
                "hotel_phone": data.get("hotelPhoneNumber"),
            }
        )


@dataclass(kw_only=True)
class DeadheadActivity(Activity):
    description: str
    origin_iata_code: str
    origin_icao_code: Optional[str] = None
    origin_name: str
    origin_country: str
    origin_terminal: Optional[str] = None
    destination_iata_code: str
    destination_icao_code: Optional[str] = None
    destination_name: str
    destination_country: str
    destination_terminal: Optional[str] = None
    duration: timedelta

    @property
    def title(self):
        return (
            "Deadhead: "
            + self.description
            + " "
            + self.origin_iata_code
            + "-"
            + self.destination_iata_code
        )

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "DeadheadActivity":
        return cls(
            **super().from_roster(data, force_base=True).__dict__
            | {
                "description": data["deadheadDescription"],
                "origin_iata_code": data["departureAirportCode"],
                "origin_icao_code": data.get("departureAirportIcaoCode"),
                "origin_name": data["departureAirportName"],
                "origin_country": data["departureCountryName"],
                "origin_terminal": data.get("departureTerminal"),
                "destination_iata_code": data["arrivalAirportCode"],
                "destination_icao_code": data.get("arrivalAirportIcaoCode"),
                "destination_name": data["arrivalAirportName"],
                "destination_country": data["arrivalCountryName"],
                "destination_terminal": data.get("arrivalTerminal"),
                "duration": timedelta(
                    hours=int(data["duration"][:2]),
                    minutes=int(data["duration"][3:5]),
                    seconds=int(data["duration"][-2:]),
                ),
            }
        )


@dataclass(kw_only=True)
class ShuttleActivity(DeadheadActivity):
    @property
    def title(self):
        return (
            "Shuttle: "
            + self.description
            + " "
            + self.origin_iata_code
            + "-"
            + self.destination_iata_code
        )

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "ShuttleActivity":
        return cls(**super().from_roster(data).__dict__)


@dataclass(kw_only=True)
class TrainActivity(DeadheadActivity):
    @property
    def title(self):
        return (
            "Train: "
            + self.description
            + " "
            + self.origin_iata_code
            + "-"
            + self.destination_iata_code
        )

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "TrainActivity":
        return cls(**super().from_roster(data).__dict__)


@dataclass(kw_only=True)
class FlightActivity(Activity):
    flight_number: str
    aircraft_type: str
    aircraft_registration: str
    origin_iata_code: str
    origin_icao_code: str
    origin_name: str
    origin_country: str
    origin_terminal: Optional[str] = None
    destination_iata_code: str
    destination_icao_code: str
    destination_name: str
    destination_country: str
    destination_terminal: Optional[str] = None
    block_time: timedelta
    flight_duty: timedelta
    max_flight_duty: timedelta
    is_extended_flight_duty: bool
    catering_type: str

    @property
    def title(self):
        return (
            self.flight_number
            + " "
            + self.origin_iata_code
            + "-"
            + self.destination_iata_code
        )

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "FlightActivity":
        return cls(
            **super().from_roster(data, force_base=True).__dict__
            | {
                "flight_number": data["flightNumber"],
                "aircraft_type": data["flightAircraftVersion"],
                "aircraft_registration": data["flightAircraftRegistration"],
                "origin_iata_code": data["departureAirportCode"],
                "origin_icao_code": data["departureAirportIcaoCode"],
                "origin_name": data["departureAirportName"],
                "origin_country": data["departureCountryName"],
                "origin_terminal": data.get("departureTerminal"),
                "destination_iata_code": data["arrivalAirportCode"],
                "destination_icao_code": data["arrivalAirportIcaoCode"],
                "destination_name": data["arrivalAirportName"],
                "destination_country": data["arrivalCountryName"],
                "destination_terminal": data.get("arrivalTerminal"),
                "block_time": timedelta(
                    hours=int(data["flightBlockTime"][:2]),
                    minutes=int(data["flightBlockTime"][-2:]),
                ),
                "flight_duty": timedelta(
                    hours=int(data["flightDutyPeriod"][:2]),
                    minutes=int(data["flightDutyPeriod"][3:5]),
                    seconds=int(data["flightDutyPeriod"][-2:]),
                ),
                "max_flight_duty": timedelta(
                    hours=int(data["maxFlightDutyPeriod"][:2]),
                    minutes=int(data["maxFlightDutyPeriod"][3:5]),
                    seconds=int(data["maxFlightDutyPeriod"][-2:]),
                ),
                "is_extended_flight_duty": data["flightDutyType"] != "Standard",
                "catering_type": data["flightSerieType"],
            }
        )
