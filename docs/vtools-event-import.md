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
below) — it fetches this chapter's event list **live from vTools**
(no manual CSV export needed) and produces ready-to-paste HTML,
including a link to each event's own vTools page. There's still no way
to auto-*publish* it (WordPress editing is manual), so this doc still
describes the manual publishing step, and the CSV-export path remains
as a fallback (e.g. if vtools.ieee.org is unreachable).

There are two more scripts for importing the same event data into
**The Events Calendar** — the plugin that actually runs the site's
`/events/` page (see `learnings.md`):

- `scripts/vtools_events_to_tec_csv.py` generates a CSV for Events →
  Import → CSV. **This site's WordPress rejects that upload** ("Sorry,
  you are not allowed to upload this file type") — a known WordPress/WP
  Engine/security-plugin issue unrelated to the file's content (see
  "Importing into The Events Calendar" below for what we tried). Kept
  around in case that gets fixed or you're pointing this at a
  different, unaffected site.
- `scripts/vtools_events_to_tec_api.py` — **the one that actually
  works here** — creates the same events/venues directly via the
  plugin's REST API instead of uploading a file at all, sidestepping
  the upload block entirely. See "Importing via the REST API" below.

## Where the historical data comes from

Two sources:

1. **The old chapter website** (pre-migration, `ewh.ieee.org`) — a
   handful of very old (2006-era) events that predate vTools. These are
   already captured in [`old-site-past-events.md`](old-site-past-events.md)
   and on the Past Events page; there's nothing left to pull for this
   source going forward.
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

`scripts/vtools_events_to_html.py` prints the full Past Events HTML: an
"Upcoming Events (vTools)" / "All Events (vTools)" links line, then each
event grouped by `<h2>YEAR</h2>`, title linked to its own vTools page, in
the same format used above.

```
python3 scripts/vtools_events_to_html.py > past_events.html
```

With no arguments, it hits vTools live (takes ~10-15 seconds — see "How
it fetches live data" below). It also accepts a manually-exported CSV
path as a fallback:

```
python3 scripts/vtools_events_to_html.py path/to/export.csv > past_events.html
```

### How it fetches live data

The live-fetch logic lives in `scripts/vtools_events.py`, shared by both
scripts on this page. No login or API key needed — two requests do all
the work:

1. This chapter's own search results, as CSV, gives the full list of
   event IDs (this is the same URL as the "All Events" link, with
   `.csv` inserted before the query string):
   `https://events.vtools.ieee.org/events/search.csv?_sub=true&q=&ou=CH03037+-+Huntsville+Section+Chapter%2C+C16&d=All&commit=Search`
2. For each ID, the documented Events API
   (`/api/doc/events`) supports a single-event lookup:
   `https://events.vtools.ieee.org/RST/events/api/public/v8/events/list?id=<id>`,
   which returns full structured data — start/end time, timezone, tags,
   attendance, cosponsor, contact, and the event's own public link
   (`https://events.vtools.ieee.org/m/<id>`).

**We tried `spoid` first and it doesn't work for this** — it looked like
the natural way to query "all events for CH03037" directly, but it's
only a sub-filter *inside* an existing named feed scoped broader than a
single chapter (a region, society, or section-group), e.g.
`/feeds/v8/c/<feed-uid>?spoid=CH03037`. Passing it to the generic
events-list endpoint returns a 400 ("The 'spoid' parameter is a feed
sub-filter and can only be used with a named feed"), and getting a feed
UID requires asking IEEE vTools staff to set one up. Hence the two-step
CSV-list-then-per-id-lookup approach above.

Notes:

- **Per-event links** use `https://events.vtools.ieee.org/m/<Id>` —
  confirmed working July 2026, and also returned directly by the API's
  `link` field.
- **Timezones matter**: timestamps from both vTools sources are UTC.
  The script converts them to each event's own timezone before
  printing — don't print the raw timestamp next to the timezone name,
  it'll be off by several hours (caught this the hard way generating
  the first version).
- **Legacy Report duplicates**: some events appear twice — once under
  their real title, once again prefixed `[Legacy Report]` with the same
  date/time. The script dedupes these to whichever has the non-legacy
  title, regardless of which one it encounters first (an earlier version
  of this script had a bug where it would keep whichever was fetched
  first — fixed by tracking "is this a legacy record" as its own field
  instead of re-deriving it from the (already-stripped) stored title).
- **Tags look slightly different** between the two data sources: the
  live API returns tags as a pre-split, hashtagged list (e.g. `#IEEE
  #Huntsville #Section`), while a manually-exported CSV's `Tags` column
  preserves the original comma-separated phrasing (e.g. `IEEE, Huntsville
  Section`). Cosmetic only.
- **2006-era events aren't in vTools** and won't appear in the script's
  output — they stay as the hand-written entries in
  [`old-site-past-events.md`](old-site-past-events.md) / the top of the
  Past Events page.
- Running this may surface events that were missed in earlier manual
  passes (e.g. this surfaced 2010, 2013, 2015–2016, and a couple of
  2018–2019 events not previously on the page) — review the output for
  events not yet published before pasting.

## Importing into The Events Calendar

`scripts/vtools_events_to_tec_csv.py` generates two CSV files, in the
format documented at
https://docs.nexcess.com/software/the-events-calendar/import-events-csv/,
for importing this chapter's vTools events as native Event Calendar
entries (rather than a plain-text page):

```
python3 scripts/vtools_events_to_tec_csv.py --out-dir /tmp/tec_export
```

This writes `events.csv` and `venues.csv`. **Import venues.csv first**,
then events.csv (WordPress admin: Events → Import → CSV, pick the
matching import type for each file) — The Events Calendar links an
event to a venue by matching "Event Venue Name" to an existing Venue
post's exact name, so the venue has to exist first.

**As of July 2026, uploading either CSV to this site fails** with
"Sorry, you are not allowed to upload this file type" — this is a known
WordPress/hosting-level issue (a MIME-type sniffing mismatch, a security
plugin, or a WP Engine upload restriction — not something wrong with the
generated file itself) and not specific to The Events Calendar. Things
worth trying if you hit this again: re-saving the CSV through a
spreadsheet app before uploading, testing with a tiny dummy CSV to see
if *all* CSV uploads are blocked, checking for a security plugin's
upload-restriction setting, or asking WP Engine support directly. None
of that resolved it for us, which is why `vtools_events_to_tec_api.py`
(below) exists — it doesn't upload a file at all.

Notes:

- **Venue Name is built from the event's address** (street address +
  city), since vTools gives us an address, not a human venue name like
  "GigaParts, Inc." Events sharing an address correctly share one venue
  — but the source data has some near-duplicate addresses (typos like
  "Permeter" vs "Parkway", inconsistent suite numbers, a trailing ", AL"
  on some entries) that will still produce separate, near-identical
  Venue posts. Worth a manual cleanup pass in WordPress after import if
  that bothers you; not something the script tries to fuzzy-match.
- **Event Category** is hardcoded to a single fixed value
  (`IEEE Computer Society`) for every event, since this whole feed is
  already scoped to one chapter. Change the `EVENT_CATEGORY` constant at
  the top of the script if you want something else.
- **Venue Country** defaults to "United States" for anything not marked
  virtual. vTools' API exposes country as a numeric id rather than a
  name; every event in this chapter's history has in fact been
  US-based, so hardcoding was simpler than resolving that id.
- **We don't know yet whether past events actually display** once
  imported into this plugin — see the note in `learnings.md`. Untested
  as of this writing.
- `--out-dir` defaults to the current directory; it also accepts a
  manually-exported CSV path as a positional argument (same fallback as
  `vtools_events_to_html.py`), though that path won't have event
  descriptions (not present in that export format).

## Importing via the REST API

Since CSV upload is blocked on this site (see above),
`scripts/vtools_events_to_tec_api.py` creates the same events and venues
by talking to The Events Calendar's own REST API directly — no file
upload involved, so the block doesn't apply. Confirmed the API is live
and reachable at `https://r3.ieee.org/huntsville-computer/wp-json/tribe/events/v1/`
(no login needed just to browse the route list — try it in a browser).

You'll need a WordPress **Application Password** (WordPress admin →
Users → your profile → Application Passwords → give it a name like
"vtools-import" → Add). This is a WordPress-native feature (5.6+)
designed exactly for this — a per-user, revocable credential for API
access that isn't your login password. Then:

```
export TEC_WP_USERNAME="your-wp-username"
export TEC_WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"
python3 scripts/vtools_events_to_tec_api.py
```

**Never commit these credentials to this repo** — they're read from
environment variables, not arguments, so they don't end up in shell
history files as easily either.

By default this creates everything as **drafts** — nothing goes live on
the public site until you review and publish from wp-admin yourself.
Once you're happy, re-run with `--publish` to create things published
directly (or just publish the drafts by hand in wp-admin).

Notes:

- **Confirmed working against the live site's schema** — the exact
  field names/types below came from querying
  `/wp-json/tribe/events/v1/` and `/wp-json/tribe/events/v1/doc`
  directly (both public, no auth needed), not guessed from generic
  plugin docs.
- **A 403 with "error code: 1010" means Cloudflare/WP Engine blocked
  the request as a bot**, not an auth failure — this happened during
  testing because Python's default `urllib` User-Agent gets flagged.
  The script sends a browser-like User-Agent to avoid this; if you see
  this error anyway, something about the request changed.
- **A 401 `rest_forbidden` means bad credentials** — check the
  Application Password was copied correctly (WordPress shows it once,
  with spaces, when you create it — include the spaces).
- **Re-running has one confirmed gap**: it checks for existing venues/
  events first so it won't duplicate already-*published* items, but
  this site's `GET /venues` and `GET /events` only accept
  `status=publish` — even `status=draft` alone gets rejected with a 400
  (confirmed by testing, not just an auth artifact). There's no way to
  query for existing drafts through this API. So: don't run this twice
  while a previous run's drafts are still sitting unpublished, or
  you'll get duplicates. Publish (or delete) them first.
- **Category** is hardcoded to `IEEE Computer Society` for every event,
  same as the CSV script — change `EVENT_CATEGORY` at the top of the
  script if you want something else.
- **Venue matching, address quirks, and the "United States" default**
  work the same way as `vtools_events_to_tec_csv.py` above — same
  near-duplicate-address caveat applies.
- **We still don't know whether past events display on the front end**
  once created this way — see the note in `learnings.md`. If you find
  out, update that note.
