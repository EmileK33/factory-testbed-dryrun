"""Differential tests for the fee_for() split into flat and handling components."""

import pytest

from src import normalise
from src.normalise import fee_for

AMOUNTS = [-100000, -10001, -10000, -9999, -1, 0, 1, 9, 10, 9999, 10000, 10001, 123457, 10**9]
REGIONS = ["EU", "NA", "APAC", "XX", "", "eu"]


def _old_fee_for(record):
    # Frozen copy of the pre-split single expression.
    return 25 + record["amount"] * {"EU": 1500, "NA": 500, "APAC": 0}.get(record["region"], 0) // 10000


@pytest.mark.parametrize("region", REGIONS)
@pytest.mark.parametrize("amount", AMOUNTS)
def test_fee_for_matches_the_old_expression(amount, region):
    record = {"id": "R", "amount": amount, "region": region}
    assert fee_for(record) == _old_fee_for(record)


def test_flat_component_is_the_flat_fee_for_any_record():
    assert normalise._flat_component({"amount": 5000, "region": "EU"}) == 25
    assert normalise._flat_component({"amount": -7, "region": "XX"}) == 25


def test_handling_component_is_the_regional_charge_only():
    assert normalise._handling_component({"amount": 1000, "region": "EU"}) == 150
    assert normalise._handling_component({"amount": 1000, "region": "APAC"}) == 0
    assert normalise._handling_component({"amount": 1000, "region": "XX"}) == 0


def test_handling_component_floors_negative_amounts():
    assert normalise._handling_component({"amount": -1, "region": "NA"}) == -1


def test_fee_for_is_the_sum_of_the_components():
    record = {"amount": 2000, "region": "NA"}
    assert fee_for(record) == normalise._flat_component(record) + normalise._handling_component(record)
