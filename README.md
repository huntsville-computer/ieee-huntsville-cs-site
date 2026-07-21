# IEEE Huntsville Computer Society Chapter — Website Ops

This repo is the home for everything related to running and maintaining the
IEEE Huntsville Computer Society Chapter's website. It's not the website's
source code (the site is a self-hosted WordPress install on WP Engine) — it's
the operational knowledge, migration history, and how-to docs so that
whoever's running the chapter's web presence next doesn't have to
rediscover any of this from scratch.

## Quick links

- **Live site:** https://r3.ieee.org/huntsville-computer/
- **WordPress admin:** https://r3.ieee.org/huntsville-computer/wp-admin/
- **IEEE vTools (event management):** https://vtools.ieee.org/
- **This chapter's vTools event search:** https://events.vtools.ieee.org/events/search/advanced?search=CH03037
- **GitHub org:** https://github.com/huntsville-computer

## What's in this repo

| Path | What it is |
|---|---|
| [`docs/getting-started.md`](docs/getting-started.md) | Onboarding doc for a new Chapter Chair / officer / volunteer: how to get access to the website, vTools, and this repo. |
| [`docs/learnings.md`](docs/learnings.md) | Practical notes on how the WordPress site is actually put together (WPBakery shortcodes, the Team Members plugin, the nav menu, WP Engine caching) — read this before making edits so you don't break something. |
| [`docs/vtools-event-import.md`](docs/vtools-event-import.md) | How to pull new/past events out of vTools and get them onto the site's Past Events archive page. |
| [`docs/old-site-past-events.md`](docs/old-site-past-events.md) | The chapter's pre-vTools (2006) past events, preserved from the old `ewh.ieee.org` site. |
| [`scripts/vtools_events.py`](scripts/vtools_events.py) | Shared code that fetches this chapter's event list live from vTools (or from a manually-exported CSV as a fallback). Used by both scripts below. |
| [`scripts/vtools_events_to_html.py`](scripts/vtools_events_to_html.py) | Generates the Past Events page HTML, with a link to each event's own vTools page. |
| [`scripts/vtools_events_to_tec_csv.py`](scripts/vtools_events_to_tec_csv.py) | Generates `events.csv`/`venues.csv` for importing into **The Events Calendar**, the plugin that actually powers the site's `/events/` page (see `docs/learnings.md`). **CSV upload is currently blocked on this site** — see `docs/vtools-event-import.md`. |
| [`scripts/vtools_events_to_tec_api.py`](scripts/vtools_events_to_tec_api.py) | Same result as the CSV script, but via The Events Calendar's REST API instead of a file upload — this is the one that actually works here. |
| [`generated/`](generated/) | Dated snapshots of the scripts' output, for reference. |

## Status (as of July 2026)

The site migration from the old `ewh.ieee.org/r3/huntsville/cs/` site is
functionally complete: placeholder pages/content removed, real officer
info published, a Past Events archive built from historical records, and
navigation cleaned up. The old site is still live and will redirect once
the chapter notifies IEEE's webmaster, Ray Umali, at
**ewh-webmaster@ieee.org** (reference ticket **#260415-000712**).

Still open: adding real upcoming meeting info to the homepage once one is
scheduled, and keeping the Past Events archive current going forward (see
`docs/vtools-event-import.md`).
