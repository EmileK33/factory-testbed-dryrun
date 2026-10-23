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


EXPECTED_TAGS = {
    "R-1001": "eu; high,priority; settled",
    "R-1002": "na; settled",
    "R-1003": "apac; bulk",
    "R-1004": "na; small",
    "R-1005": "eu; crossborder",
}


def _table_rows(text):
    lines = text.split("\n")
    rows = []
    for line in lines[5:]:
        if line == "":
            break
        rows.append(line)
    return lines[3], rows


def test_report_rows_carry_each_records_exact_tags():
    header, rows = _table_rows(render_report())
    assert header.endswith("tags")
    by_id = {row.split()[0]: row for row in rows}
    assert set(by_id) == set(EXPECTED_TAGS)
    for rec_id, tags in EXPECTED_TAGS.items():
        assert by_id[rec_id].endswith("  " + tags)


def test_report_shows_a_dash_for_a_record_without_tags():
    base = {"name": "N", "amount": 5, "currency": "USD", "region": "NA"}
    text = render_report([dict(base, id="X-1"), dict(base, id="X-2", tags=""), dict(base, id="X-3", tags="na")])
    _, rows = _table_rows(text)
    assert [row.split()[-1] for row in rows] == ["-", "-", "na"]


def test_report_footer_states_the_true_validated_count():
    from src import validate
    text = render_report()
    columns = _table_rows(text)[0].split()
    covered = len([f for f in columns if f in validate.VALIDATED_FIELDS])
    assert f"Reported fields covered by validation: {covered} of {len(columns)}" in text.split("\n")
    assert "reported fields are checked by the validation rules" not in text
    assert "tags" not in validate.VALIDATED_FIELDS
    assert "tags" not in [ln for ln in text.split("\n") if ln.startswith("Validation covers:")][0]


def test_report_ends_with_a_newline():
    assert render_report().endswith("\n")


def test_report_names_the_unlabelled_record():
    assert "Unlabelled records: Fennel Labs" in render_report()
