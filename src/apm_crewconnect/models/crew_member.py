from dataclasses import dataclass
from typing import Optional


@dataclass
class CrewMember:
    first_name: str
    last_name: str
    photo_thumbnail: str
    role_code: str
    dead_heading: bool
    ground_staff_on_board: bool
    phone: Optional[str] = None
    crew_code: Optional[str] = None
    commander: Optional[bool] = False
