"""fee_for() keeps its values and its failures when split into two components."""

import pytest

from src import normalise
from src.normalise import FLAT_FEE, fee_for

REGIONS = ("EU", "NA", "APAC", "XX")
AMOUNTS = (0, 1, -1, 9999, 10000, 10001, 10**9)

# Frozen from the single-expression fee_for() before the split: (region, amount) -> fee.
FROZEN = {
    ("EU", 0): 25, ("EU", 1): 25, ("EU", -1): 24, ("EU", 9999): 1524,
    ("EU", 10000): 1525, ("EU", 10001): 1525, ("EU", 10**9): 150000025,
    ("NA", 0): 25, ("NA", 1): 25, ("NA", -1): 24, ("NA", 9999): 524,
    ("NA", 10000): 525, ("NA", 10001): 525, ("NA", 10**9): 50000025,
    ("APAC", 0): 25, ("APAC", 1): 25, ("APAC", -1): 25, ("APAC", 9999): 25,
    ("APAC", 10000): 25, ("APAC", 10001): 25, ("APAC", 10**9): 25,
    ("XX", 0): 25, ("XX", 1): 25, ("XX", -1): 25, ("XX", 9999): 25,
    ("XX", 10000): 25, ("XX", 10001): 25, ("XX", 10**9): 25,
}


def _original(record):
    """The pre-split expression, kept verbatim as the reference."""
    return 25 + record["amount"] * {"EU": 1500, "NA": 500, "APAC": 0}.get(record["region"], 0) // 10000


def test_identity_frozen_table_covers_the_whole_grid():
    assert set(FROZEN) == {(r, a) for r in REGIONS for a in AMOUNTS}


@pytest.mark.parametrize(("region", "amount"), sorted(FROZEN))
def test_identity_value_matches_the_frozen_table(region, amount):
    assert fee_for({"amount": amount, "region": region}) == FROZEN[(region, amount)]


@pytest.mark.parametrize(("region", "amount"), sorted(FROZEN))
def test_identity_value_matches_the_original_expression(region, amount):
    record = {"amount": amount, "region": region}
    assert fee_for(record) == _original(record)


def test_identity_missing_region_raises_key_error_for_region():
    with pytest.raises(KeyError) as info:
        fee_for({"amount": 5})
    assert info.value.args == ("region",)


def test_identity_missing_amount_raises_key_error_for_amount():
    with pytest.raises(KeyError) as info:
        fee_for({"region": "EU"})
    assert info.value.args == ("amount",)


def test_identity_missing_both_raises_key_error_for_amount():
    with pytest.raises(KeyError) as info:
        fee_for({})
    assert info.value.args == ("amount",)


def test_composition_fee_is_the_sum_of_the_two_helpers(monkeypatch):
    monkeypatch.setattr(normalise, "_flat_component", lambda: 1000)
    monkeypatch.setattr(normalise, "_handling_component", lambda record: 7)
    assert fee_for({"amount": 1, "region": "EU"}) == 1007


def test_composition_flat_half_is_the_flat_fee_alone():
    assert normalise._flat_component() == FLAT_FEE == 25


@pytest.mark.parametrize(
    ("region", "amount", "expected"),
    [("EU", 10000, 1500), ("NA", 10000, 500), ("APAC", 10000, 0), ("XX", 10000, 0), ("EU", 0, 0)],
)
def test_composition_handling_half_carries_only_the_regional_part(region, amount, expected):
    assert normalise._handling_component({"amount": amount, "region": region}) == expected
