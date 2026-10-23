"""Helpers for the feed's packed columns."""

from __future__ import annotations

import re

_TAG_SEPARATOR = re.compile(r",\s*")

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


def _skip_space(raw: str, i: int) -> int:
    while i < len(raw) and raw[i].isspace():
        i += 1
    return i


def _split_tags(raw: str) -> list[str]:
    """Split *raw* into raw (unstripped) parts, one per tag.

    A comma separates tags (together with the whitespace after it) except
    inside a closed double-quoted pair. A pair opens only at the start of a tag
    and closes only at the first following quote, when that quote is followed by
    optional whitespace and then a comma or the end of the string. A string with
    an odd number of quotes is split on every comma, as before quoting existed.
    """
    if raw.count('"') % 2:
        return _TAG_SEPARATOR.split(raw)
    parts = []
    start = 0
    while True:
        k = _skip_space(raw, start)
        end = -1
        if k < len(raw) and raw[k] == '"':
            close = raw.find('"', k + 1)
            if close > 0:
                after = _skip_space(raw, close + 1)
                if after == len(raw) or raw[after] == ",":
                    end = after
        if end < 0:
            end = raw.find(",", start)
            if end < 0:
                end = len(raw)
        parts.append(raw[start:end])
        if end >= len(raw):
            return parts
        start = _skip_space(raw, end + 1)


def parse_tags(raw: str | None) -> list[str]:
    """Split the feed's ``tags`` column into individual tags.

    The column is a comma-separated list; a tag containing a comma is wrapped
    in double quotes by the upstream exporter, and that comma does not split.

    A feed row is free-form JSON, so the column is not guaranteed to be a
    string. A column that is already a sequence is already split and passes
    through; anything else yields no tags rather than raising, because
    ``check_record()`` promises a normalised record or ``None`` and cannot keep
    that promise if this throws. Passing this function its own output returns
    that output unchanged.
    """
    if isinstance(raw, (list, tuple)):
        return [str(tag).strip() for tag in raw if str(tag).strip()]
    if not isinstance(raw, str) or not raw:
        return []
    return [part.strip().strip('"') for part in _split_tags(raw) if part.strip()]
