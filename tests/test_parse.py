"""Tests for the packed-column helpers."""

import pytest

from src.parse import parse_tags


def test_parse_tags_splits_a_plain_list():
    assert parse_tags("na,settled") == ["na", "settled"]


def test_parse_tags_tolerates_spacing_after_the_separator():
    assert parse_tags("apac, bulk") == ["apac", "bulk"]


def test_parse_tags_returns_nothing_for_a_blank_column():
    assert parse_tags("") == []
    assert parse_tags(None) == []


def test_parse_tags_passes_an_already_split_column_through():
    assert parse_tags(["already", "a", "list"]) == ["already", "a", "list"]


def test_parse_tags_is_idempotent():
    once = parse_tags("na,settled")
    assert parse_tags(once) == once


def test_parse_tags_does_not_raise_on_a_column_of_an_unusable_type():
    assert parse_tags(17) == []
    assert parse_tags({"na": 1}) == []


NBSP = chr(0xA0)
EM = chr(0x2003)

# Inputs the pre-#87 parser handled and the tokenizer must keep handling identically
# (written out literally, not recomputed). Rows follow PLAN.md's input-space table.
UNCHANGED = [
    # T1 separator then whitespace
    ("na,settled", ["na", "settled"]),
    ("na,\tsettled", ["na", "settled"]),
    ("na,\nsettled", ["na", "settled"]),
    ("na,\r\nsettled", ["na", "settled"]),
    ("na,\n\nsettled", ["na", "settled"]),
    ("na," + NBSP + "settled", ["na", "settled"]),
    ("na," + EM + "settled", ["na", "settled"]),
    # T2 whitespace elsewhere
    ("", []),
    (" ", []),
    (NBSP, []),
    (" na , settled ", ["na", "settled"]),
    ("na" + NBSP + ",settled", ["na", "settled"]),
    # T3 empty parts
    (",", []),
    (",na,", ["na"]),
    ("na,,settled", ["na", "settled"]),
    # T4 no quotes
    ("na;settled", ["na;settled"]),
    ("na settled", ["na settled"]),
    # T5 closed quotes, no comma inside
    ('"na"', ["na"]),
    ('"na",settled', ["na", "settled"]),
    ('na,"settled"', ["na", "settled"]),
    ("\t" + '"na",' + NBSP + '"settled"', ["na", "settled"]),
    # T7 unmatched quotes
    ('na,"settled', ["na", "settled"]),
    ('na",settled', ["na", "settled"]),
    ('"na,settled', ["na", "settled"]),
    ('na,\t"settled', ["na", "settled"]),
    ('na,' + NBSP + '"settled', ["na", "settled"]),
    ('na,\n"settled', ["na", "settled"]),
    ('"a,b', ["a", "b"]),
    ('"""', [""]),
    # T8 empty pair (retained quirk: yields an empty tag)
    ('""', [""]),
    ('x,""', ["x", ""]),
    # T9 mid-word quotes
    ('a"b,c', ['a"b', "c"]),
    ('a",b"', ["a", "b"]),
    ('a",b",c', ["a", "b", "c"]),
    ('a"b,c"d', ['a"b', 'c"d']),
    ('x,a",b"', ["x", "a", "b"]),
    # T10 quote beside a comma
    ('",na', ["", "na"]),
    ('na,"', ["na", ""]),
    # T11 even count, no clean close
    ('"a"b,c"d', ['a"b', 'c"d']),
    ('"a""b,c"', ['a""b', "c"]),
    ('"a" "b,c"', ['a" "b', "c"]),
    ('a",  "b', ["a", "b"]),
    # T12 odd count holding a closed pair with a comma
    ('x,"a,b",y"', ["x", "a", "b", "y"]),
    ('eu,"high,priority",settled"', ["eu", "high", "priority", "settled"]),
    # T13 not a string / list-shaped
    (None, []),
    (17, []),
    (b"na,settled", []),
    ([], []),
    ((), []),
    (["a", " b ", ""], ["a", "b"]),
    (("a", "b"), ["a", "b"]),
    (["a,b", "c"], ["a,b", "c"]),
]

# T6: a closed quoted pair holding a comma is one tag (ruling 2).
RULED = [
    ('eu,"high,priority",settled', ["eu", "high,priority", "settled"]),
    ('eu,"high, priority",settled', ["eu", "high, priority", "settled"]),
    ('"a,b"', ["a,b"]),
    ('x,"a,b"', ["x", "a,b"]),
    ('"a,b",x', ["a,b", "x"]),
    ('"a,b","c,d"', ["a,b", "c,d"]),
    ('x,"a,b","c,d",y', ["x", "a,b", "c,d", "y"]),
    ('"a,b" ,c', ["a,b", "c"]),
    (' "a,b"', ["a,b"]),
    (NBSP + '"a,b",c', ["a,b", "c"]),
    ('eu,\t"high,priority"', ["eu", "high,priority"]),
    ('eu,' + NBSP + '"high,priority",settled', ["eu", "high,priority", "settled"]),
    ('eu,\n"a,b",settled', ["eu", "a,b", "settled"]),
    ('"a,\nb"', ["a,\nb"]),
    ('"a,b",', ["a,b"]),
    ('x,"a,,b",y', ["x", "a,,b", "y"]),
    # Known limit, pinned so it stays deliberate: a pair holding only a comma and a
    # space is one tag ", " (the old parser returned two empty tags).
    ('", "', [", "]),
]


@pytest.mark.parametrize("raw, expected", UNCHANGED)
def test_parse_tags_keeps_every_pre_existing_shape(raw, expected):
    assert parse_tags(raw) == expected


@pytest.mark.parametrize("raw, expected", RULED)
def test_parse_tags_keeps_a_quoted_comma_inside_one_tag(raw, expected):
    assert parse_tags(raw) == expected


def test_parse_tags_output_is_idempotent_for_quoted_commas():
    once = parse_tags('eu,"high,priority",settled')
    assert parse_tags(once) == once


def test_check_record_survives_a_tags_column_that_is_not_a_string():
    from src.validate import check_record

    record = {
        "id": "R-3001",
        "name": "Odd Feed",
        "amount": 1,
        "currency": "USD",
        "region": "NA",
        "tags": ["a", "b"],
    }
    assert check_record(record) is not None
