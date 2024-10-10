from dataclasses import dataclass
from datetime import date

from .activity import Activity


@dataclass
class Roster:
    start: date
    end: date
    activities: list[Activity]

    
