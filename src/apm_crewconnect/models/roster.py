from dataclasses import dataclass
from datetime import date

from .activity import Activity


@dataclass
class Roster:
    user_id: str
    start: date
    end: date
    activities: list[Activity]
