# Keeping the Past Events archive current

The site has a **Past Events** page
(https://r3.ieee.org/huntsville-computer/past-events/) that's a plain,
chronological write-up of chapter history — separate from the
website's built-in Events section, which only ever shows *upcoming*
events (see `learnings.md`). Anything that's already happened needs to
be added to the Past Events page manually; it won't appear there on its
own.

As of July 2026, generating the HTML for this page is automated via
`scripts/vtools_events_to_html.py` (see "Automating this with a script"
below) — it takes a vTools CSV export and produces ready-to-paste HTML,
including a link to each event's own vTools page. There's still no way
to auto-*publish* it (WordPress editing is manual), so this doc still
describes the full manual process.

## Where the historical data comes from

Two sources:

1. **The old chapter website** (pre-migration, `ewh.ieee.org`) — a
   handful of very old (2006-era) events that predate vTools. These are
   already captured in `migration-guide.md` and on the Past Events page;
   there's nothing left to pull for this source going forward.
2. **IEEE vTools** — the system of record for everything from ~2014
   onward. This chapter's vTools ID is **CH03037**.

## Pulling new events from vTools

1. Go to vTools' event search:
   https://events.vtools.ieee.org/events/search/advanced?search=CH03037
   (adjust the date range / paging as needed — the search UI supports
   filtering by date).
2. Export the results to CSV (vTools has an export option on the search
   results page). The export includes, per event: title, date/time,
   location, format (in-person/virtual/hybrid), attendee counts,
   contact email, co-sponsors, and tags.
3. For each new event since the last update, pull out: **title, date,
   time, location, format, and contact email** — that's the level of
   detail already used for every entry on the Past Events page.
4. Edit the Past Events page in WordPress (`Pages → Past Events →
   Backend Editor → Code`), and add a new entry under the correct
   `<h2>YEAR</h2>` section (create a new year heading if needed),
   following the existing format:

   ```html
   <p><strong>Event Title</strong><br>
   Month Day, Year | Start – End Time (Timezone)<br>
   Location / format / other relevant details</p>
   ```

5. Keep entries in chronological order within each year, and keep years
   in descending order (newest year at the top) to match the existing
   page structure.

## A note on the CSV export format

The vTools CSV export has a lot of columns most of which aren't needed
for the archive (internal IDs, lat/long, registration caps, etc.) The
ones actually used to build each entry are: `Event Title`, `Event Date`,
`End Time`, `Tm Zone Info`, `Event Location`, `Location Type`,
`Contact Email`, `Cosponsor Name`, and `Tags`. If you're processing a
large export by hand, it's easiest to open it in a spreadsheet, hide the
irrelevant columns, and sort by `Event Date`.

## Automating this with a script

`scripts/vtools_events_to_html.py` takes a vTools CSV export and prints
the full Past Events HTML: an "Upcoming Events (vTools)" / "All Events
(vTools)" links line, then each event grouped by `<h2>YEAR</h2>`, title
linked to its own vTools page, in the same format used above.

```
python3 scripts/vtools_events_to_html.py path/to/export.csv > past_events.html
```

Notes:

- **Per-event links** use `https://events.vtools.ieee.org/m/<Id>` —
  confirmed working July 2026 by checking it resolves to the correct
  event. There's no documented public API endpoint for pulling a single
  chapter's events without a pre-arranged "custom feed" (see the
  Events API docs at `/api/doc/events` — `spoid`-based queries require a
  named feed that IEEE staff have to set up first), so the CSV export +
  this script remains the practical path.
- **Timezones matter**: the CSV's `Event Date`/`End Time` columns are in
  UTC. The script converts them to each event's own `Tm Zone Info` zone
  before printing — don't print the raw CSV timestamp next to the
  timezone name, it'll be off by several hours (caught this the hard
  way generating the first version).
- **Legacy Report duplicates**: some events appear twice in a CSV export
  — once under their real title, once again prefixed
  `[Legacy Report]` with the same date. The script treats these as the
  same event and dedupes to whichever has the non-legacy title.
- **2006-era events aren't in vTools** and won't appear in the script's
  output — they stay as the hand-written entries already in
  `migration-guide.md` / the top of the Past Events page.
- Running this against a full CSV export may surface events that were
  missed in earlier manual passes (e.g. this surfaced 2010, 2013,
  2015–2016, and a couple of 2018–2019 events not previously on the
  page) — review the output for events not yet published before pasting.
