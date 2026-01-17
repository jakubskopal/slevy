# Agrty - Grocery Crawler Project

Agrty is a sophisticated web scraping tool designed to aggregate product and price data from major online grocery retailers. It uses a hybrid approach of detailed Selenium-based crawling and efficient offline parsing.

## Project Structure

The project is organized by data source in the `sources/` directory.

### Sources

#### 1. Tesco (`sources/tesco/`)
*   **Target**: `nakup.itesco.cz`
*   **Crawler** (`crawler.py`): 
    *   **Architecture**: Multi-threaded Selenium crawler.
    *   **Strategy**: "Click-based" navigation (mimics user behavior) to traverse categories and pagination.
    *   **Features**:
        *   **Resiliency**: Automated recovery from connection failures and page load timeouts. If a category fails, it restarts from scratch in a fresh window.
        *   **State Management**: Tracks processed products and category hierarchy in `data/tesco_raw/tesco_state.json` to allow pausing and resuming.
        *   **Raw Data**: Saves full HTML source of product pages (gzipped) to `data/tesco_raw/` for offline parsing.
*   **Parser** (`parser.py`):
    *   **Input**: Gzipped HTML files from `data/tesco_raw/`.
    *   **Extraction**: Hybrid extraction using:
        *   **Apollo Cache**: Extracts the hydrated React state (Apollo) directly from the HTML for structured data.
        *   **JSON-LD**: Fallback to Schema.org structural metadata.
        *   **Exhaustive DOM**: Final fallback to CSS selectors.
    *   **Output**: `data/tesco.result.json`

#### 2. Kupi (`sources/kupi/`)
*   **Target**: `kupi.cz` (Price aggregation and flyer site)
*   **Crawler**: Selenium-based crawler that archives deal pages.
    *   **Raw Data**: Saves raw HTML content (gzipped) to `data/kupi_raw/`.
*   **Parser** (`parser.py`):
    *   **Features**:
        *   **Dual-Path Parsing**: Handles both detail view (`sleva_*.html`) and category grid view (`slevy_*.html`) files.
        *   **Smart Date Parsing**: Converts Czech natural language dates (e.g., "dnes končí", "čt 15. 1.") into standard ISO ranges.
        *   **Deduplication**: Merges offers from different files based on product name.
    *   **Output**: `data/kupi.result.json`

#### 3. Wolt (Albert, Billa, Globus)
*   **Target**: `wolt.com` (Delivery platform)
*   **Unified Crawler** (`sources/wolt/crawler.py`):
    *   **Architecture**: Shared codebase for multiple stores.
    *   **Multi-Store Support**: Configurable via `--store` argument (maps to specific venue URLs).
    *   **Features/Strategy**:
        *   **Dynamic Category Discovery**: Automatically scans the store page to find all categories.
        *   **Browser Pooling**: Reuses WebDriver instances to minimize overhead.
        *   **Resumable**: Tracks progress using `CrawlerState`, allowing pause/resume.
*   **Unified Parser** (`sources/wolt/parser.py`):
    *   **Input**: Raw HTML files from `data/<store>_raw/`.
    *   **Features**: Extracts product details, prices, and images from Wolt's standardized layout.
    *   **Output**: `data/<store>.result.json` (e.g., `albert.result.json`)

## Data Schema

The output files (`*.result.json`) conform to a unified JSON schema defined in:

**`sources/schema.json`**

### Key Fields:
*   `products`: Array of product objects.
    *   `name`: Standardized product name.
    *   `product_url`: Original URL of the product.
    *   `prices`: Array of price offers.
        *   `price`: Current price.
        *   `original_price`: Price before discount.
        *   `unit_price`: Price per unit (e.g. per kg).
        *   `condition`: Conditions (e.g., "Clubcard").
        *   `validity_start` / `validity_end`: Date range for the offer.

## Browser Automation

This project relies heavily on **Selenium WebDriver** for crawling.

*   **Human-like Behavior**: The Tesco crawler is specifically designed to avoid detection by behaving like a user (clicking menus, scrolling, waiting for elements) rather than just hitting APIs.
*   **Performance**:
    *   **Parallelism**: Configurable `ThreadExecutor` allows running multiple browser windows simultaneously (`--workers N`).
    *   **Headless**: Supports running in `headless=new` mode for efficiency on servers.

## Browser Application

The `browser/` directory contains a modern web application for visualizing the aggregated data.

*   **Stack**: React + Vite
*   **Name**: Agravity Deals
*   **Functionality**:
    *   **Data Source**: Dynamically loads data from `data/` via `index.json`, allowing users to switch between sources (e.g., Kupi, Tesco, Albert) via a dropdown.
    *   **Filtering**:
        *   **Stores**: Local filtering by specific retailer.
        *   **Categories**: Hierarchical tree-based filtering with support for inclusion/exclusion logic.
        *   **Brands**: Filter by manufacturer brand.
    *   **Sorting**: Sort products by Absolute Price or Unit Price (ASC/DESC).
    *   **Comparison**: Displays aggregated offers per product, allowing easy comparison of prices across different stores and package sizes.
    *   **Unit Pricing**: Automatically calculates and highlights unit prices (e.g., per kg/l) to reveal true value.

### Running the App
1.  Navigate to `browser/`.
2.  **Node.js Setup**:
    *   If you use [nvm](https://github.com/nvm-sh/nvm), run `nvm use` (checks `.nvmrc`).
    *   Otherwise, ensure you have Node.js (v20+) installed.
3.  Install dependencies: `npm install`.
4.  **Data Setup**: The build process automatically copies `data/*.result.json` to `public/` and generates the index.
    *   Ensure you have generated data in `../data/`.
5.  Start dev server: `npm run dev`.

## Documentation Maintenance

**Note**: This `README.md` and the `sources/schema.json` are maintained by the AI assistant.

*   **When to update**: If you add a new data source, change the crawler architecture, modify the output schema, or change how the browser app consumes data.
*   **How to update**: Explicitly ask the assistant to "update the project README" after making your code changes.

