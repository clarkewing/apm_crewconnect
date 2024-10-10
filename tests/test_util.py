"""Test SDK util methods."""

import sys

import pytest

sys.path.append("./src")

from datetime import date
from apm_crewconnect import utils


def test_date_range() -> None:
    """Test date_range."""
    assert utils.date_range(date(2024, 7, 19), date(2024, 7, 22)) == [
        date(2024, 7, 19),
        date(2024, 7, 20),
        date(2024, 7, 21),
        date(2024, 7, 22),
    ]

    with pytest.raises(ValueError):
        utils.date_range(date(2024, 7, 22), date(2024, 7, 19))
