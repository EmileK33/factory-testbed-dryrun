"""Tests for the fee_for() split into its flat and handling components."""

import pytest

import src.normalise as normalise
from src.normalise import FLAT_FEE, fee_for

# Independent copy of the rate table, so a change to the real table is caught here.
ORACLE_BP = {"EU": 1500, "NA": 500, "APAC": 0}

AMOUNTS = [0, 1, 99, 100, 9999, 10000, 10001, 123456, -1, -9999]
REGIONS = ["EU", "NA", "APAC", "XX"]
GRID = [(a, r) for a in AMOUNTS for r in REGIONS]


def _original(record):
    """The expression fee_for() held before the split."""
    return 25 + record["amount"] * ORACLE_BP.get(record["region"], 0) // 10000


def test_equivalence_with_the_original_expression():
    assert len(GRID) == 40
    for amount, region in GRID:
        record = {"amount": amount, "region": region}
        assert fee_for(record) == _original(record), (amount, region)


def test_equivalence_error_contract_matches_the_original():
    for record in ({"amount": 5}, {"region": "EU"}, {}):
        with pytest.raises(KeyError) as old:
            _original(record)
        with pytest.raises(KeyError) as new:
            fee_for(record)
        assert new.value.args == old.value.args


def test_split_fee_for_is_the_sum_of_the_two_helpers(monkeypatch):
    monkeypatch.setattr(normalise, "_flat_component", lambda record: 1000)
    monkeypatch.setattr(normalise, "_handling_component", lambda record: 7)
    assert normalise.fee_for({"amount": 1, "region": "EU"}) == 1007


def test_helper_values():
    eu = {"amount": 1000, "region": "EU"}
    assert normalise._flat_component(eu) == FLAT_FEE
    assert normalise._handling_component(eu) == 150
    assert normalise._handling_component({"amount": 1000, "region": "XX"}) == 0
    assert normalise._handling_component({"amount": 99, "region": "EU"}) == 14


def test_public_names_are_unchanged():
    public = {name for name in dir(normalise) if not name.startswith("_")}
    assert public == {"FLAT_FEE", "HANDLING_BP", "apply_fees", "fee_for", "annotations"}
