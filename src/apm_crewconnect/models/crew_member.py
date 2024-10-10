from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CrewMember:
    first_name: str
    last_name: str
    photo_thumbnail: str
    dead_heading: bool
    ground_staff_on_board: bool
    role_code: Optional[str] = None
    phone: Optional[str] = None
    crew_code: Optional[str] = None
    commander: Optional[bool] = False

    @classmethod
    def from_roster(cls, data: dict[str, Any]) -> "CrewMember":
        return cls(
            crew_code=data["crewCode"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            photo_thumbnail=data["photoThumbnail"],
            role_code=data["contractRoles"],
            phone=data.get("firstPhoneNumber", None),
            commander=data["commander"],
            dead_heading=False,
            ground_staff_on_board=False,
        )
