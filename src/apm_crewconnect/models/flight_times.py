from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FlightTimes:
    departure_estimated: bool
    arrival_estimated: bool
    block_out: Optional[datetime] = None
    block_off: Optional[datetime] = None
    block_on: Optional[datetime] = None
    block_in: Optional[datetime] = None
