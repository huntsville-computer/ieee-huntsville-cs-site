#!/usr/bin/env python3
"""
Shared logic for pulling this chapter's event list from vTools, live or
from a CSV export. Used by both vtools_events_to_html.py (Past Events
page HTML) and vtools_events_to_tec_csv.py (The Events Calendar plugin
CSV import).

This chapter's OU is CH03037 ("Huntsville Section Chapter, C16"). Two
live vTools endpoints, no login required:

1. The chapter's own search results page, in CSV form, gives the full
   list of this chapter's event IDs:
   https://events.vtools.ieee.org/events/search.csv?_sub=true&q=&ou=CH03037+-+Huntsville+Section+Chapter%2C+C16&d=All&commit=Search
   (this is the same URL as the "All Events" link, with .csv appended
   before the query string -- it does NOT include end-time, timezone,
   or address details, which is why step 2 is needed.)

2. The documented Events API (https://events.vtools.ieee.org/api/doc/events)
   supports looking up one event at a time by id:
   https://events.vtools.ieee.org/RST/events/api/public/v8/events/list?id=<id>
   This returns full structured data -- start/end time, timezone, tags,
   attendance, cosponsor, contact, address, and the event's own public
   link (https://events.vtools.ieee.org/m/<id>) -- confirmed correct
   against several events spanning 2014-2026.

Note on `spoid`: the generic events-list endpoint's `spoid` parameter
looked like it might let us query all of CH03037's events directly, but
it only works as a sub-filter *inside* an existing named feed scoped to
something broader than a single chapter (a region, society, or
section-group) -- e.g. `/feeds/v8/c/<feed-uid>?spoid=CH03037`. Passing
spoid to the generic endpoint returns a 400: "The 'spoid' parameter is a
feed sub-filter and can only be used with a named feed." Getting a feed
UID requires asking IEEE vTools staff to set one up; we don't have one,
so we fall back to the two-step approach above.
"""
import csv
import io
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

SEARCH_CSV_URL = (
    "https://events.vtools.ieee.org/events/search.csv"
    "?_sub=true&q=&ou=CH03037+-+Huntsville+Section+Chapter%2C+C16"
    "&d=All&commit=Search"
)
EVENT_API_URL = "https://events.vtools.ieee.org/RST/events/api/public/v8/events/list?id={id}"

UPCOMING_SEARCH_URL = (
    "https://events.vtools.ieee.org/events/search?_sub=true&q=&"
    "ou=CH03037+-+Huntsville+Section+Chapter%2C+C16&d=Upcoming&commit=Search"
)
ALL_SEARCH_URL = (
    "https://events.vtools.ieee.org/events/search?_sub=true&q=&"
    "ou=CH03037+-+Huntsville+Section+Chapter%2C+C16&d=All&commit=Search"
)

LEGACY_PREFIX = "[Legacy Report]"

TZ_ABBREV = {
    "America/Chicago": "CT",
    "US/Central": "CT",
    "America/New_York": "ET",
    "US/Eastern": "ET",
}

LOCATION_TYPE_LABELS = {"physical": "In-person", "virtual": "Virtual", "hybrid": "Hybrid"}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ieee-huntsville-cs-site-script/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def fetch_event_ids_live():
    text = fetch(SEARCH_CSV_URL)
    rows = list(csv.DictReader(io.StringIO(text)))
    return [row["id"] for row in rows]


def fetch_event_live(event_id):
    data = json.loads(fetch(EVENT_API_URL.format(id=event_id)))
    return data["data"][0]["attributes"]


def local_datetime(iso_utc_str, tz_name):
    dt_utc = datetime.strptime(iso_utc_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    try:
        tz = ZoneInfo(tz_name) if tz_name else timezone.utc
    except Exception:
        tz = timezone.utc
    return dt_utc.astimezone(tz)


def normalize_from_api(attrs):
    """Map a live API event record into our common event shape."""
    tz_name = attrs["time-zone"]["name"] if attrs.get("time-zone") else ""
    return {
        "id": str(attrs["id"]),
        "title": attrs["title"].strip(),
        "description": attrs.get("description", "") or "",
        "start": local_datetime(attrs["start-time"], tz_name),
        "end": local_datetime(attrs["end-time"], tz_name) if attrs.get("end-time") else None,
        "tz_name": tz_name,
        "address1": attrs.get("address1", "") or "",
        "address2": attrs.get("address2", "") or "",
        "location": attrs.get("city", "") or "",
        "postal_code": attrs.get("postal-code", "") or "",
        "location_type": LOCATION_TYPE_LABELS.get((attrs.get("location-type") or "").lower(), attrs.get("location-type") or ""),
        "members": attrs.get("ieee-attending"),
        "non_members": attrs.get("guests-attending"),
        "contact": attrs.get("contact-email", "") or "",
        "cosponsor": attrs.get("cosponsor-name", "") or "",
        "tags": attrs.get("tags") or [],
        "url": attrs.get("link") or f"https://events.vtools.ieee.org/m/{attrs['id']}",
    }


def normalize_from_csv_row(row):
    """Map a row from a manually-exported (advanced search) CSV into our common event shape."""
    tz_name = row.get("Tm Zone Info", "").strip()
    start = local_datetime(row["Event Date"][:19].replace(" ", "T") + ".000Z", tz_name)
    end_raw = row.get("End Time", "").strip()
    end = local_datetime(end_raw[:19].replace(" ", "T") + ".000Z", tz_name) if end_raw else None

    members = row.get("Number of IEEE Member Attendees", "").strip()
    non_members = row.get("Number of Non-Member Attendees", "").strip()

    return {
        "id": row["Id"],
        "title": row["Event Title"].strip(),
        "description": "",  # not present in the advanced-search CSV export
        "start": start,
        "end": end,
        "tz_name": tz_name,
        "address1": row.get("Address1", "").strip(),
        "address2": row.get("Address2", "").strip(),
        "location": row.get("Event Location", "").strip(),
        "postal_code": row.get("Postal Code", "").strip(),
        "location_type": LOCATION_TYPE_LABELS.get(
            row.get("Location Type", "").strip().lower(), row.get("Location Type", "").strip()
        ),
        "members": members or None,
        "non_members": non_members or None,
        "contact": row.get("Contact Email", "").strip(),
        "cosponsor": row.get("Cosponsor Name", "").strip(),
        "tags": [t.strip() for t in row.get("Tags", "").split(",") if t.strip()],
        "url": f"https://events.vtools.ieee.org/m/{row['Id']}",
    }


def dedupe(events):
    by_key = {}
    for ev in events:
        title = ev["title"]
        is_legacy = title.startswith(LEGACY_PREFIX)
        key = (re.sub(r"^\[Legacy Report\]\s*", "", title).lower(), ev["start"].date())
        existing = by_key.get(key)
        if existing is None or (existing["_is_legacy"] and not is_legacy):
            ev["_is_legacy"] = is_legacy
            by_key[key] = ev
    for ev in by_key.values():
        ev["title"] = re.sub(r"^\[Legacy Report\]\s*", "", ev["title"])
    return list(by_key.values())


def load_events_live():
    ids = fetch_event_ids_live()
    events = []
    for event_id in ids:
        events.append(normalize_from_api(fetch_event_live(event_id)))
        time.sleep(0.2)  # be polite to IEEE's servers
    return events


def load_events_from_csv(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return [normalize_from_csv_row(row) for row in rows]


def load_events(csv_path=None):
    events = load_events_from_csv(csv_path) if csv_path else load_events_live()
    events = dedupe(events)
    events.sort(key=lambda ev: ev["start"])
    return events
