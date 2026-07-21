# How this site is actually built — notes from the 2026 migration

This site runs on a shared IEEE WordPress theme/template ("IEEE Sites
Theme (Official)") on WP Engine hosting, with WPBakery Page Builder for
layout. It looks like a normal WordPress site from the Pages/Posts list,
but a few pages (especially the homepage) are built from raw page-builder
shortcodes, not plain content. Below is what we learned the hard way
during the 2026 migration off the old `ewh.ieee.org` site.

## The homepage is not a normal page

The front page (`Pages → Home — Front Page`) is built entirely out of
WPBakery shortcodes: a hero slideshow (`[ieee_slideshow]` /
`[ieee_slide ...]`), a "Featured"/"News" post list (`[ieee_posts ...]`), a
promoted banner (`[ieee_promoted ...]`), the Chapter Members widget
(`[tmm name="chapter-members"]`), a Membership call-to-action, and an
events list (`[ieee_events ...]`).

To edit it precisely, use **Backend Editor → Code** (not the visual
WPBakery drag-and-drop builder) — this shows the raw shortcode text in a
plain `<textarea>`. This is the only reliable way to make small text
changes (like swapping a placeholder date) without the visual builder
silently restructuring something.

**When editing that textarea:** don't trust word-boundary/select-all
keyboard shortcuts (`ctrl+a`, `ctrl+Home`, `ctrl+shift+End`,
`ctrl+shift+Right`) — they were unreliable in browser automation testing
and either did nothing or wildly overshot. What worked reliably: click at
the start of the text, `Home`, then shift-click at the end position,
`shift+End`, and — critically — zoom in on the exact character before
typing to confirm the selection boundary doesn't include or exclude a
quote/bracket character. Getting this wrong breaks shortcode syntax
(mismatched quotes = the whole block silently fails to render). If you
do corrupt it, don't save — reload the page to discard.

## The "Chapter Members" widget is a separate plugin

The officer/member cards on the homepage come from the **Team Members**
plugin (a custom post type, not a normal widget), edited from its own
admin screen, referenced via `[tmm name="chapter-members"]`. Its editor
is a repeater UI (add/remove member blocks). We found that editing an
existing member block's fields and saving could wipe the *entire* team
(all members disappeared) rather than updating just that one — root cause
unclear. Safer approach: if you need to replace who's listed, delete
everything and use "Add a member" to create fresh entries rather than
editing in place.

## The nav menu doesn't auto-clean itself

If you trash a Page that's linked from the Primary Navigation menu,
WordPress does **not** remove the menu item — it just flags it
`(Invalid)` and shows a banner. You have to go to
`Appearance → Menus` and manually remove each stale item. Also: new pages
you create are **not** automatically added to the nav menu — you have to
add them yourself (Pages panel → check the page → "Add to Menu" → Save
Menu), or they'll be published but effectively undiscoverable.

## WP Engine caches pages for logged-out visitors

WordPress admin (logged-in) views always show live, current content —
but public/logged-out visitors are served from WP Engine's page cache,
which can be significantly stale (we saw it serve a snapshot from
*before* same-day edits). There is no cache-purge control anywhere in
this WordPress admin (checked Settings, Tools, Plugins, and the admin
toolbar) — none of the 80 installed plugins is a WP Engine cache-control
plugin. Purging manually requires the **WP Engine User Portal**
(my.wpengine.com), which is a separate login from WordPress itself. If
you make a change and it's not showing up for visitors, this is almost
certainly why — check with a logged-out/incognito view (or wait; it does
eventually clear on its own).

## The Events section only shows *upcoming* events (by default)

Both the homepage sidebar events widget and the `/events/` page (from
The Events Calendar plugin) only display future-dated events by default.
If there are none, they show nothing (or "There are no upcoming events")
— this is normal, not a bug.

There is a way to get past events *into* this same plugin now —
`scripts/vtools_events_to_tec_csv.py` generates a CSV importable via
Events → Import → CSV (see `vtools-event-import.md`) — but we haven't
verified whether/how past events display on the front end once imported
(The Events Calendar Pro may have a "past events" list view that isn't
linked from the default nav; untested as of this writing). Until that's
confirmed, the plain-HTML Past Events page (built by
`vtools_events_to_html.py`) remains the reliable way to show chapter
history publicly.

## Plugin landscape

The site has ~80 installed plugins (mostly inactive), inherited from the
IEEE hosting template. Notably active/relevant ones: **WPBakery Page
Builder** (page layout), **Team Members** (the officer widget),
**The Events Calendar** + **Pro** (the `/events/` page and upcoming-event
widgets), **Yoast SEO**, **WP Statistics**. Most of the other 70-odd
plugins are inactive and installed by default with the IEEE template —
don't assume something is in use just because it's installed.
