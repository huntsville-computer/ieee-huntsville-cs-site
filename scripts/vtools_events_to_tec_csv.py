#!/usr/bin/env python3
"""
Generate CSV files for importing this chapter's vTools events into
The Events Calendar WordPress plugin, which is what actually powers the
site's /events/ page (see docs/learnings.md). See vtools_events.py for
how the live vTools fetch works.

Column reference: https://docs.nexcess.com/software/the-events-calendar/import-events-csv/

Usage:
    python3 vtools_events_to_tec_csv.py
        -> writes events.csv and venues.csv in the current directory

    python3 vtools_events_to_tec_csv.py --out-dir /some/path
        -> writes them there instead

    python3 vtools_events_to_tec_csv.py path/to/export.csv
        -> use a manually-exported CSV instead of fetching live
           (note: that export doesn't include event descriptions --
           see load_events() in vtools_events.py)

Import order matters: import venues.csv first (Events > Import > CSV,
select "Venues" as the import type), *then* events.csv (same screen,
select "Events"). The events importer matches "Event Venue Name" to an
existing Venue post by exact name -- if venues.csv hasn't been imported
first, events will import without a linked venue.

Assumptions baked in below (all easy to change by editing the constants
at the top of this file):
- Event Category is set to a single fixed value for every event, since
  this whole feed is already scoped to one chapter (CH03037). Change
  EVENT_CATEGORY if you'd rather split it up.
- Venue Country defaults to "United States" for any physical/hybrid
  event -- vTools' API exposes country as a numeric id (via a
  `relationships.country` lookup) rather than a name, and every event
  in this chapter's history has in fact been US-based, so hardcoding
  was simpler than adding a second API call per event to resolve it.
  If that ever stops being true, this will need fixing.
- Venue Name is built from the event's address (address1 + city), not a
  human venue name like "GigaParts, Inc." -- vTools doesn't give us a
  separate venue name field, just an address. Events at the same address
  will correctly share one venue.
"""
import argparse
import csv
import html
import re
import sys
from pathlib import Path

from vtools_events import load_events

EVENT_CATEGORY = "IEEE Computer Society"
DEFAULT_COUNTRY = "United States"

EVENTS_CSV_COLUMNS = [
    "Event Name",
    "Event Description",
    "Event Start Date",
    "Event Start Time",
    "Event End Date",
    "Event End Time",
    "All Day Event",
    "Timezone",
    "Event Venue Name",
    "Event Category",
    "Event Tags",
    "Event Website",
]

VENUES_CSV_COLUMNS = [
    "Venue Name",
    "Venue Address",
    "Venue Address 2",
    "Venue City",
    "Venue State/Province",
    "Venue Zip",
    "Venue Country",
]


def venue_name_for(ev):
    if not ev["address1"] and not ev["location"]:
        return ""
    parts = [p for p in [ev["address1"].strip(), ev["location"].strip()] if p]
    return ", ".join(parts)


def strip_html(text):
    # crude, but Event Description just needs to be readable plain text
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", text).strip()


def event_row(ev):
    return {
        "Event Name": ev["title"],
        "Event Description": strip_html(ev["description"]),
        "Event Start Date": ev["start"].strftime("%Y-%m-%d"),
        "Event Start Time": ev["start"].strftime("%H:%M:%S"),
        "Event End Date": ev["end"].strftime("%Y-%m-%d") if ev["end"] else ev["start"].strftime("%Y-%m-%d"),
        "Event End Time": ev["end"].strftime("%H:%M:%S") if ev["end"] else "",
        "All Day Event": "false",
        "Timezone": ev["tz_name"],
        "Event Venue Name": venue_name_for(ev),
        "Event Category": EVENT_CATEGORY,
        "Event Tags": ", ".join(ev["tags"]),
        "Event Website": ev["url"],
    }


def venue_rows(events):
    venues = {}
    for ev in events:
        name = venue_name_for(ev)
        if not name or name in venues:
            continue
        venues[name] = {
            "Venue Name": name,
            "Venue Address": ev["address1"],
            "Venue Address 2": ev["address2"],
            "Venue City": ev["location"],
            "Venue State/Province": "",
            "Venue Zip": ev["postal_code"],
            "Venue Country": DEFAULT_COUNTRY if ev["location_type"] != "Virtual" else "",
        }
    return list(venues.values())


def write_csv(path, columns, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path", nargs="?", help="manually-exported CSV to use instead of fetching live")
    parser.add_argument("--out-dir", default=".", help="directory to write events.csv/venues.csv into")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    events = load_events(args.csv_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    events_path = out_dir / "events.csv"
    venues_path = out_dir / "venues.csv"

    write_csv(events_path, EVENTS_CSV_COLUMNS, [event_row(ev) for ev in events])
    write_csv(venues_path, VENUES_CSV_COLUMNS, venue_rows(events))

    print(f"Wrote {len(events)} events to {events_path}", file=sys.stderr)
    print(f"Wrote {venues_path}", file=sys.stderr)
    print("Import venues.csv first, then events.csv (Events -> Import -> CSV).", file=sys.stderr)


if __name__ == "__main__":
    main()
