"""Helpers for the feed's packed columns."""

from __future__ import annotations

import csv

# The feed contract fixes the tag vocabulary: a tag outside this set is an
# exporter error rather than a new category. ``parse_tags()`` drops anything
# unrecognised before returning, so no downstream consumer has to re-check.
KNOWN_TAGS = (
    "air",
    "apac",
    "bulk",
    "crossborder",
    "eu",
    "high",
    "na",
    "priority",
    "rail",
    "settled",
    "small",
    "unlabelled",
)


def _squash(text: str) -> str:
    """The one whitespace normaliser: every run of whitespace becomes one space."""
    return " ".join(text.split())


def _clean(items: object) -> list[str]:
    """Normalise each item with ``_squash()``; drop ``None`` and empty items."""
    squashed = (_squash(str(item)) for item in items if item is not None)
    return [tag for tag in squashed if tag]


def parse_tags(raw: str | None) -> list[str]:
    """Split the feed's ``tags`` column into individual tags.

    The column is a comma-separated list; a tag containing a comma is wrapped
    in double quotes by the upstream exporter.

    A feed row is free-form JSON, so the column is not guaranteed to be a
    string. A column that is already a sequence is already split and passes
    through; anything else yields no tags rather than raising, because
    ``check_record()`` promises a normalised record or ``None`` and cannot keep
    that promise if this throws. Passing this function its own output returns
    that output unchanged.

    A string is read by one parser, the ``csv`` reader, so a quoted tag keeps
    its comma. Line breaks (LF, CR, CRLF) are turned into spaces first, because
    the reader rejects a raw one outside quotes and the column is one logical
    line. A value the reader still rejects (a field past its size limit) is not
    split: it yields one tag holding the stripped text.

    One helper, ``_squash()``, normalises whitespace: every run of Unicode
    whitespace (the ``str.split()`` set: space, TAB, NBSP, VT, FF, CR, LF,
    U+2007, U+202F and the rest) becomes one space. It runs on the string before
    the reader sees it, so a TAB or NBSP between a comma and an opening quote no
    longer hides the quote, and on every element of a list or tuple, which drops
    ``None`` and empty elements. Side effect: a run of spaces inside a quoted tag
    collapses to one.
    """
    if isinstance(raw, (list, tuple)):
        return _clean(raw)
    if not isinstance(raw, str):
        return []
    text = _squash(raw)
    if not text:
        return []
    try:
        fields = next(csv.reader([text], skipinitialspace=True), [])
    except csv.Error:
        fields = [text]
    return _clean(fields)
