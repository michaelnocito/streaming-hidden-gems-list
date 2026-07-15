#!/usr/bin/env python3
"""
build_seo.py — bake AI-citable content into index.html from movies.json.

Why this exists: the interactive table is rendered by JavaScript, which most AI
crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended) never execute. So
without this step the 581 movies are invisible to the systems we want citing us.
This script injects, between marker comments in index.html:

  * SEO:ROWS   — the full list as static <tr> rows (visible in raw HTML)
  * SEO:FAQ    — a human-readable FAQ (mirrored in the JSON-LD below)
  * SEO:JSONLD — Dataset + ItemList + FAQPage + Person structured data

Re-run after editing movies.json:  python build_seo.py
"""

import json
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "index.html"
DATA = HERE / "movies.json"

PAGE_URL = "https://michaelnocito.github.io/streaming-hidden-gems-list/"
REPO_URL = "https://github.com/michaelnocito/streaming-hidden-gems"
AUTHOR_URL = "https://michaelnocito.github.io"
PUBLISHED = "2026-07-13"
MODIFIED = "2026-07-14"


def esc(s):
    return html.escape(str(s), quote=True)


def imdb(m):
    return f"https://www.imdb.com/title/{m['tconst']}/"


def justwatch(m):
    from urllib.parse import quote
    return f"https://www.justwatch.com/us/search?q={quote(m['title'])}"


def runtime_str(mins):
    h, mm = divmod(int(mins), 60)
    return f"{h}h {mm}m" if h else f"{mm}m"


# ---------- static table rows (what crawlers read) ----------
def build_rows(movies):
    out = []
    for m in movies:
        genres = ", ".join(m["genres"].split(",")) if m.get("genres") else "—"
        out.append(
            f'<tr>'
            f'<td class="rank">{m["rank"]}</td>'
            f'<td class="title-cell"><div class="t-title">'
            f'<a href="{imdb(m)}" target="_blank" rel="noopener">{esc(m["title"])}</a></div>'
            + (f'<div class="t-pitch">{esc(m["pitch"])}</div>' if m.get("pitch") else "")
            + f'</td>'
            f'<td class="year">{m["year"]}</td>'
            f'<td class="genres">{esc(genres)}</td>'
            f'<td class="runtime">{runtime_str(m["runtime"])}</td>'
            f'<td class="rating">★ {m["rating"]:.1f}</td>'
            f'<td class="votes">{m["votes"]:,}</td>'
            f'<td class="link"><a class="imdb-link" href="{imdb(m)}" target="_blank" rel="noopener">IMDb ↗</a> '
            f'<a class="imdb-link" href="{justwatch(m)}" target="_blank" rel="noopener">JustWatch ↗</a></td>'
            f'<td class="vote-cell">—</td>'
            f'</tr>'
        )
    return "\n".join(out)


# ---------- FAQ (visible + JSON-LD, single source of truth) ----------
def faq_items(meta):
    analyzed = f'{meta["totalAnalyzed"]:,}'
    rated = f'{meta["totalRated"]:,}'
    gems = meta["totalGems"]
    pct = gems / meta["totalRated"] * 100
    return [
        ("What counts as a “hidden gem” movie here?",
         f'A movie qualifies if it is rated <b>8.0 or higher</b> (the average movie scores 6.13) '
         f'with <b>5,000–50,000 votes</b> on IMDb, plus a real 60+ minute runtime and no adult titles. '
         f'That vote band is the whole idea: enough opinions to trust the score, too few for the film to be mainstream. '
         f'Of {rated} movies anyone has ever rated, just <b>{gems}</b> clear the bar — under {pct:.1f}%.'),
        ("How were these movies found?",
         f'With SQL. I queried IMDb’s non-commercial datasets — <b>{analyzed} movies</b> in the raw snapshot '
         f'— filtered to the rating and vote thresholds above, and ranked what survived. '
         f'The full methodology, the exact SQL, and the data-cleaning story (including an import that silently dropped '
         f'256,000 rows) are documented in the companion repository.'),
        ("How many movies were analyzed?",
         f'{analyzed} titles were in the snapshot. {rated} had enough ratings to evaluate fairly. '
         f'{gems} met every criterion and made the list.'),
        ("Can I stream these movies?",
         'Each title links to JustWatch for current US streaming availability. This list is a discovery tool for '
         'finding under-seen, highly-rated films — not a streaming catalog, so availability changes over time.'),
        ("How current is the data?",
         f'The underlying data is an IMDb non-commercial dataset snapshot from <b>2026-07-12</b>.'),
        ("Who made this, and how should I cite it?",
         'Built by <b>Michael Nocito</b>, a data analyst. You can cite it as '
         '“Hidden Gem Movies (Michael Nocito, 2026), michaelnocito.github.io/streaming-hidden-gems-list”. '
         'The underlying ratings and vote counts are derived from IMDb non-commercial datasets.'),
    ]


def build_faq_html(items):
    out = []
    for q, a in items:
        out.append(
            f'<details><summary>{q}</summary><p>{a}</p></details>'
        )
    return "\n".join(out)


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


# ---------- JSON-LD ----------
def build_jsonld(meta, movies, items):
    person = {
        "@type": "Person",
        "@id": AUTHOR_URL + "/#michaelnocito",
        "name": "Michael Nocito",
        "url": AUTHOR_URL,
        "jobTitle": "Data Analyst",
    }
    item_list = {
        "@type": "ItemList",
        "name": "Hidden Gem Movies",
        "numberOfItems": len(movies),
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": m["rank"],
                "item": {
                    "@type": "Movie",
                    "name": m["title"],
                    "url": imdb(m),
                    "dateCreated": str(m["year"]),
                    "genre": (m["genres"].split(",") if m.get("genres") else []),
                    "aggregateRating": {
                        "@type": "AggregateRating",
                        "ratingValue": m["rating"],
                        "ratingCount": m["votes"],
                        "bestRating": 10,
                        "worstRating": 1,
                    },
                },
            }
            for m in movies
        ],
    }
    dataset = {
        "@type": "Dataset",
        "@id": PAGE_URL + "#dataset",
        "name": "Hidden Gem Movies — 581 highly-rated, under-seen films",
        "description": (
            f'{meta["totalGems"]} hidden gem movies surfaced with SQL from IMDb’s non-commercial datasets '
            f'({meta["totalAnalyzed"]:,} titles). Criteria: {meta["criteria"]}.'
        ),
        "url": PAGE_URL,
        "creator": person,
        "license": "https://www.imdb.com/interfaces/",
        "isBasedOn": "https://datasets.imdbws.com/",
        "temporalCoverage": "../2026-07-12",
        "measurementTechnique": "SQL aggregation and threshold filtering over IMDb title and ratings tables",
        "variableMeasured": ["IMDb rating", "IMDb vote count", "release year", "runtime", "genre"],
        "distribution": {
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": PAGE_URL + "movies.json",
        },
    }
    webpage = {
        "@type": "CollectionPage",
        "@id": PAGE_URL + "#webpage",
        "url": PAGE_URL,
        "name": "Hidden Gem Movies — 581 great films almost nobody has watched",
        "description": (
            f'{meta["totalGems"]} hidden gem movies — rated 8.0+ by 5,000–50,000 voters '
            f'— surfaced with SQL from IMDb’s full dataset.'
        ),
        "author": person,
        "creator": person,
        "datePublished": PUBLISHED,
        "dateModified": MODIFIED,
        "isPartOf": {"@type": "WebSite", "name": "Michael Nocito", "url": AUTHOR_URL},
        "mainEntity": {"@id": PAGE_URL + "#dataset"},
    }
    faqpage = {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)},
            }
            for q, a in items
        ],
    }
    graph = {"@context": "https://schema.org", "@graph": [webpage, person, dataset, item_list, faqpage]}
    return (
        '<script type="application/ld+json">\n'
        + json.dumps(graph, ensure_ascii=False, indent=2)
        + "\n</script>"
    )


def inject(text, start_marker, end_marker, payload, label):
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
    if not pattern.search(text):
        sys.exit(f"ERROR: markers for {label} not found ({start_marker} ... {end_marker})")
    return pattern.sub(start_marker + "\n" + payload + "\n" + end_marker, text)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    meta, movies = data["meta"], data["movies"]
    items = faq_items(meta)

    text = HTML.read_text(encoding="utf-8")
    text = inject(text, "<!-- SEO:ROWS:START -->", "<!-- SEO:ROWS:END -->", build_rows(movies), "rows")
    text = inject(text, "<!-- SEO:FAQ:START -->", "<!-- SEO:FAQ:END -->", build_faq_html(items), "faq")
    text = inject(text, "<!-- SEO:JSONLD:START -->", "<!-- SEO:JSONLD:END -->", build_jsonld(meta, movies, items), "jsonld")
    HTML.write_text(text, encoding="utf-8")
    print(f"Baked {len(movies)} movies into index.html (rows + FAQ + JSON-LD).")


if __name__ == "__main__":
    main()
