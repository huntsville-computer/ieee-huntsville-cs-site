# Keeping the Past Events archive current

The site has a **Past Events** page
(https://r3.ieee.org/huntsville-computer/past-events/) that's a plain,
chronological write-up of chapter history — separate from the
website's built-in Events section, which only ever shows *upcoming*
events (see `learnings.md`). Anything that's already happened needs to
be added to the Past Events page manually; it won't appear there on its
own.

There is no automated pipeline for this today — no script, no API
integration. This doc describes the manual process we used during the
2026 migration so it's repeatable.

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

## Ideas for automating this later

This is a good candidate for a small script (Python or similar) living
in this repo that takes a vTools CSV export and generates the HTML
snippet to paste into the Past Events page, removing the manual
formatting step. Nothing like that exists yet as of this writing — if
you build one, add it to this repo and update this doc.
