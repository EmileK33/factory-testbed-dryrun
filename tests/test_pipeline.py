"""Tests for fee application.

Conversion and counting used to live here too. They were split out into
``test_conversion.py`` and ``test_counts.py`` because each is coupled to a
different committed data file, and holding both in one file forced any two items
touching different data to edit the same test — see this repository's TESTING.md
routing table.
"""

import pytest

from src import normalise
from src.normalise import apply_fees, fee_for

AMOUNTS = [0, 1, 99, 100, 1000, 10**9, -1, -99, -1000]
REGIONS = ["EU", "NA", "APAC", "XX"]
GRID = [{"id": "R-0", "amount": a, "region": r} for a in AMOUNTS for r in REGIONS]
ORIGINAL_BP = {"EU": 1500, "NA": 500, "APAC": 0}


def _original_fee(record):
    """The expression fee_for used before it was split, kept verbatim."""
    return 25 + record["amount"] * ORIGINAL_BP.get(record["region"], 0) // 10000


def test_fee_for_matches_the_original_expression():
    assert len(GRID) == 36
    for record in GRID:
        assert fee_for(record) == _original_fee(record), record


def test_fee_for_is_the_sum_of_its_components():
    assert len(GRID) == 36
    for record in GRID:
        flat = normalise._flat_component(record)
        handling = normalise._handling_component(record)
        assert flat == normalise.FLAT_FEE
        assert fee_for(record) == flat + handling, record


def test_public_names_are_unchanged():
    for name in ("FLAT_FEE", "HANDLING_BP", "fee_for", "apply_fees"):
        assert hasattr(normalise, name), name
    for name in ("_flat_component", "_handling_component"):
        assert callable(getattr(normalise, name)), name


def test_apply_fees_rejects_a_negative_gross_amount():
    with pytest.raises(ValueError):
        apply_fees([{"id": "R-9", "amount": -1, "region": "NA"}])


def test_apply_fees_charges_the_regional_handling_rate():
    [row] = apply_fees([{"id": "R-9", "amount": 1000, "region": "EU"}])
    assert row["net"] == 1000 - (25 + 150)
