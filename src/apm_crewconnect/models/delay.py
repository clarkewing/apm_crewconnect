from dataclasses import dataclass
from typing import Optional


@dataclass
class Delay:
    delay_minutes: int
    delay_code: Optional[str] = None
    delay_reason: Optional[str] = None
