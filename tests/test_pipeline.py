"""Tests for fee application.

Conversion and counting used to live here too. They were split out into
``test_conversion.py`` and ``test_counts.py`` because each is coupled to a
different committed data file, and holding both in one file forced any two items
touching different data to edit the same test — see this repository's TESTING.md
routing table.
"""

import pytest

from src import normalise
from src.normalise import apply_fees


def test_apply_fees_rejects_a_negative_gross_amount():
    with pytest.raises(ValueError):
        apply_fees([{"id": "R-9", "amount": -1, "region": "NA"}])


def test_apply_fees_charges_the_regional_handling_rate():
    [row] = apply_fees([{"id": "R-9", "amount": 1000, "region": "EU"}])
    assert row["net"] == 1000 - (25 + 150)


def _legacy_fee(record):
    # The pre-refactor expression, written out literally as the oracle.
    return normalise.FLAT_FEE + record["amount"] * normalise.HANDLING_BP.get(record["region"], 0) // 10000


_GRID_AMOUNTS = [-19, -1, 0, 1, 9, 10, 19, 20, 99, 100, 1000, 1999, 9999, 123457, 10**9]
_GRID_REGIONS = ["EU", "NA", "APAC", "LATAM", ""]


@pytest.mark.parametrize("region", _GRID_REGIONS)
@pytest.mark.parametrize("amount", _GRID_AMOUNTS)
def test_fee_for_matches_the_pre_refactor_expression(amount, region):
    record = {"id": "R-1", "amount": amount, "region": region}
    assert normalise.fee_for(record) == _legacy_fee(record)


def test_flat_component_is_the_flat_fee():
    assert normalise._flat_component() == 25


def test_handling_component_floors_the_product_and_defaults_unknown_regions_to_zero():
    assert normalise._handling_component({"amount": 1000, "region": "EU"}) == 150
    assert normalise._handling_component({"amount": 1999, "region": "NA"}) == 99
    assert normalise._handling_component({"amount": 1000, "region": "LATAM"}) == 0


def test_fee_for_is_the_sum_of_its_components(monkeypatch):
    monkeypatch.setattr(normalise, "_flat_component", lambda: 1000)
    monkeypatch.setattr(normalise, "_handling_component", lambda record: 2000)
    assert normalise.fee_for({"amount": 0, "region": "EU"}) == 3000
