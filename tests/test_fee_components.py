"""The fee is its flat and handling components, with the old rounding preserved."""

import itertools

import pytest

from src.normalise import _flat_component, _handling_component, fee_for

AMOUNTS = [-100000, -10001, -10000, -9999, -1, 0, 1, 9999, 10000, 10001, 123457, 2**40]
REGIONS = ["EU", "NA", "APAC", "XX", ""]


def _old_expression(record):
    # literal copy of the pre-split single expression
    return 25 + record["amount"] * {"EU": 1500, "NA": 500, "APAC": 0}.get(record["region"], 0) // 10000


@pytest.mark.parametrize("amount,region", list(itertools.product(AMOUNTS, REGIONS)))
def test_fee_for_equals_the_pre_split_expression(amount, region):
    record = {"amount": amount, "region": region}
    assert fee_for(record) == _old_expression(record)


@pytest.mark.parametrize("amount,region", list(itertools.product(AMOUNTS, REGIONS)))
def test_fee_for_is_the_sum_of_its_components(amount, region):
    record = {"amount": amount, "region": region}
    assert fee_for(record) == _flat_component(record) + _handling_component(record)


def test_handling_rounds_toward_minus_infinity():
    assert _handling_component({"amount": -1, "region": "NA"}) == -1
    assert fee_for({"amount": -1, "region": "NA"}) == 24


def test_handling_is_floored_for_positive_amounts():
    assert _handling_component({"amount": 19, "region": "NA"}) == 0
    assert _handling_component({"amount": 20, "region": "NA"}) == 1


def test_unknown_region_has_no_handling_charge():
    assert _handling_component({"amount": 5000, "region": "XX"}) == 0
    assert _flat_component({"amount": 5000, "region": "XX"}) == 25
