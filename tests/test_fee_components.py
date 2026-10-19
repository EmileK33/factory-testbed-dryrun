"""Characterisation of ``fee_for()`` and its two components.

The expected fees are frozen literals (taken from the pre-split implementation),
not recomputed from the formula, so a change in rounding shows up here.
"""

import pytest

from src.normalise import _flat_component, _handling_component, fee_for

CASES = [
    (-10001, 'EU', -1476),
    (-10001, 'NA', -476),
    (-10001, 'APAC', 25),
    (-10001, 'MARS', 25),
    (-10001, '', 25),
    (-10000, 'EU', -1475),
    (-10000, 'NA', -475),
    (-10000, 'APAC', 25),
    (-10000, 'MARS', 25),
    (-10000, '', 25),
    (-9999, 'EU', -1475),
    (-9999, 'NA', -475),
    (-9999, 'APAC', 25),
    (-9999, 'MARS', 25),
    (-9999, '', 25),
    (-1, 'EU', 24),
    (-1, 'NA', 24),
    (-1, 'APAC', 25),
    (-1, 'MARS', 25),
    (-1, '', 25),
    (0, 'EU', 25),
    (0, 'NA', 25),
    (0, 'APAC', 25),
    (0, 'MARS', 25),
    (0, '', 25),
    (1, 'EU', 25),
    (1, 'NA', 25),
    (1, 'APAC', 25),
    (1, 'MARS', 25),
    (1, '', 25),
    (19, 'EU', 27),
    (19, 'NA', 25),
    (19, 'APAC', 25),
    (19, 'MARS', 25),
    (19, '', 25),
    (20, 'EU', 28),
    (20, 'NA', 26),
    (20, 'APAC', 25),
    (20, 'MARS', 25),
    (20, '', 25),
    (21, 'EU', 28),
    (21, 'NA', 26),
    (21, 'APAC', 25),
    (21, 'MARS', 25),
    (21, '', 25),
    (199, 'EU', 54),
    (199, 'NA', 34),
    (199, 'APAC', 25),
    (199, 'MARS', 25),
    (199, '', 25),
    (200, 'EU', 55),
    (200, 'NA', 35),
    (200, 'APAC', 25),
    (200, 'MARS', 25),
    (200, '', 25),
    (201, 'EU', 55),
    (201, 'NA', 35),
    (201, 'APAC', 25),
    (201, 'MARS', 25),
    (201, '', 25),
    (999, 'EU', 174),
    (999, 'NA', 74),
    (999, 'APAC', 25),
    (999, 'MARS', 25),
    (999, '', 25),
    (1000, 'EU', 175),
    (1000, 'NA', 75),
    (1000, 'APAC', 25),
    (1000, 'MARS', 25),
    (1000, '', 25),
    (9999, 'EU', 1524),
    (9999, 'NA', 524),
    (9999, 'APAC', 25),
    (9999, 'MARS', 25),
    (9999, '', 25),
    (10000, 'EU', 1525),
    (10000, 'NA', 525),
    (10000, 'APAC', 25),
    (10000, 'MARS', 25),
    (10000, '', 25),
    (10001, 'EU', 1525),
    (10001, 'NA', 525),
    (10001, 'APAC', 25),
    (10001, 'MARS', 25),
    (10001, '', 25),
    (123457, 'EU', 18543),
    (123457, 'NA', 6197),
    (123457, 'APAC', 25),
    (123457, 'MARS', 25),
    (123457, '', 25),
    (1000000000007, 'EU', 150000000026),
    (1000000000007, 'NA', 50000000025),
    (1000000000007, 'APAC', 25),
    (1000000000007, 'MARS', 25),
    (1000000000007, '', 25),
]


@pytest.mark.parametrize(("amount", "region", "fee"), CASES)
def test_fee_for_is_unchanged(amount, region, fee):
    assert fee_for({"amount": amount, "region": region}) == fee


@pytest.mark.parametrize(("amount", "region", "fee"), CASES)
def test_fee_for_is_the_sum_of_its_components(amount, region, fee):
    record = {"amount": amount, "region": region}
    assert _flat_component(record) == 25
    assert _flat_component(record) + _handling_component(record) == fee


@pytest.mark.parametrize("record", [{"amount": 5}, {"region": "EU"}, {}])
def test_fee_for_still_requires_both_keys(record):
    with pytest.raises(KeyError):
        fee_for(record)
