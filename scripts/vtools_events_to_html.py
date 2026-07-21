#!/usr/bin/env python3
"""
Generate the full Past Events page HTML: this chapter's vTools events
(fetched live, no manual CSV export needed -- see vtools_events.py),
merged with the pre-vTools 2006 events from ../docs/old-site-past-events.md.
One script, one combined output, ready to paste into WordPress
(Pages -> Past Events -> Backend Editor -> Code).

Usage:
    python3 vtools_events_to_html.py > past_events.html

    # Or, to run against a previously-saved CSV export instead of the
    # live site (e.g. if vtools.ieee.org is unreachable):
    python3 vtools_events_to_html.py path/to/export.csv > past_events.html

To record more pre-vTools events later, just edit
docs/old-site-past-events.md (same `**Title**` / `- Date: ...` /
`- Speaker: ...` format) -- this script picks it up automatically.
"""
import re
import sys
import urllib.error
from collections import defaultdict
from pathlib import Path

from vtools_events import ALL_SEARCH_URL, TZ_ABBREV, UPCOMING_SEARCH_URL, load_events

OLD_SITE_EVENTS_PATH = Path(__file__).parent.parent / "docs" / "old-site-past-events.md"


def format_event(ev):
    date_str = ev["start"].strftime("%B %-d, %Y")
    start_str = ev["start"].strftime("%-I:%M %p").lstrip("0")
    end_str = f" – {ev['end'].strftime('%-I:%M %p').lstrip('0')}" if ev["end"] else ""
    tz_str = f" ({TZ_ABBREV.get(ev['tz_name'], ev['tz_name'])})" if ev["tz_name"] else ""

    attendee_bits = []
    if ev["members"] not in (None, ""):
        attendee_bits.append(f"{ev['members']} IEEE members")
    if ev["non_members"] not in (None, ""):
        attendee_bits.append(f"{ev['non_members']} non-members")
    attendees_str = ", ".join(attendee_bits)

    detail_line = " | ".join(
        filter(None, [ev["location"], ev["location_type"], f"Attendees: {attendees_str}" if attendees_str else ""])
    )

    # Hashtag-style tags (from the live API) read better space-separated;
    # plain-text tags (from a manually-exported CSV) read better comma-separated.
    tags_str = ""
    if ev["tags"]:
        tags_str = " ".join(ev["tags"]) if ev["tags"][0].startswith("#") else ", ".join(ev["tags"])

    extra_lines = []
    if ev["cosponsor"]:
        extra_lines.append(f"Co-sponsor: {ev['cosponsor']}")
    if tags_str:
        extra_lines.append(f"Tags: {tags_str}")
    if ev["contact"]:
        extra_lines.append(f"Contact: {ev['contact']}")

    lines = [
        f'<p><strong><a href="{ev["url"]}" target="_blank" rel="noopener">{ev["title"]}</a></strong><br>',
        f"{date_str} | {start_str}{end_str}{tz_str}<br>",
    ]
    if detail_line:
        lines.append(f"{detail_line}<br>")
    if extra_lines:
        lines.append(" | ".join(extra_lines) + "<br>")

    lines[-1] = lines[-1].rsplit("<br>", 1)[0]
    lines.append("</p>")
    return "\n".join(lines)


def load_old_site_events(path=OLD_SITE_EVENTS_PATH):
    """
    Parse docs/old-site-past-events.md's `**Title**` / `- Key: Value` blocks
    into (year, html_block) pairs. These predate vTools, so there's no start/
    end datetime to work with -- the date line is kept as free text.
    """
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", text)

    results = []
    for block in blocks:
        block = block.strip()
        title_match = re.match(r"\*\*(.+?)\*\*\s*\n(.+)", block, re.S)
        if not title_match:
            continue
        title, body = title_match.groups()

        fields = []
        for line in body.strip().splitlines():
            field_match = re.match(r"-\s*([^:]+):\s*(.+)", line.strip())
            if field_match:
                fields.append(field_match.groups())
        if not fields:
            continue

        date_value = next((v for k, v in fields if k.strip().lower() == "date"), "")
        year_match = re.search(r"\b(\d{4})\b", date_value)
        if not year_match:
            continue
        year = int(year_match.group(1))

        lines = [f"<p><strong>{title}</strong><br>", f"{date_value}<br>"]
        for key, value in fields:
            if key.strip().lower() == "date":
                continue
            lines.append(f"{key.strip()}: {value}<br>")
        lines[-1] = lines[-1].rsplit("<br>", 1)[0]
        lines.append("</p>")

        results.append((year, "\n".join(lines)))

    return results


def main():
    if len(sys.argv) > 2:
        print(f"Usage: {sys.argv[0]} [path/to/export.csv]", file=sys.stderr)
        sys.exit(1)

    try:
        events = load_events(sys.argv[1] if len(sys.argv) == 2 else None)
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"Couldn't reach vtools.ieee.org live ({e}).", file=sys.stderr)
        print("Pass a CSV export path as an argument instead.", file=sys.stderr)
        sys.exit(1)

    by_year_html = defaultdict(list)
    for year, html_block in load_old_site_events():
        by_year_html[year].append(html_block)
    for ev in events:
        by_year_html[ev["start"].year].append(format_event(ev))

    print(
        "<p>\n"
        f'  <a href="{UPCOMING_SEARCH_URL.replace("&", "&amp;")}" target="_blank" rel="noopener">Upcoming Events (vTools)</a> |\n'
        f'  <a href="{ALL_SEARCH_URL.replace("&", "&amp;")}" target="_blank" rel="noopener">All Events (vTools)</a>\n'
        "</p>\n"
    )

    # Oldest year first, matching the page's existing structure.
    for year in sorted(by_year_html.keys()):
        print(f"<h2>{year}</h2>\n")
        for html_block in by_year_html[year]:
            print(html_block)
            print()


if __name__ == "__main__":
    main()
