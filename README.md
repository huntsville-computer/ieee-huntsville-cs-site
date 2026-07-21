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
| [`migration-guide.md`](migration-guide.md) | The original 2026 WordPress migration guide (old ewh.ieee.org site → r3.ieee.org). Kept as a historical record of what the site looked like pre-migration and what got fixed. |
| [`docs/getting-started.md`](docs/getting-started.md) | Onboarding doc for a new Chapter Chair / officer / volunteer: how to get access to the website, vTools, and this repo. |
| [`docs/learnings.md`](docs/learnings.md) | Practical notes on how the WordPress site is actually put together (WPBakery shortcodes, the Team Members plugin, the nav menu, WP Engine caching) — read this before making edits so you don't break something. |
| [`docs/vtools-event-import.md`](docs/vtools-event-import.md) | How to pull new/past events out of vTools and get them onto the site's Past Events archive page. |

## Status (as of July 2026)

The site migration from the old `ewh.ieee.org/r3/huntsville/cs/` site is
functionally complete: placeholder pages/content removed, real officer
info published, a Past Events archive built from historical records, and
navigation cleaned up. The old site is still live and will redirect once
the chapter notifies IEEE's webmaster (see `migration-guide.md` for the
ticket reference).

Still open: adding real upcoming meeting info to the homepage once one is
scheduled, and keeping the Past Events archive current going forward (see
`docs/vtools-event-import.md`).
