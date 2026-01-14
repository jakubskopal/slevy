# Tesco Scraper Notes

## Implementation Details

### Crawler (`crawler.py`)
- **Technology**: Playwright with Firefox (Headless).
- **Stealth**: Uses `playwright-stealth` and specific User-Agent/Fingerprinting bypasses.
- **Strategy**:
  1. Opens homepage (`/groceries/cs-CZ/`) to establish session/cookies.
  2. Navigates to each main category by clicking or direct search (Firefox handles these better than Chromium).
  3. Scans through all pages of product listings to collect product detail URLs.
  4. Downloads each product detail page and saves the rendered HTML as `.html.gz`.
- **Anti-Bot**: Handles Akamai triggers by using Firefox and stealth patches.

### Parser (`parser.py`)
- **Technology**: BeautifulSoup + regex for JSON extraction.
- **Strategy**:
  1. Extracts the `apolloCache` JSON object from the HTML source.
  2. Locates the `ProductType:<ID>` entity which contains rich metadata.
  3. Maps accurate fields: `title`, `brandName`, `defaultImageUrl`, `categories`.
  4. Extracts exact price data: `actual`, `unitPrice`, `unitOfMeasure`.
  5. Handles "Piece vs Weight" by checking `displayType` and `averageWeight`.

## Usage

### Prerequisites
Ensure the virtual environment is set up and browser binaries are installed:
```bash
.venv/bin/pip install playwright-stealth
.venv/bin/playwright install firefox
```

### Running the Crawl
To perform a full crawl (this may take time due to protective delays):
```bash
.venv/bin/python3 sources/tesco/crawler.py --color
```
To test with a limited number of products:
```bash
.venv/bin/python3 sources/tesco/crawler.py --limit 10 --color
```

### Running the Parse
To generate `tesco.json` from the downloaded files:
```bash
.venv/bin/python3 sources/tesco/parser.py --color
```

## Data Observations
- **Brand**: Accurately extracted via `brandName` in Apollo state.
- **Units**: Common values are `each` (translated to piece), `kg`, etc.
- **Clubcard**: The parser can detect `isClubcard` flags to distinguish promotions.
