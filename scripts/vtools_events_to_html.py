#!/usr/bin/env python3
"""
Generate the Past Events page HTML (with per-event vTools links) by
pulling this chapter's event list live from vTools -- no manual CSV
export needed. See vtools_events.py for how the live fetch works.

Usage:
    python3 vtools_events_to_html.py > past_events.html

    # Or, to run against a previously-saved CSV export instead of the
    # live site (e.g. if vtools.ieee.org is unreachable):
    python3 vtools_events_to_html.py path/to/export.csv > past_events.html
"""
import sys
import urllib.error
from collections import defaultdict

from vtools_events import ALL_SEARCH_URL, TZ_ABBREV, UPCOMING_SEARCH_URL, load_events


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

    by_year = defaultdict(list)
    for ev in events:
        by_year[ev["start"].year].append(ev)

    print(
        "<p>\n"
        f'  <a href="{UPCOMING_SEARCH_URL.replace("&", "&amp;")}" target="_blank" rel="noopener">Upcoming Events (vTools)</a> |\n'
        f'  <a href="{ALL_SEARCH_URL.replace("&", "&amp;")}" target="_blank" rel="noopener">All Events (vTools)</a>\n'
        "</p>\n"
    )

    for year in sorted(by_year.keys(), reverse=True):
        print(f"<h2>{year}</h2>\n")
        for ev in by_year[year]:
            print(format_event(ev))
            print()


if __name__ == "__main__":
    main()
