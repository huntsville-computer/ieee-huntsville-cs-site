# Getting Started — for new Chapter Chairs, officers, and volunteers

Welcome to running the IEEE Huntsville Computer Society Chapter's web
presence. There are three separate systems you'll likely need access to,
and they each work differently. This doc walks through what each one is
for and how to get in.

## 1. The chapter website (WordPress)

- **URL:** https://r3.ieee.org/huntsville-computer/
- **Admin login:** https://r3.ieee.org/huntsville-computer/wp-admin/
- **Hosting:** WP Engine (managed WordPress hosting). The site itself is
  provisioned through IEEE's Region 3 web hosting program, not a personal
  or chapter-owned WP Engine account.

To get an admin account, ask the outgoing Chapter Chair or Webmaster to
add you as a WordPress user (Users → Add New in the wp-admin sidebar), or
if you're the first officer standing up the site, contact IEEE web
hosting support (see `migration-guide.md` for the "Helpful WordPress
Resources" links) to get provisioned.

**Before editing anything**, read [`learnings.md`](learnings.md) — the
site uses WPBakery Page Builder shortcodes on some pages (notably the
homepage), and editing the raw shortcode carelessly can break the layout.

There is currently no login access to the WP Engine hosting portal
(my.wpengine.com) documented anywhere in this repo — if you hit a
site-wide caching issue (edits not showing up for visitors) and need to
manually purge the cache, you'll need to track down who has that portal
login, likely through IEEE's web hosting team.

## 2. IEEE vTools (event management)

- **URL:** https://vtools.ieee.org/
- vTools is IEEE's official system of record for scheduling meetings,
  tracking attendance, and reporting chapter activity to IEEE. It's
  separate from the website — posting a meeting in vTools does **not**
  automatically post it to the WordPress site.
- Access is tied to your IEEE membership number and your chapter officer
  role in IEEE's records (vTools syncs officer roles from IEEE's national
  database, so you may need to confirm your chapter officer position is
  up to date in IEEE's system before vTools gives you edit rights for
  this chapter).
- This chapter's vTools ID is **CH03037** — useful for searching event
  history (see the link in the main README, or `vtools-event-import.md`
  for how to pull events into the website).

## 3. This GitHub repo / org

- **Org:** https://github.com/huntsville-computer
- This repo isn't the website's source code — WordPress lives entirely on
  WP Engine's servers, there's nothing here to "deploy." This repo is
  documentation: migration history, how the site is built, and
  step-by-step guides like this one.
- Ask whoever currently maintains the GitHub org to add you as a
  collaborator/member. If you're taking over as Chapter Chair and no one
  has org access anymore, GitHub support can help recover org ownership
  if you can demonstrate chapter affiliation.

## Suggested first steps for a new officer

1. Get WordPress admin access and log in — just look around, don't edit
   anything yet.
2. Read `learnings.md` in this repo so you understand how the homepage
   and Team Members widget work before touching them.
3. Get vTools access and confirm you can see this chapter's event history
   at the CH03037 search link.
4. Get added to the GitHub org so you can update this repo as you learn
   things (please do — future-you and future-officers will thank you).
