"""The fee is the sum of a flat component and a regional handling component."""

import pytest

from src.normalise import (
    FLAT_FEE,
    HANDLING_BP,
    _flat_component,
    _handling_component,
    fee_for,
)


def test_flat_component_is_the_flat_fee_in_every_region():
    for region in (*HANDLING_BP, "XX"):
        assert _flat_component({"amount": 1000, "region": region}) == FLAT_FEE


def test_handling_component_applies_the_regional_basis_points():
    assert _handling_component({"amount": 1000, "region": "EU"}) == 150
    assert _handling_component({"amount": 1000, "region": "NA"}) == 50
    assert _handling_component({"amount": 1000, "region": "APAC"}) == 0


def test_handling_component_floors_rather_than_rounds():
    assert _handling_component({"amount": 1, "region": "EU"}) == 0
    assert _handling_component({"amount": 7, "region": "EU"}) == 1
    assert _handling_component({"amount": -1, "region": "EU"}) == -1


def test_unknown_region_has_no_handling_charge():
    assert _handling_component({"amount": 1000, "region": "XX"}) == 0
    assert fee_for({"amount": 1000, "region": "XX"}) == FLAT_FEE


def test_handling_component_does_not_include_the_flat_fee():
    assert _handling_component({"amount": 0, "region": "EU"}) == 0


@pytest.mark.parametrize("amount", [0, 1, 7, 333, 1000, 99999, 10**9 + 7])
@pytest.mark.parametrize("region", ["EU", "NA", "APAC", "XX"])
def test_fee_for_is_the_sum_of_its_components(amount, region):
    record = {"amount": amount, "region": region}
    assert fee_for(record) == _flat_component(record) + _handling_component(record)
    assert fee_for(record) == FLAT_FEE + amount * HANDLING_BP.get(region, 0) // 10000
