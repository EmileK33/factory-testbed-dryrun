"""Tests for fee application.

Conversion and counting used to live here too. They were split out into
``test_conversion.py`` and ``test_counts.py`` because each is coupled to a
different committed data file, and holding both in one file forced any two items
touching different data to edit the same test — see this repository's TESTING.md
routing table.
"""

import pytest

from src.normalise import _flat_component, _handling_component, apply_fees, fee_for


def test_apply_fees_rejects_a_negative_gross_amount():
    with pytest.raises(ValueError):
        apply_fees([{"id": "R-9", "amount": -1, "region": "NA"}])


def test_apply_fees_charges_the_regional_handling_rate():
    [row] = apply_fees([{"id": "R-9", "amount": 1000, "region": "EU"}])
    assert row["net"] == 1000 - (25 + 150)


@pytest.mark.parametrize(
    ("region", "amount", "fee"),
    [
        ("EU", 1000, 175),
        ("EU", 10000, 1525),
        ("EU", 7, 26),
        ("EU", 0, 25),
        ("EU", -1, 24),
        ("NA", 999, 74),
        ("APAC", 10000, 25),
        ("XX", 10000, 25),
    ],
)
def test_fee_for_is_the_flat_fee_plus_the_floored_handling_charge(region, amount, fee):
    assert fee_for({"region": region, "amount": amount}) == fee


@pytest.mark.parametrize("region", ["EU", "NA", "APAC", "XX"])
def test_the_flat_component_is_the_flat_fee_alone(region):
    assert _flat_component({"region": region, "amount": 10000}) == 25


@pytest.mark.parametrize(
    ("region", "amount", "handling"),
    [
        ("EU", 1000, 150),
        ("EU", 10000, 1500),
        ("NA", 999, 49),
        ("APAC", 10000, 0),
        ("XX", 10000, 0),
        ("EU", -1, -1),
    ],
)
def test_the_handling_component_is_the_floored_regional_charge_alone(region, amount, handling):
    assert _handling_component({"region": region, "amount": amount}) == handling
