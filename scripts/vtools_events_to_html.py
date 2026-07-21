#!/usr/bin/env python3
"""
Generate the Past Events page HTML (with per-event vTools links) from a
vTools CSV export.

Usage:
    python3 vtools_events_to_html.py path/to/export.csv > past_events.html

Where the CSV comes from: vTools event search results page -> Export to CSV
(see docs/vtools-event-import.md for how to pull it for this chapter, OU
CH03037).

Each event links to its public vTools page at:
    https://events.vtools.ieee.org/m/<Id>
(confirmed working July 2026 -- there's no documented public API endpoint
for a single chapter's events without a pre-arranged custom feed, so the
CSV export + this script is the practical path until/unless IEEE staff
sets one up.)
"""
import csv
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

VTOOLS_EVENT_URL = "https://events.vtools.ieee.org/m/{id}"

LEGACY_PREFIX = "[Legacy Report]"


def load_events(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    by_key = {}
    for row in rows:
        title = row["Event Title"].strip()
        date = row["Event Date"][:10]  # YYYY-MM-DD
        is_legacy = title.startswith(LEGACY_PREFIX)
        key = (re.sub(r"^\[Legacy Report\]\s*", "", title).lower(), date)

        existing = by_key.get(key)
        if existing is None or (existing["_is_legacy"] and not is_legacy):
            row["_is_legacy"] = is_legacy
            by_key[key] = row

    return list(by_key.values())


def local_datetime(raw_utc_str, tz_name):
    """vTools CSV timestamps are UTC; convert to the event's own timezone."""
    dt_utc = datetime.strptime(raw_utc_str[:19], "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    try:
        tz = ZoneInfo(tz_name) if tz_name else timezone.utc
    except Exception:
        tz = timezone.utc
    return dt_utc.astimezone(tz)


TZ_ABBREV = {
    "America/Chicago": "CT",
    "US/Central": "CT",
    "America/New_York": "ET",
    "US/Eastern": "ET",
}


def format_event(row):
    title = re.sub(r"^\[Legacy Report\]\s*", "", row["Event Title"].strip())
    event_id = row["Id"]
    url = VTOOLS_EVENT_URL.format(id=event_id)

    tz_name = row.get("Tm Zone Info", "").strip()
    dt = local_datetime(row["Event Date"], tz_name)
    date_str = dt.strftime("%B %-d, %Y")
    start_str = dt.strftime("%-I:%M %p").lstrip("0")

    end_time = row.get("End Time", "").strip()
    end_str = ""
    if end_time:
        end_dt = local_datetime(end_time, tz_name)
        end_str = f" – {end_dt.strftime('%-I:%M %p').lstrip('0')}"

    tz_str = f" ({TZ_ABBREV.get(tz_name, tz_name)})" if tz_name else ""

    location = row.get("Event Location", "").strip()
    location_type = row.get("Location Type", "").strip()
    fmt = {"physical": "In-person", "virtual": "Virtual", "hybrid": "Hybrid"}.get(
        location_type.lower(), location_type
    )

    members = row.get("Number of IEEE Member Attendees", "").strip()
    non_members = row.get("Number of Non-Member Attendees", "").strip()
    attendee_bits = []
    if members:
        attendee_bits.append(f"{members} IEEE members")
    if non_members:
        attendee_bits.append(f"{non_members} non-members")
    attendees_str = ", ".join(attendee_bits)

    contact = row.get("Contact Email", "").strip()
    cosponsor = row.get("Cosponsor Name", "").strip()
    tags = row.get("Tags", "").strip()

    detail_line = " | ".join(
        filter(None, [location, fmt, f"Attendees: {attendees_str}" if attendees_str else ""])
    )

    extra_lines = []
    if cosponsor:
        extra_lines.append(f"Co-sponsor: {cosponsor}")
    if tags:
        extra_lines.append(f"Tags: {tags}")
    if contact:
        extra_lines.append(f"Contact: {contact}")

    lines = [
        f'<p><strong><a href="{url}" target="_blank" rel="noopener">{title}</a></strong><br>',
        f"{date_str} | {start_str}{end_str}{tz_str}<br>",
    ]
    if detail_line:
        lines.append(f"{detail_line}<br>")
    if extra_lines:
        lines.append(" | ".join(extra_lines) + "<br>")

    # drop trailing <br> on the last line before closing </p>
    lines[-1] = lines[-1].rsplit("<br>", 1)[0]
    lines.append("</p>")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} path/to/export.csv", file=sys.stderr)
        sys.exit(1)

    events = load_events(sys.argv[1])
    events.sort(key=lambda r: r["Event Date"])

    by_year = defaultdict(list)
    for row in events:
        local_dt = local_datetime(row["Event Date"], row.get("Tm Zone Info", "").strip())
        by_year[str(local_dt.year)].append(row)

    print(
        '<p>\n'
        '  <a href="https://events.vtools.ieee.org/events/search?_sub=true&amp;q=&amp;'
        'ou=CH03037+-+Huntsville+Section+Chapter%2C+C16&amp;d=Upcoming&amp;commit=Search" '
        'target="_blank" rel="noopener">Upcoming Events (vTools)</a> |\n'
        '  <a href="https://events.vtools.ieee.org/events/search?_sub=true&amp;q=&amp;'
        'ou=CH03037+-+Huntsville+Section+Chapter%2C+C16&amp;d=All&amp;commit=Search" '
        'target="_blank" rel="noopener">All Events (vTools)</a>\n'
        "</p>\n"
    )

    for year in sorted(by_year.keys(), reverse=True):
        print(f"<h2>{year}</h2>\n")
        for row in by_year[year]:
            print(format_event(row))
            print()


if __name__ == "__main__":
    main()
