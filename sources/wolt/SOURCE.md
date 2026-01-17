# Albert Wolt Scraper Notes

## Target Website
- **URL**: `https://wolt.com/cs/cze/prague/venue/albert-vinohradska`
- **Platform**: Wolt delivery service (Albert Vinohradská store)
- **Type**: Online grocery ordering platform

## Website Structure

### Main Page
- **URL Pattern**: `https://wolt.com/cs/cze/prague/venue/albert-vinohradska`
- **Features**:
  - Left sidebar with category navigation
  - Special offers section ("Speciální nabídky")
  - Most ordered section ("Nejčastěji objednávané")
  - Category-based browsing
  - Persistent address selection modal that must be closed

### Category Navigation
- **URL Pattern**: `https://wolt.com/cs/cze/prague/venue/albert-vinohradska/items/[category-slug]-[id]`
- **Examples**:
  - Fruits & Vegetables: `.../items/ovoce-a-zelenina-3`
  - Bakery: `.../items/pekarna-a-cukrarna-11`
  - Dairy & Chilled: `.../items/mlecne-a-chlazene-21`
  - Yogurts & Desserts (subcategory): `.../items/jogurty-a-dezerty-22`

- **Structure**:
  - Main categories have subcategories
  - Subcategories have their own unique IDs and URLs
  - Products are displayed in a grid format
  - Within main category views, products are grouped by subcategory sections

### Product Pages
- **URL Pattern**: `https://wolt.com/cs/cze/prague/venue/albert-vinohradska/[product-slug]-itemid-[id]`
- **Example**: `.../rajcata-cherry-itemid-65...`
- **Features**:
  - Product image
  - Product name
  - Price (current and original if discounted)
  - Unit price (per kg/l)
  - Weight/quantity
  - "Add to cart" button with quantity selector
  - Product description
  - "Info o produktu" (Product info) link

### Pagination Mechanism
- **Type**: **Infinite Scroll**
- **Behavior**:
  - Initial load: ~24-47 products depending on category
  - New products load automatically as user scrolls to bottom
  - No traditional "Load more" button or numbered pagination
  - "Všechny položky" (All items) links present when viewing from main page
  - Total products in a category can be in the hundreds

### DOM Structure
- **Product Elements**:
  - Attribute: `data-test-id="VenueItem"` or `data-testid="VenueItem"`
  - Container: `<a>` tags wrapping entire product card
  - Product links contain `-itemid-` in href
  - Common CSS classes: `c1apib1v`, `c1kav63t` (may change)

- **Category Links**:
  - Located in left sidebar
  - Links contain `/items/` in href
  - Clickable navigation elements

## API Endpoints

### Main Venue API
- **Endpoint**: `https://restaurant-api.wolt.com/v1/pages/venue/albert-vinohradska`
- **Method**: GET
- **Returns**: JSON with complete venue data including:
  - Venue information (name, location, hours)
  - All categories and subcategories
  - Product listings with full details
  - Pricing information
  - Availability data

### Data Structure (from API)
```json
{
  "results": [{
    "venue": {
      "id": "...",
      "name": "Albert Vinohradská",
      "categories": [...]
    },
    "items": [{
      "id": "...",
      "name": "Product Name",
      "description": "...",
      "baseprice": 3890,  // Price in minor units (haléře)
      "image": "https://...",
      "category": "...",
      ...
    }]
  }]
}
```

## Crawling Strategy

### Recommended Approach
1. **API-First Strategy**:
   - Fetch the main venue API endpoint
   - Parse JSON response for all products and categories
   - Extract product details directly from API data
   - Much faster and more reliable than browser automation

2. **Browser Automation (if needed)**:
   - Use Playwright/Selenium for JavaScript-heavy interactions
   - Handle address selection modal (close it first)
   - Navigate through categories via sidebar
   - Implement scroll-based pagination:
     - Scroll to bottom of page
     - Wait for new products to load
     - Repeat until no new products appear
   - Extract product links with `-itemid-` pattern
   - Visit individual product pages for detailed information

### Anti-Bot Considerations
- Website appears to be standard React/Next.js application
- No obvious anti-bot protection observed
- API endpoint is publicly accessible
- Rate limiting may apply to API requests

## Data Extraction Points

### Product Information
- **Name**: Product title
- **Price**: Current price (in Kč)
- **Original Price**: Pre-discount price (if applicable)
- **Unit Price**: Price per kg/l/piece
- **Unit of Measure**: kg, l, g, ks (pieces)
- **Image URL**: Product image
- **Category**: Main category and subcategory
- **Description**: Product description text
- **Availability**: In stock status
- **Brand**: Brand name (if available)

### Category Information
- **Category ID**: Unique identifier
- **Category Name**: Display name
- **Category Slug**: URL-friendly name
- **Parent Category**: For subcategories
- **Product Count**: Number of products in category

## Technical Notes

### Modals and Popups
- **Address Selection Modal**: Appears on first visit
  - Must be closed to interact with page
  - Close button selector: `[aria-label="Zavřít"]` or similar
  - Can be closed via JavaScript: `document.querySelector('button').click()`

### Performance
- Initial page load: Fast
- API response: Very fast (~200-500ms)
- Infinite scroll: Smooth, loads ~20-30 products per batch
- Product page load: Fast

### Data Freshness
- Prices update in real-time
- Availability changes dynamically
- Special offers have validity periods
- Recommend daily crawls for accurate pricing

## Comparison with Other Sources

### vs. Tesco
- **Simpler**: No complex anti-bot measures
- **Faster**: API-first approach possible
- **Cleaner**: Well-structured JSON data
- **Limited**: Only Albert Vinohradská location

### vs. Kupi
- **Different Purpose**: Actual store vs. deal aggregator
- **More Products**: Full grocery catalog vs. selected deals
- **Real Prices**: Actual selling prices vs. promotional prices
- **Single Source**: One store vs. multiple retailers

## Implementation Priority

1. **High Priority**: API-based crawler
   - Fastest and most reliable
   - Complete data in single request
   - Easy to parse and maintain

2. **Medium Priority**: Browser-based crawler
   - Useful for validation
   - Can handle dynamic content
   - More complex but flexible

3. **Low Priority**: HTML parsing
   - Backup strategy if API changes
   - More fragile due to DOM changes
   - Requires more maintenance
