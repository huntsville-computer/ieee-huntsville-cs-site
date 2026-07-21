# Keeping the Past Events archive current

The site has a **Past Events** page
(https://r3.ieee.org/huntsville-computer/past-events/) that's a plain,
chronological write-up of chapter history — separate from the
website's built-in Events section, which only ever shows *upcoming*
events (see `learnings.md`). Anything that's already happened needs to
be added to the Past Events page manually; it won't appear there on its
own.

`scripts/vtools_events_to_html.py` generates the whole page's HTML in
one shot: it fetches this chapter's event list **live from vTools** (no
manual CSV export needed) *and* merges in the pre-vTools 2006 events
from [`old-site-past-events.md`](old-site-past-events.md), so there's
one combined, ready-to-paste block instead of juggling two sources.
There's still no way to auto-*publish* it (WordPress editing is
manual), so you paste the output in yourself.

(We also tried importing events as native entries into The Events
Calendar plugin — first via its CSV importer, which this site's
WordPress rejects with "Sorry, you are not allowed to upload this file
type"; then via its REST API directly, which worked but required a
WordPress Application Password that turned out to be disabled here too.
Abandoned both in favor of this simpler, already-working approach.)

## Where the historical data comes from

Two sources:

1. **The old chapter website** (pre-migration, `ewh.ieee.org`) — a
   handful of very old (2006-era) events that predate vTools. Captured
   in [`old-site-past-events.md`](old-site-past-events.md), which
   `vtools_events_to_html.py` reads and merges in automatically. If you
   ever turn up more pre-2014 events, add them there in the same
   `**Title**` / `- Date: ...` / `- Speaker: ...` format.
2. **IEEE vTools** — the system of record for everything from ~2014
   onward. This chapter's vTools ID is **CH03037**.

## Generating the page

```
python3 scripts/vtools_events_to_html.py > past_events.html
```

With no arguments, it hits vTools live (takes ~10-15 seconds — see "How
it fetches live data" below). It also accepts a manually-exported vTools
CSV path as a fallback (e.g. if vtools.ieee.org is unreachable):

```
python3 scripts/vtools_events_to_html.py path/to/export.csv > past_events.html
```

Then paste the output into WordPress: `Pages → Past Events → Backend
Editor → Code`, replacing the page's content. Keep entries in
chronological order within each year, oldest year at the top (matching
the page's existing structure) — the script already does this for you.

### How it fetches live data

The live-fetch logic lives in `scripts/vtools_events.py`. No login or
API key needed — two requests do all the work:

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
- Running this may surface events that were missed in earlier manual
  passes (e.g. this surfaced 2010, 2013, 2015–2016, and a couple of
  2018–2019 events not previously on the page) — review the output for
  events not yet published before pasting.
