from dataclasses import dataclass
from typing import Optional


@dataclass
class PassengerInfo:
    total_pax_from_mvt: Optional[int] = None
    expected_pax_f: Optional[int] = None
    expected_pax_c: Optional[int] = None
    expected_pax_w: Optional[int] = None
    expected_pax_y: Optional[int] = None
    expected_pax_infant: Optional[int] = None
    expected_pax_pad: Optional[int] = None
    pax_f: Optional[int] = None
    pax_c: Optional[int] = None
    pax_w: Optional[int] = None
    pax_y: Optional[int] = None
    pax_pad: Optional[int] = None
    pax_male: Optional[int] = None
    pax_female: Optional[int] = None
    pax_infant: Optional[int] = None
    booked_pax_f: Optional[int] = None
    booked_pax_c: Optional[int] = None
    booked_pax_w: Optional[int] = None
    booked_pax_y: Optional[int] = None
    booked_pax_infant: Optional[int] = None
    booked_pax_pad: Optional[int] = None
    pax_adults: Optional[int] = None
    pax_children: Optional[int] = None
