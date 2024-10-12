from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from ..exceptions import UnhandledActivityTypeException, UnhandledAircraftTypeException
from .crew_member import CrewMember


@dataclass(kw_only=True)
class Activity:
    id: Optional[int]
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
    def title(self) -> str:
        return self.details

    @classmethod
    def from_roster(
        cls, data: dict[str, Any], force_base: bool = False
    ) -> Union["Activity", None]:
        if force_base:
            return Activity(
                id=data.get("opsLegCrewId"),
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

            if data["groundType"] == "O":
                if data["groundCode"] == "OFFHS":
                    return AbsentActivity.from_roster(data)

                return OffActivity.from_roster(data)

            if data["groundType"] == "N":
                if data["groundCode"] == "UNFIT":
                    return UnfitActivity.from_roster(data)

                return BlankFlightActivity.from_roster(data)

            if data["groundType"] == "V":
                return VacationActivity.from_roster(data)

            if data["groundType"] == "A":
                return AbsentActivity.from_roster(data)

        raise UnhandledActivityTypeException(data)


@dataclass(kw_only=True)
class GroundActivity(Activity):
    ground_code: str
    description: str

    @property
    def title(self) -> str:
        return self.ground_code

    @property
    def category(self) -> str:
        return self.ground_code[:4].upper()

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
class OffActivity(GroundActivity):
    @property
    def is_requested(self) -> bool:
        return self.ground_code == "OFFD"

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "OffActivity":
        return cls(**super().from_roster(data).__dict__)


@dataclass(kw_only=True)
class BlankFlightActivity(GroundActivity):
    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "BlankFlightActivity":
        return cls(**super().from_roster(data).__dict__)


@dataclass(kw_only=True)
class VacationActivity(GroundActivity):
    @property
    def is_on_blank(self) -> bool:
        return self.ground_code == "CPBLANC"

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "VacationActivity":
        return cls(**super().from_roster(data).__dict__)


@dataclass(kw_only=True)
class AbsentActivity(GroundActivity):
    @property
    def is_on_off(self) -> bool:
        return self.ground_code == "CPBLANC"

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "AbsentActivity":
        return cls(**super().from_roster(data).__dict__)


@dataclass(kw_only=True)
class UnfitActivity(GroundActivity):
    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "UnfitActivity":
        return cls(**super().from_roster(data).__dict__)


@dataclass(kw_only=True)
class SimulatorActivity(GroundActivity):
    block_time: timedelta

    @property
    def title(self) -> str:
        return "Sim Session: " + self.ground_code

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "SimulatorActivity":
        super_activity = GroundActivity.from_roster(data)

        return cls(
            **super_activity.__dict__
            | {
                "block_time": super_activity.end - super_activity.start,
            }
        )


@dataclass(kw_only=True)
class HotelActivity(Activity):
    hotel_name: str
    hotel_address: Optional[str] = None
    hotel_email: Optional[str] = None
    hotel_phone: Optional[str] = None

    @property
    def title(self) -> str:
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
    def title(self) -> str:
        return (
            "Deadhead: "
            + self.description
            + " "
            + self.origin_iata_code
            + "-"
            + self.destination_iata_code
        )

    @property
    def category(self) -> str:
        return "DHD"

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
    def title(self) -> str:
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
    def title(self) -> str:
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
    origin_timezone: timezone
    origin_terminal: Optional[str] = None
    destination_iata_code: str
    destination_icao_code: str
    destination_name: str
    destination_country: str
    destination_timezone: timezone
    destination_terminal: Optional[str] = None
    block_time: timedelta
    flight_duty: timedelta
    max_flight_duty: timedelta
    is_extended_flight_duty: bool
    role: str
    catering_type: str

    @property
    def title(self) -> str:
        return (
            self.flight_number
            + " "
            + self.origin_iata_code
            + "-"
            + self.destination_iata_code
        )

    @property
    def category(self) -> str:
        return "FLT"

    @property
    def aircraft_code(self) -> str:
        if self.aircraft_type == "737-800":
            return "73H"

        if self.aircraft_type == "A320neo":
            return "32N"

        raise UnhandledAircraftTypeException

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
                "origin_timezone": timezone(
                    timedelta(
                        hours=int(data["departureAirportTimeZone"][:3]),
                        minutes=int(data["departureAirportTimeZone"][-2:]),
                    )
                ),
                "origin_terminal": data.get("departureTerminal"),
                "destination_iata_code": data["arrivalAirportCode"],
                "destination_icao_code": data["arrivalAirportIcaoCode"],
                "destination_name": data["arrivalAirportName"],
                "destination_country": data["arrivalCountryName"],
                "destination_timezone": timezone(
                    timedelta(
                        hours=int(data["arrivalAirportTimeZone"][:3]),
                        minutes=int(data["arrivalAirportTimeZone"][-2:]),
                    )
                ),
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
                "role": data["flightRole"],
                "catering_type": data["flightSerieType"],
            }
        )
