import { useState, useEffect, useMemo } from 'react'

const formatPrice = (price) => {
  if (price === null || price === undefined) return '—'
  return new Intl.NumberFormat('cs-CZ', {
    style: 'currency',
    currency: 'CZK',
    minimumFractionDigits: 2
  }).format(price)
}

// Helper to render filter group (moved outside to prevent re-mounts)
const FilterGroup = ({ title, items, type, filters, toggleFilter, onClear }) => (
  <div className="filter-section">
    <div className="section-header">
      <h3>{title}</h3>
      <button className="clear-link" onClick={onClear}>Clear</button>
    </div>
    <div className="filter-group">
      {Object.entries(items).map(([name, count]) => (
        <label key={name} className="filter-item">
          <input
            type="checkbox"
            checked={filters[type].has(name)}
            onChange={() => toggleFilter(type, name)}
          />
          <span>{name}</span>
          <span className="filter-count">{count}</span>
        </label>
      ))}
    </div>
  </div>
)

const PriceRow = ({ pr }) => (
  <div className="price-item">
    <div className="price-item-header">
      <div className="store-info">
        <span className="store-name">{pr.store_name}</span>
      </div>
      {pr.validity && <span className="price-validity">{pr.validity}</span>}
    </div>

    {pr.condition && <div className="price-condition">{pr.condition}</div>}

    <div className="price-details">
      {/* Package Info */}
      {pr.package_size && (
        <span className="package-size">{pr.package_size}</span>
      )}

      <div className="price-values">
        <span className="price-main">
          {formatPrice(pr.price)}
        </span>

        {/* Discount */}
        {pr.discount_pct && (
          <span className="discount">-{pr.discount_pct}%</span>
        )}
      </div>
    </div>

    {/* Unit Price */}
    {(pr.unit_price) && (
      <div className="unit-price">
        ({formatPrice(pr.unit_price)} / {pr.unit || 'unit'})
      </div>
    )}
  </div>
)

const PriceList = ({ prices, selectedStores }) => {
  const [expanded, setExpanded] = useState(false)

  const { visible, hidden, hiddenRange } = useMemo(() => {
    // 1. Sort all by unit price ascending
    const sorted = [...prices].sort((a, b) => {
      const upA = a.unit_price ?? Infinity
      const upB = b.unit_price ?? Infinity
      return upA - upB
    })

    // 2. If no stores selected, show all
    if (selectedStores.size === 0) {
      return { visible: sorted, hidden: [], hiddenRange: null }
    }

    // 3. Filter
    const visible = []
    const hidden = []

    sorted.forEach(p => {
      if (selectedStores.has(p.store_name)) {
        visible.push(p)
      } else {
        hidden.push(p)
      }
    })

    let hiddenRange = null
    if (hidden.length > 0) {
      const vals = hidden.map(p => p.price).filter(v => v !== null)
      if (vals.length > 0) {
        const min = Math.min(...vals)
        const max = Math.max(...vals)
        hiddenRange = min === max ? formatPrice(min) : `${formatPrice(min)} - ${formatPrice(max)}`
      } else {
        hiddenRange = "unknown price"
      }
    }

    return { visible, hidden, hiddenRange }
  }, [prices, selectedStores])

  return (
    <div className="price-list">
      {visible.map((pr, idx) => <PriceRow key={idx} pr={pr} />)}

      {hidden.length > 0 && (
        <>
          {!expanded ? (
            <div className="more-offers" onClick={() => setExpanded(true)}>
              +{hidden.length} more offers for {hiddenRange}
            </div>
          ) : (
            hidden.map((pr, idx) => <PriceRow key={`h-${idx}`} pr={pr} />)
          )}
        </>
      )}
    </div>
  )
}

const CategoryNode = ({ node, filters, toggleFilter, hasSelectedParent = false }) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const hasChildren = Object.keys(node.children).length > 0
  const isChecked = filters.categories.has(node.name)
  const isExcluding = isChecked && hasSelectedParent

  const sortedChildren = useMemo(() => {
    return Object.values(node.children).sort((a, b) => a.name.localeCompare(b.name, 'cs'))
  }, [node.children])

  return (
    <div key={node.name} className="category-node">
      <div className="category-header">
        {hasChildren && (
          <button
            className={`expand-toggle ${isExpanded ? 'expanded' : ''}`}
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
          >
            ▶
          </button>
        )}
        <label className="filter-item">
          <input
            type="checkbox"
            className={isExcluding ? 'exclude' : ''}
            checked={isChecked}
            onChange={() => toggleFilter('categories', node.name)}
          />
          <span>{node.name}</span>
          <span className="filter-count">{node.count}</span>
        </label>
      </div>
      {hasChildren && isExpanded && (
        <div className="category-children">
          {sortedChildren.map(child => (
            <CategoryNode
              key={child.name}
              node={child}
              filters={filters}
              toggleFilter={toggleFilter}
              hasSelectedParent={hasSelectedParent || isChecked}
            />
          ))}
        </div>
      )}
    </div>
  )
}

const CategoryTree = ({ products, filters, toggleFilter, onClear }) => {
  // Build Tree
  const tree = useMemo(() => {
    const t = {}
    products.forEach(p => {
      const cats = p.categories
      if (!cats || cats.length === 0) return

      let currentLevel = t
      cats.forEach((c) => {
        if (!currentLevel[c]) {
          currentLevel[c] = { name: c, count: 0, children: {} }
        }
        currentLevel[c].count += 1
        currentLevel = currentLevel[c].children
      })
    })
    return t
  }, [products])

  const sortedRoots = useMemo(() => {
    return Object.values(tree).sort((a, b) => a.name.localeCompare(b.name, 'cs'))
  }, [tree])

  return (
    <div className="filter-section">
      <div className="section-header">
        <h3>Categories</h3>
        <button className="clear-link" onClick={onClear}>Clear</button>
      </div>
      <div className="filter-group">
        {sortedRoots.map(root => (
          <CategoryNode
            key={root.name}
            node={root}
            filters={filters}
            toggleFilter={toggleFilter}
          />
        ))}
      </div>
    </div>
  )
}

function App() {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [filters, setFilters] = useState({
    brands: new Set(),
    categories: new Set(),
    stores: new Set()
  })
  const [sortOption, setSortOption] = useState('default') // default, price-asc, price-desc, unit-asc, unit-desc

  useEffect(() => {
    fetch('/output.json')
      .then(res => res.json())
      .then(d => {
        setData(d)
        setIsLoading(false)
      })
      .catch(err => {
        console.error("Failed to load data", err)
        setIsLoading(false)
      })
  }, [])

  const toggleFilter = (type, value) => {
    setFilters(prev => {
      const newSet = new Set(prev[type])
      if (newSet.has(value)) {
        newSet.delete(value)
      } else {
        newSet.add(value)
      }
      return { ...prev, [type]: newSet }
    })
  }

  const resetFilters = () => {
    setFilters({
      brands: new Set(),
      categories: new Set(),
      stores: new Set()
    })
  }

  const clearSection = (type) => {
    setFilters(prev => ({ ...prev, [type]: new Set() }))
  }

  const processedProducts = useMemo(() => {
    if (!data) return []

    // 1. Filter
    let filtered = data.products.filter(p => {
      // Brand Filter
      if (filters.brands.size > 0) {
        if (!filters.brands.has(p.brand)) return false
      }

      // Category Filter (match any, with inverse subtraction for children)
      if (filters.categories.size > 0) {
        // Find all categories in the product path that are selected
        const selectedMatches = p.categories.map((c, idx) => ({ name: c, idx })).filter(m => filters.categories.has(m.name))

        if (selectedMatches.length === 0) return false

        // Logic: For the deepest selected category in this product's path, 
        // if it has an ancestor that is ALSO selected, consider it an EXCLUSION.
        const deepestMatch = selectedMatches[selectedMatches.length - 1]
        const hasSelectedAncestor = selectedMatches.some(m => m.idx < deepestMatch.idx)

        if (hasSelectedAncestor) return false
      }

      // Store Filter
      // Modified Logic: Keep product if it has ANY relevant offers, OR if no stores selected
      if (filters.stores.size > 0) {
        const productStores = p.prices.map(pr => pr.store_name)
        // Ensure at least one price matches selected store
        if (!productStores.some(s => filters.stores.has(s))) return false
      }

      return true
    })

    // 2. Sort
    if (sortOption !== 'default') {
      filtered = [...filtered].sort((a, b) => {
        const getRelevantPrices = (prod) => {
          if (filters.stores.size === 0) return prod.prices;
          return prod.prices.filter(p => filters.stores.has(p.store_name));
        };

        const getMetric = (prod, field, type = 'min') => {
          const prices = getRelevantPrices(prod);
          const values = prices.map(p => p[field]).filter(v => v !== null && v !== undefined);
          if (values.length === 0) return type === 'min' ? Infinity : -1;
          return type === 'min' ? Math.min(...values) : Math.max(...values);
        };

        if (sortOption === 'price-asc') {
          return getMetric(a, 'price', 'min') - getMetric(b, 'price', 'min')
        }
        if (sortOption === 'price-desc') {
          return getMetric(b, 'price', 'max') - getMetric(a, 'price', 'max')
        }
        if (sortOption === 'unit-asc') {
          return getMetric(a, 'unit_price', 'min') - getMetric(b, 'unit_price', 'min')
        }
        if (sortOption === 'unit-desc') {
          return getMetric(b, 'unit_price', 'min') - getMetric(a, 'unit_price', 'min')
        }
        return 0
      })
    }

    return filtered
  }, [data, filters, sortOption])

  if (isLoading) return <div className="loading">Loading products...</div>
  if (!data) return <div className="error">Failed to load data. Ensure output.json is in public folder.</div>

  const { brands, categories, stores } = data.metadata

  return (
    <>
      <header>
        <h1>Agravity Deals</h1>
        <div className="controls">
          <select
            value={sortOption}
            onChange={(e) => setSortOption(e.target.value)}
            className="sort-select"
          >
            <option value="default">Default Sort</option>
            <option value="price-asc">Price: Low to High</option>
            <option value="price-desc">Price: High to Low</option>
            <option value="unit-asc">Unit Price: Low to High</option>
          </select>
          <div className="stats">
            {processedProducts.length} filtered / {data.metadata.total_products} total
          </div>
        </div>
      </header>

      <div className="container">
        <aside>
          <div className="sidebar-header">
            <h2>Filters</h2>
            <button className="reset-button" onClick={resetFilters}>Clear All</button>
          </div>

          <FilterGroup
            title="Stores"
            items={stores}
            type="stores"
            filters={filters}
            toggleFilter={toggleFilter}
            onClear={() => clearSection('stores')}
          />

          <CategoryTree
            products={data.products}
            filters={filters}
            toggleFilter={toggleFilter}
            onClear={() => clearSection('categories')}
          />

          <FilterGroup
            title="Brands"
            items={brands}
            type="brands"
            filters={filters}
            toggleFilter={toggleFilter}
            onClear={() => clearSection('brands')}
          />
        </aside>

        <main>
          <div className="product-grid">
            {processedProducts.map((p, i) => (
              <div key={i} className="product-card">
                <img src={p.image_url} alt={p.title} className="product-image" loading="lazy" />
                <div className="product-content">
                  <div className="product-brand">{p.brand}</div>
                  <h2 className="product-title">{p.name}</h2>
                  <div className="product-categories">
                    {p.categories.join(' › ')}
                  </div>

                  <PriceList prices={p.prices} selectedStores={filters.stores} />
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    </>
  )
}

export default App
