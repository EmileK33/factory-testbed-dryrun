"""Tests for the rendered settlement report."""

from src.records import load_records
from src.report import render_report
from src.validate import check_record


def test_report_lists_every_accepted_record():
    text = render_report()
    accepted = [row for row in (check_record(r) for r in load_records()) if row]
    for row in accepted:
        assert row["id"] in text


def test_report_reports_the_counts_it_read():
    text = render_report()
    assert f"Records read: {len(load_records())}" in text


def test_report_ends_with_a_newline():
    assert render_report().endswith("\n")


def test_report_shows_each_records_tags():
    lines = render_report().splitlines()
    header = next(line for line in lines if line.startswith("id "))
    assert header.endswith("tags")
    row = next(line for line in lines if line.startswith("R-1001"))
    assert row.endswith("eu; high,priority; settled")


def test_report_shows_a_dash_for_a_record_without_tags():
    base = {"id": "R-9001", "name": "No Tags", "amount": 5, "currency": "USD", "region": "NA"}
    for tags in ({}, {"tags": []}, {"tags": ""}):
        lines = render_report([{**base, **tags}]).splitlines()
        row = next(line for line in lines if line.startswith("R-9001"))
        assert row.endswith("  -")
        assert "[]" not in row


def test_report_tags_cell_never_breaks_the_row_or_prints_none():
    from src.report import _cell

    tags = ["high\npriority", None, "set\r\ntled"]
    assert _cell({"tags": tags}, "tags") == "high priority; set tled"
    assert _cell({"tags": (None,)}, "tags") == "-"
    base = {"id": "R-9002", "name": "Wrapped", "amount": 5, "currency": "USD", "region": "NA"}
    text = render_report([{**base, "tags": tags}])
    row = next(line for line in text.splitlines() if line.startswith("R-9002"))
    assert row.endswith("high priority; set tled")
    assert "None" not in row


def test_report_footer_states_the_true_validated_count():
    from src.validate import VALIDATED_FIELDS

    text = render_report()
    assert "5 of 6 reported fields are checked by the validation rules." in text
    assert "All 6" not in text
    assert "tags" not in VALIDATED_FIELDS


def test_report_names_the_unlabelled_record():
    assert "Unlabelled records: Fennel Labs" in render_report()
