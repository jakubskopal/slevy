# Albert Wolt Crawler

Browser-based crawler for Albert Vinohradská store on Wolt platform.

## Features

- **Parallel Execution**: Multiple browser windows crawling simultaneously
- **Infinite Scroll Support**: Handles Wolt's dynamic product loading
- **State Management**: Resume interrupted crawls
- **Gzipped Storage**: Compressed HTML files with metadata
- **Dynamic Category Discovery**: Automatically finds all categories

## Usage

### Basic Usage
```bash
cd sources/albert
python crawler.py
```

### With Options
```bash
# Limit products per category (for testing)
python crawler.py --limit 5

# Run with 3 parallel workers
python crawler.py --workers 3

# Run in headless mode
python crawler.py --headless

# Show colored progress bar
python crawler.py --color
```

## Output

- **HTML Files**: `data/albert_raw/*.html.gz`
- **State File**: `data/albert_raw/albert_state.json`

## Architecture

- `crawler.py` - Main orchestration and worker management
- `crawler_category.py` - Category navigation and infinite scroll
- `crawler_product.py` - Product page data extraction
- `crawler_global.py` - Shared utilities

## Data Format

Each HTML file includes metadata header:
```html
<!-- META_JSON: {"origin_url": "...", "preparsed": {...}} -->
```

Preparsed data includes:
- Product name
- Price (current and original)
- Unit price
- Image URL
- Description
- Breadcrumbs/category
