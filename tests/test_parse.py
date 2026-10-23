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


QUOTED = ["eu", "high,priority", "settled"]
OVERSIZE = "x" * 200000  # past csv's 131072-character field limit


def test_parse_tags_keeps_a_quoted_comma_tag_whole():
    assert parse_tags('eu,"high,priority",settled') == QUOTED
    assert parse_tags('"x, y" , z') == ["x, y", "z"]


def test_parse_tags_keeps_a_quoted_comma_whole_across_a_line_break():
    from src.validate import check_record

    for sep in ("\n", "\r", "\r\n"):
        raw = f'eu,"high,priority",{sep}settled'
        assert parse_tags(raw) == QUOTED
        record = {
            "id": "R-3002",
            "name": "Wrapped Feed",
            "amount": 1,
            "currency": "USD",
            "region": "NA",
            "tags": raw,
        }
        assert check_record(record)["tags"] == QUOTED
    assert parse_tags("na,\nsettled") == ["na", "settled"]
    assert parse_tags('eu,"high\npriority",settled') == ["eu", "high priority", "settled"]


def test_parse_tags_an_oversize_field_yields_one_tag_and_does_not_raise():
    from src.validate import check_record

    assert parse_tags(OVERSIZE) == [OVERSIZE]
    assert parse_tags("  " + OVERSIZE + "  ") == [OVERSIZE]
    record = {
        "id": "R-3003",
        "name": "Huge Feed",
        "amount": 1,
        "currency": "USD",
        "region": "NA",
        "tags": OVERSIZE,
    }
    assert check_record(record)["tags"] == [OVERSIZE]


def test_parse_tags_a_value_csv_rejects_is_not_split():
    assert parse_tags("a," + OVERSIZE) == ["a," + OVERSIZE]


def test_parse_tags_unbalanced_quote_does_not_raise():
    assert parse_tags('eu,"high') == ["eu", "high"]


def test_parse_tags_blank_after_stripping_yields_nothing():
    assert parse_tags("   ") == []
    assert parse_tags(",,") == []


def test_parse_tags_is_idempotent_on_the_quoted_witness():
    once = parse_tags('eu,"high,priority",\nsettled')
    assert parse_tags(once) == once


WHITESPACE_BEFORE_A_QUOTE = {
    "TAB": "\t",
    "NBSP": " ",
    "VT": "\x0b",
    "FF": "\x0c",
    "U+2007": " ",
    "U+202F": " ",
    "CRLF+TAB": "\r\n\t",
    "mixed": " \t \x0b",
}


@pytest.mark.parametrize("gap", list(WHITESPACE_BEFORE_A_QUOTE.values()), ids=list(WHITESPACE_BEFORE_A_QUOTE))
def test_parse_tags_whitespace_before_a_quote_does_not_hide_the_quote(gap):
    assert parse_tags(f'eu,{gap}"high,priority",settled') == QUOTED


def test_parse_tags_treats_every_whitespace_character_alike():
    every = [chr(i) for i in range(0x110000) if chr(i).isspace()]
    assert len(every) >= 25  # the denominator: the str.split() set, not a sample
    for gap in every:
        assert parse_tags(f'eu,{gap}"high,priority",settled') == QUOTED, hex(ord(gap))
        assert parse_tags(f'eu,"high{gap}priority"{gap},settled') == ["eu", "high priority", "settled"]
        assert parse_tags(f"{gap}na,{gap}settled{gap}") == ["na", "settled"]
        assert parse_tags(gap + gap) == []


def test_parse_tags_skips_a_space_before_an_opening_quote():
    assert parse_tags('eu, "high,priority", settled') == QUOTED


def test_parse_tags_collapses_a_run_of_spaces_inside_a_quoted_tag():
    # Side effect of the one normalisation: whitespace inside a tag is not preserved.
    assert parse_tags('eu,"high   priority",settled') == ["eu", "high priority", "settled"]
    assert parse_tags('eu,"high\t  priority",settled') == ["eu", "high priority", "settled"]


def test_parse_tags_normalises_a_list_element_with_a_line_break():
    assert parse_tags(["high\npriority", "settled"]) == ["high priority", "settled"]
    assert parse_tags(("a\r\n\tb", "c d")) == ["a b", "c d"]
    assert parse_tags(["a   b"]) == ["a b"]


def test_parse_tags_drops_none_and_empty_list_elements():
    assert parse_tags(["a", None, "b"]) == ["a", "b"]
    assert parse_tags([None]) == []
    assert parse_tags(["a", "", "  ", " ", "b"]) == ["a", "b"]
    assert parse_tags([5, True]) == ["5", "True"]


def test_parse_tags_list_output_is_idempotent_after_normalising():
    once = parse_tags(["high\npriority", None, "settled"])
    assert parse_tags(once) == once


def test_parse_tags_does_not_raise_on_a_column_of_an_unusable_type():
    assert parse_tags(17) == []
    assert parse_tags({"na": 1}) == []


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
