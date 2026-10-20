"""Tests for fee application.

Conversion and counting used to live here too. They were split out into
``test_conversion.py`` and ``test_counts.py`` because each is coupled to a
different committed data file, and holding both in one file forced any two items
touching different data to edit the same test — see this repository's TESTING.md
routing table.
"""

import pytest

from src.normalise import (
    FLAT_FEE,
    _flat_component,
    _handling_component,
    apply_fees,
    fee_for,
)

AMOUNTS = (0, 1, 99, 100, 101, 1000, 9999, 10**9, -1, -101)
REGIONS = ("EU", "NA", "APAC", "unknown")


def _original_fee(record):
    """The one-line expression fee_for() held before it was split, frozen."""
    bp = {"EU": 1500, "NA": 500, "APAC": 0}
    return 25 + record["amount"] * bp.get(record["region"], 0) // 10000


def test_apply_fees_rejects_a_negative_gross_amount():
    with pytest.raises(ValueError):
        apply_fees([{"id": "R-9", "amount": -1, "region": "NA"}])


def test_apply_fees_charges_the_regional_handling_rate():
    [row] = apply_fees([{"id": "R-9", "amount": 1000, "region": "EU"}])
    assert row["net"] == 1000 - (25 + 150)


def test_fee_for_matches_original_expression_on_every_amount_and_region():
    for amount in AMOUNTS:
        for region in REGIONS:
            record = {"amount": amount, "region": region}
            assert fee_for(record) == _original_fee(record), (amount, region)


def test_fee_for_without_a_region_still_raises_key_error():
    with pytest.raises(KeyError):
        fee_for({"amount": 1})


def test_flat_component_ignores_region_and_amount():
    assert _flat_component({"amount": 999999, "region": "unknown"}) == FLAT_FEE
    assert _flat_component({"amount": -5, "region": "EU"}) == FLAT_FEE


def test_handling_component_is_basis_points_of_the_amount():
    assert _handling_component({"amount": 1000, "region": "EU"}) == 150
    assert _handling_component({"amount": 1000, "region": "NA"}) == 50
    assert _handling_component({"amount": 1000, "region": "APAC"}) == 0
    assert _handling_component({"amount": 1000, "region": "unknown"}) == 0
    assert _handling_component({"amount": 99, "region": "EU"}) == 14


def test_fee_for_is_sum_of_components():
    for amount in AMOUNTS:
        for region in REGIONS:
            record = {"amount": amount, "region": region}
            assert fee_for(record) == _flat_component(record) + _handling_component(record)
