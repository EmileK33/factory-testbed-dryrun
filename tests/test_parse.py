"""Tests for the packed-column helpers."""

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
