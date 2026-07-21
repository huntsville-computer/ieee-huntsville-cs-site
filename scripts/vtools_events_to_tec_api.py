#!/usr/bin/env python3
"""
Push this chapter's vTools events into The Events Calendar via its REST
API, instead of the Events -> Import -> CSV screen (which some WP
Engine/security-plugin setups block with "Sorry, you are not allowed to
upload this file type" -- see docs/vtools-event-import.md). No file
upload involved here at all, so that restriction doesn't apply.

Requires a WordPress Application Password for a user who can publish
posts (Editor or Administrator): WordPress admin -> Users -> your
profile -> Application Passwords -> add a new one named e.g.
"vtools-import". Never put the password in this repo -- pass it via
environment variables:

    export TEC_WP_USERNAME="your-wp-username"
    export TEC_WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"
    python3 vtools_events_to_tec_api.py

By default this creates everything as DRAFTS, so nothing goes live on
the public site until you review and publish from wp-admin yourself.
Pass --publish once you're happy with a dry run to publish directly.

Re-run safety, with one confirmed catch: it checks for existing venues
(by name) and events (by title + start time) before creating anything,
so running it again after adding new vTools events won't duplicate
already-PUBLISHED items. But this site's GET /venues and GET /events
endpoints only accept status=publish (confirmed: even status=draft
alone returns a 400 rest_invalid_param, regardless of authentication)
-- there's no way to query for existing drafts via this API. So if you
run this twice while a first run's drafts are still sitting unpublished,
the second run WON'T see them and will create duplicates. Workflow that
avoids this: run once, review and publish (or delete) everything in
wp-admin, then future runs will correctly see the published events/venues
and skip them.

Confirmed live against https://r3.ieee.org/huntsville-computer/wp-json/tribe/events/v1/
on 2026-07-20 -- that's the default --site value below. GET requests
work unauthenticated; POST requires a valid Application Password (a bad
one correctly gets a 401 rest_forbidden, so auth errors are easy to
tell apart from Cloudflare/WAF blocks -- see the User-Agent header
below, which is required to avoid the latter).
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from vtools_events import load_events

DEFAULT_SITE = "https://r3.ieee.org/huntsville-computer"
EVENT_CATEGORY = "IEEE Computer Society"
DEFAULT_COUNTRY = "United States"


class Api:
    def __init__(self, site, username, app_password):
        self.base = site.rstrip("/") + "/wp-json/tribe/events/v1"
        token = base64.b64encode(f"{username}:{app_password}".encode()).decode()
        self.auth_header = f"Basic {token}"

    def request(self, method, path, params=None, body=None):
        url = f"{self.base}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params, doseq=True)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", self.auth_header)
        req.add_header("Content-Type", "application/json")
        # Python's default urllib User-Agent trips WP Engine/Cloudflare's bot
        # blocking (seen as a 403 "error code: 1010") even with valid auth.
        req.add_header("User-Agent", "Mozilla/5.0 (compatible; ieee-huntsville-cs-site-script/1.0)")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {detail}") from None

    def get_all(self, path, params=None):
        """Page through a GET endpoint's results (uses the plugin's own per_page/page params)."""
        items = []
        page = 1
        params = dict(params or {})
        while True:
            params["page"] = page
            params["per_page"] = 100
            data = self.request("GET", path, params=params)
            key = next(k for k in data if isinstance(data.get(k), list))
            batch = data[key]
            items.extend(batch)
            if page >= data.get("total_pages", 1) or not batch:
                break
            page += 1
        return items

    def get_all_any_status(self, path):
        """
        Like get_all(), but first tries status=publish,draft to include
        drafts (so a re-run can see not-yet-published items from a previous
        run). Confirmed this site's GET /venues and /events only accept
        status=publish -- status=draft alone also gets rejected with 400
        rest_invalid_param, so this always falls back to published-only here.
        Kept as a try/except (rather than deleted) in case this site's REST
        API version ever changes to support it, or in case someone points
        --site at a different install that does.
        """
        try:
            return self.get_all(path, {"status": "publish,draft"})
        except RuntimeError as e:
            print(f"  (couldn't fetch drafts too -- {e}; falling back to published-only)", file=sys.stderr)
            return self.get_all(path)


def venue_name_for(ev):
    if not ev["address1"] and not ev["location"]:
        return ""
    parts = [p for p in [ev["address1"].strip(), ev["location"].strip()] if p]
    return ", ".join(parts)


def ensure_venues(api, events, status):
    needed = {}
    for ev in events:
        name = venue_name_for(ev)
        if name and name not in needed:
            needed[name] = ev

    existing = {v["venue"]: v["id"] for v in api.get_all_any_status("/venues")}

    name_to_id = {}
    for name, ev in needed.items():
        if name in existing:
            name_to_id[name] = existing[name]
            continue
        created = api.request(
            "POST",
            "/venues",
            body={
                "venue": name,
                "address": ev["address1"],
                "city": ev["location"],
                "zip": ev["postal_code"],
                "country": DEFAULT_COUNTRY if ev["location_type"] != "Virtual" else "",
                "status": status,
            },
        )
        name_to_id[name] = created["id"]
        print(f"  created venue: {name} (id {created['id']})", file=sys.stderr)
        time.sleep(0.2)
    return name_to_id


def existing_event_keys(api):
    existing = api.get_all_any_status("/events")
    keys = set()
    for e in existing:
        title = (e.get("title") or "").strip().lower()
        start = (e.get("start_date") or "")[:19]
        keys.add((title, start))
    return keys


def create_event(api, ev, venue_id, status):
    body = {
        "title": ev["title"],
        "description": ev["description"],
        "start_date": ev["start"].strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": (ev["end"] or ev["start"]).strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": ev["tz_name"],
        "all_day": False,
        "status": status,
        "website": ev["url"],
        "categories": [EVENT_CATEGORY],
        "tags": ev["tags"],
    }
    if venue_id:
        body["venue"] = [venue_id]
    return api.request("POST", "/events", body=body)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path", nargs="?", help="manually-exported CSV to use instead of fetching live")
    parser.add_argument("--site", default=DEFAULT_SITE, help="WordPress site base URL")
    parser.add_argument("--publish", action="store_true", help="create as published (default: draft)")
    args = parser.parse_args()

    username = os.environ.get("TEC_WP_USERNAME")
    app_password = os.environ.get("TEC_WP_APP_PASSWORD")
    if not username or not app_password:
        print("Set TEC_WP_USERNAME and TEC_WP_APP_PASSWORD environment variables first.", file=sys.stderr)
        print("(WordPress admin -> Users -> your profile -> Application Passwords)", file=sys.stderr)
        sys.exit(1)

    status = "publish" if args.publish else "draft"
    api = Api(args.site, username, app_password)

    events = load_events(args.csv_path)
    print(f"Loaded {len(events)} events from vTools.", file=sys.stderr)

    print("Checking/creating venues...", file=sys.stderr)
    venue_ids = ensure_venues(api, events, status)

    print("Checking existing events...", file=sys.stderr)
    existing = existing_event_keys(api)

    created, skipped = 0, 0
    for ev in events:
        key = (ev["title"].strip().lower(), ev["start"].strftime("%Y-%m-%d %H:%M:%S"))
        if key in existing:
            skipped += 1
            continue
        venue_id = venue_ids.get(venue_name_for(ev))
        result = create_event(api, ev, venue_id, status)
        print(f"  created event: {ev['title']} (id {result['id']}, {status})", file=sys.stderr)
        created += 1
        time.sleep(0.2)

    print(f"\nDone. {created} events created as {status}, {skipped} already existed and were skipped.", file=sys.stderr)
    if status == "draft":
        print("Review them in WordPress admin, then re-run with --publish once you're happy.", file=sys.stderr)


if __name__ == "__main__":
    main()
