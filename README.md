# WikiTheory: AI Wiki Mystery Prototype

This starter project has been turned into a small Streamlit mystery prototype
called WikiTheory. The player explores original wiki-style articles about
Mizukawa, follows internal links, saves pages to a watchlist, and submits
article contributions for editorial review.

## Run

1. Install dependencies:

```bash
pip install -r src/requirements.txt
```

2. Put your API key in `src/.env` or your shell environment:

```bash
OPENAI_API_KEY=your_api_key_here
```

Optional cheap-model override:

```bash
WIKI_MYSTERY_MODEL=gpt-4o-mini
```

3. Start the app:

```bash
streamlit run src/streamlit_basic.py
```

## How It Works

- `src/streamlit_basic.py` is the existing Streamlit entry point. It delegates to
  the playable WikiTheory app.
- `src/wiki_theory_app.py` renders the dense encyclopedia-style UI: compact top
  search, left navigation, small article tabs, a real section-based table of
  contents, article-specific right-side infoboxes, references, external links,
  categories, watchlist, contribution editor, inbox, and contributor profile.
- `src/wiki_theory.css` contains the reusable WikiTheory component styles:
  `WikiLayout`, `WikiHeader`, `WikiSidebar`, `WikiArticle`, `WikiInfobox`,
  `WikiTableOfContents`, `WikiReferences`, `WikiCategories`, and `WikiLink`.
- `src/wiki_mystery_engine.py` contains the seed articles, local JSON storage,
  link parsing, OpenAI generation calls, reference/category fallback logic, and
  contribution review calls.
- `src/wiki_mystery_canon.md` is the hidden fictional canon used by the article
  generator and contribution review system. The app does not show it directly.
- Generated pages are saved to `src/wiki_mystery_store/articles.json`, so a
  generated link opens the same structured article on later visits.
- Watched pages are saved to `src/wiki_mystery_store/watchlist.json`, so the
  watchlist persists after page reload.

The generation pipeline sends the hidden canon summary, clicked title, article
role, reveal budget, related article summaries, and the required JSON schema.
Articles are requested as structured JSON with `leadParagraphs`, typed
`sections`, `[[Internal Links]]`, article-specific infobox fields, fictional
references, external links, and categories.

## Article Format

WikiTheory articles now use a structured schema instead of a single body string:

```json
{
  "title": "Article title",
  "articleType": "case | person | place | organization | document | investigation | theory | timeline | record",
  "summary": "Short lead summary.",
  "leadParagraphs": ["paragraph 1", "paragraph 2"],
  "infobox": {
    "title": "Displayed infobox title",
    "imageCaption": "optional fictional caption",
    "fields": [
      { "label": "Date", "value": "17 September 1998" },
      { "label": "Location", "value": "[[Mizukawa Town]]" }
    ]
  },
  "sections": [
    { "heading": "Disappearance", "paragraphs": ["...", "..."] }
  ],
  "links": ["Emi Kuroda", "Mizukawa Town"],
  "references": ["fictional citation"],
  "externalLinks": ["fictional archive index"],
  "categories": ["1998 incidents"]
}
```

Legacy body-only articles are normalized into this structure at load time, so
previously generated pages still open.

## Article Generation

Before generating a red-link page, the engine plans the article role: case,
person, place, organization, document, investigation, theory, timeline, or
record. That role controls the length target, section headings, infobox fields,
and reveal budget. Overview pages summarize and link outward; narrower pages
carry the detailed weather, clinic, property, family, and archive records.

## Article Links

Article leads, sections, infobox values, and approved contributor revisions use
`[[Article Title]]` markup. The UI renders those as WikiTheory links:

- Blue links are seeded/existing articles.
- Purple links are locally saved generated articles.
- Red links are missing pages. Opening one calls the existing OpenAI generation
  flow, saves the result to JSON, and then treats that page as existing.

The top search box uses the same route, so searching for an unknown title also
generates and saves a new article.

## Watchlist

Article pages include a `Watch this page` / `Remove from watchlist` control.
The sidebar shows saved pages under `Watchlist`, plus a `View full watchlist`
link. The full watchlist page is styled like a wiki special page with page type,
last viewed time, status, and notes.

Articles also expose public `incompleteSections` metadata for contribution
targets. Canon answers stay hidden inside the review system and are never shown
in the article JSON rendered to the player.

## Contribution Loop

The old direct answer screen has been replaced with an in-universe workflow:

1. Open `Contribute an Article`.
2. Choose an incomplete or disputed article section.
3. Write an encyclopedia-style revision and reference related pages.
4. Submit for review.
5. WikiTheory editor personas respond in an `Editorial Discussion` thread.

The review call sends only the target section metadata, hidden canon summary for
that section, recently viewed pages, watched pages, related article summaries,
and the submitted text. The model returns structured JSON with a decision, editor
comments, prestige change, optional approved patch, and inbox message.

Approved contributions add a contributor revision section to the article, increase
prestige, and create an inbox message. Sections that need revision remain under
discussion. Rejected revisions receive in-universe editorial critique without
revealing the full hidden canon.

Contributor prestige is tracked in session state. Levels progress from `New
Contributor` through `Verified Contributor`, `Field Archivist`, `Senior Editor`,
and `Theory Curator`. After enough approved edits, a placeholder archive thread,
`The Kanzaki Radio Silence`, unlocks on the contributor profile.

## Trademark Note

The UI is an original encyclopedia-inspired interface. It does not use the real
Wikipedia name, logo, icons, copied CSS, copied text, or any Wikimedia assets.

## Changed Files

- Added `src/wiki_theory_app.py`
- Added `src/wiki_theory.css`
- Updated `src/wiki_mystery_engine.py`
- Updated `src/streamlit_basic.py` to launch the WikiTheory app
- Updated `.gitignore` so generated local article storage is not treated as
  source code
- Updated this `README.md`
