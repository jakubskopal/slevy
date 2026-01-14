# Agent Project Context - Slevy (Kupi.cz & Tesco Aggregator)

## Project Overview
This project is a discount aggregator ("Slevy") that scrapes data from multiple sources (**Kupi.cz** and **Tesco**) and displays them in a unified React-based web application.

## Tech Stack
- **Backend (Kupi)**: Python 3, `BeautifulSoup4`, `requests`, `gzip`, `threading`.
- **Backend (Tesco)**: Python 3, `Playwright` (Firefox), `playwright-stealth`, `BeautifulSoup4`.
- **Frontend**: React (Vite), Vanilla CSS.
- **Deployment**: GitHub Actions + GitHub Pages (at `/slevy/`).

## Architectural Decisions
1. **Multi-Source Structure**: 
   - `sources/kupi/`: Original Kupi.cz scraper.
   - `sources/tesco/`: Tesco scraper using browser automation.
2. **Data Storage**: Raw HTML is saved as `.html.gz` in `data/raw/` (Kupi) or `data/tesco_raw/` (Tesco).
3. **Metadata Injection**: 
   - Kupi: Embeds original URL as an HTML comment.
   - Tesco: Embeds a `META_JSON` comment with origin URL and preparsed DOM data (breadcrumbs, simple price).
4. **Decoupled Parsers**: Each source has its own `parser.py` producing a JSON dataset (`kupi.json`, `tesco.json`).
5. **Tesco Specifics**:
   - **Crawler**: Uses Playwright with Firefox and stealth patches to bypass Akamai/anti-bot. Navigates by clicking to maintain session validity.
   - **Parser**: Prioritizes extracting `apolloCache` state or JSON-LD from the HTML, falling back to DOM parsing only if necessary.
6. **Frontend Integration**:
   - The React app consumes JSON data. (Future goal: Merge multiple sources into one `output.json`).

## Usage

### Kupi.cz
- **Crawl**: `source .venv/bin/activate && python3 sources/kupi/crawler.py --color`
- **Parse**: `python3 sources/kupi/parser.py --color`

### Tesco
- **Install (First Run)**: 
  ```bash
  .venv/bin/pip install playwright-stealth
  .venv/bin/playwright install firefox
  ```
- **Crawl**: `python3 sources/tesco/crawler.py --workers 3 --color`
- **Parse**: `python3 sources/tesco/parser.py --color`

### Web App
- **Dev**: `cd browser && nvm use && npm run dev`
- **Build**: `cd browser && npm run build` (creates `dist/`)

## Persistent Observations
- **Environment**: Always use `python3` inside `.venv` and respect `.nvmrc` for Node.
- **Tesco Consistency**: The Tesco crawler uses a specialized `CrawlerState` to handle resumes and parallelism.
- **Aesthetics**: When modifying the UI, prioritize high-quality aesthetics and Czech locale sorting.
