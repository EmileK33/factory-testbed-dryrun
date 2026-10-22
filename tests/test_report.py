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


def _lines(records=None):
    return render_report(records).splitlines()


def test_report_has_a_tags_column_last():
    assert _lines()[3].split()[-1] == "tags"


def test_report_shows_each_records_tags_joined_with_semicolons():
    rows = {line.split()[0]: line for line in _lines()[5:10]}
    assert rows["R-1001"].endswith("  eu; high,priority; settled")
    assert rows["R-1002"].endswith("  na; settled")


def test_report_shows_a_dash_for_a_record_with_no_tags():
    record = {"id": "R-9", "name": "N", "amount": 5, "currency": "USD", "region": "NA"}
    row = _lines([record])[5]
    assert row.startswith("R-9") and row.endswith("  -")


def test_report_leaves_other_list_valued_cells_as_they_were():
    record = {
        "id": "R-9",
        "name": [1],
        "amount": 5,
        "currency": "USD",
        "region": "NA",
        "tags": "na",
    }
    row = _lines([record])[5]
    assert row.startswith("R-9") and "[1]" in row


def test_report_footer_states_the_true_validated_count():
    from src.validate import VALIDATED_FIELDS

    text = render_report()
    assert "tags" not in VALIDATED_FIELDS
    assert "reported fields are checked" not in text
    assert "Reported fields covered by the validation rules: 5 of 6." in text.splitlines()


def test_report_names_the_unlabelled_record():
    assert "Unlabelled records: Fennel Labs" in render_report()
