# Hidden Gem Movies — the list site

Browsable front-end for the 581 hidden gem movies found in the
[streaming-hidden-gems](https://github.com/michaelnocito/streaming-hidden-gems)
SQL analysis. Companion to
[steam-hidden-gems-list](https://github.com/michaelnocito/steam-hidden-gems-list),
same format and design.

**Live:** https://michaelnocito.github.io/streaming-hidden-gems-list/

## What it is

- `index.html` — the whole site (no build step). Card grid of all 581 movies,
  ranked by rating, with search and filters (Documentaries / Classics / 2020s).
- `movies.json` — the data, exported straight from the analysis database
  (IMDb snapshot 2026-07-12). Top picks carry a short pitch; the rest are the
  raw results.
- Every card links to its IMDb page and has a 💎 Gem / 😐 Meh vote widget.

## Voting

Votes are shared live via the same Supabase backend as the Steam list site
(one `gem_votes` table serves both; movie keys are "Title (Year)" so they
cannot collide with game names). The anon key in `index.html` is public by
design; row-level security limits it to inserting a vote and reading
aggregate counts. See `SETUP.md`.

## How the list was made

The methodology, the teaching-commented SQL, and the data-quality stories
(a quote character that silently ate 256,000 rows, IMDb's fake `\N` nulls)
live in the analysis repo:
https://github.com/michaelnocito/streaming-hidden-gems
