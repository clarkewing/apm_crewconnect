from dataclasses import dataclass


@dataclass
class FlightTimes:
    departure_estimated: bool
    arrival_estimated: bool
