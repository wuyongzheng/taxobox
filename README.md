# TaxoBox

A client-side web app to explore plant taxonomy. Add plants, see their shared
ancestry, and jump to Wikipedia for every node. Data is loaded from local TSV
files generated from Wikipedia dumps. A demo can be accessed at github.io
(TODO)

## Quick start

1. Generate language/domain pages and configs:

```bash
python3 scripts/generate-pages.py
```

2. Serve the folder with a static server (required for `fetch()`):

```bash
python3 -m http.server 8000 --directory html
```
3. Open `http://localhost:8000/` in your browser.

## Files

- `html/index.template.html` - HTML template for language/domain pages
- `html/index.html` - Default page (English + Plants)
- `html/index-*.html` - Generated pages per language/domain
- `html/styles.css` - Styling
- `html/app.js` - Data loading, search, and tree rendering
- `html/config-*.js` - Generated configs for each language/domain page
- `html/pages.json` - Page generation manifest
- `html/tax-*.tsv` and `html/page-*.tsv` - Raw TSV data
- `html/tax-*.tsv.gz` and `html/page-*.tsv.gz` - Gzip-compressed data (optional)

## Config generation

Edit `html/pages.json` to add languages, then regenerate pages with:

```bash
python3 scripts/generate-pages.py
```

Each generated `config-*.js` exposes `window.APP_CONFIG`:

```js
window.APP_CONFIG = {
  WIKI_PAGE: "https://en.wikipedia.org/wiki/",
  WIKI_FILE: "https://en.wikipedia.org/wiki/Special:FilePath/",
  TAX_TSV: "tax-en-plant.tsv",
  PAGE_TSV: "page-en-plant.tsv",
  LANGUAGE: "English",
};
```

The app will load `TAX_TSV.gz` / `PAGE_TSV.gz` if the browser supports gzip decompression, otherwise it falls back to the raw `.tsv` files.

## Data format

### `tax.tsv`
Each line: `name<TAB>parent<TAB>rank<TAB>page`

- `name` is the taxonomy key.
- `parent` is the parent taxonomy key.
- `rank` is a label like `clade`, `genus`, `familia`. Add `!` to force-display a node (e.g., `subfamilia!`).
- `page` is the Wikipedia page name (links to `page.tsv.name`).

### `page.tsv`
Each line: `name<TAB>length<TAB>taxonomy<TAB>image<TAB>redir1<TAB>redir2...`

- `name` is the page title, also as a primary key.
- `length` is the page character count (used for search ranking).
- `taxonomy` links to `tax.tsv.name`.
- `image` is the file part of the Wikipedia image URL.
- `redir*` are alternate names for search.

## Features

- Tree visualization of shared taxonomy (rooted at the lowest common ancestor).
- Search with alternate names.
- Clickable nodes linking to Wikipedia.
- Shareable links via the `plants` query parameter.
- Pruning of single-child taxonomy nodes without images (unless `rank!`).

## Share links

Selected leaves are encoded in the URL:

```
?pages=Apple_Potato_Lavandula
```

Use the “Copy share link” button for convenience.
