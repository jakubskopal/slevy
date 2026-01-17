import { useState, useEffect, useMemo } from 'react'
import { Routes, Route, useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { Data, FilterState, Source, Product } from './types'

// Components
import { Loading } from './components/common/Loading'
import { Header } from './components/layout/Header'
import { Sidebar } from './components/layout/Sidebar'
import { ProductCard } from './components/products/ProductCard'

function Shop() {
  const { source } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  const [data, setData] = useState<Data | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [sources, setSources] = useState<Source[]>([])
  const [currentSource, setCurrentSource] = useState<Source | null>(null)

  // Derived State from URL
  const filters = useMemo<FilterState>(() => ({
    brands: new Set(searchParams.getAll('brands')),
    categories: new Set(searchParams.getAll('categories')),
    stores: new Set(searchParams.getAll('stores'))
  }), [searchParams])

  const sortOption = searchParams.get('sort') || 'default'

  // 1. Load Index on Mount
  useEffect(() => {
    fetch('index.json')
      .then(res => res.json())
      .then((idx: { sources: Source[] }) => {
        if (idx.sources && idx.sources.length > 0) {
          setSources(idx.sources)
        } else {
          console.error("Index.json empty or invalid")
          setIsLoading(false)
        }
      })
      .catch(err => {
        console.warn("Failed to load index.json (dev mode?)", err)
        setSources([{ name: 'Dev (Kupi)', file: 'kupi.result.json' }])
      })
  }, [])

  // 2. Sync Source Param -> Current Source
  useEffect(() => {
    if (sources.length === 0) return

    if (!source) {
      // No source valid, redirect to default (kupi or first)
      const def = sources.find(s => s.name === 'kupi') || sources[0]
      if (def) navigate('/' + def.name, { replace: true })
      return
    }

    const selected = sources.find(s => s.name === source)
    if (selected) {
      setCurrentSource(selected)
    } else {
      console.warn(`Unknown source: ${source}`)
      const def = sources[0]
      if (def) navigate('/' + def.name, { replace: true })
    }
  }, [source, sources, navigate])

  // 3. Load Data when Current Source Changes
  useEffect(() => {
    if (!currentSource) return

    setIsLoading(true)
    setData(null)

    // Artificial delay for "nice" loading experience (min 500ms)
    Promise.all([
      fetch(currentSource.file).then(res => res.json()),
      new Promise(resolve => setTimeout(resolve, 500))
    ])
      .then(([d]) => {
        setData(d)
        setIsLoading(false)
      })
      .catch(err => {
        console.error(`Failed to load data from ${currentSource.file}`, err)
        setIsLoading(false)
      })
  }, [currentSource])

  // Helpers
  const updateParams = (updater: (params: URLSearchParams) => void) => {
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev)
      updater(newParams)
      return newParams
    })
  }

  const toggleFilter = (type: keyof FilterState, value: string) => {
    updateParams(params => {
      const current = new Set(params.getAll(type))
      if (current.has(value)) current.delete(value)
      else current.add(value)

      params.delete(type)
      current.forEach(v => params.append(type, v))
    })
  }

  const setFilterSet = (type: keyof FilterState, values: Set<string>) => {
    updateParams(params => {
      params.delete(type)
      values.forEach(v => params.append(type, v))
    })
  }

  const resetFilters = () => {
    updateParams(params => {
      params.delete('brands')
      params.delete('categories')
      params.delete('stores')
    })
  }

  const clearSection = (type: keyof FilterState) => {
    updateParams(params => params.delete(type))
  }

  const setSortOption = (val: string) => {
    updateParams(params => {
      if (val === 'default') params.delete('sort')
      else params.set('sort', val)
    })
  }

  const processedProducts = useMemo(() => {
    if (!data) return []

    let filtered = data.products.filter(p => {
      if (filters.brands.size > 0 && p.brand && !filters.brands.has(p.brand)) return false

      if (filters.categories.size > 0) {
        const selectedMatches = p.categories.map((c, idx) => ({ name: c, idx })).filter(m => filters.categories.has(m.name))
        if (selectedMatches.length === 0) return false
        const deepestMatch = selectedMatches[selectedMatches.length - 1]
        const hasSelectedAncestor = selectedMatches.some(m => m.idx < deepestMatch.idx)
        if (hasSelectedAncestor) return false
      }

      if (filters.stores.size > 0) {
        const productStores = p.prices.map(pr => pr.store_name)
        if (!productStores.some(s => filters.stores.has(s))) return false
      }
      return true
    })

    if (sortOption !== 'default') {
      filtered = [...filtered].sort((a, b) => {
        const getRelevantPrices = (prod: Product) => {
          if (filters.stores.size === 0) return prod.prices;
          return prod.prices.filter(p => filters.stores.has(p.store_name));
        };
        const getMetric = (prod: Product, field: 'price' | 'unit_price', type = 'min') => {
          const prices = getRelevantPrices(prod);
          const values = prices.map(p => p[field]).filter((v): v is number => v !== null && v !== undefined);
          if (values.length === 0) return type === 'min' ? Infinity : -1;
          return type === 'min' ? Math.min(...values) : Math.max(...values);
        };
        if (sortOption === 'price-asc') return getMetric(a, 'price', 'min') - getMetric(b, 'price', 'min')
        if (sortOption === 'price-desc') return getMetric(b, 'price', 'max') - getMetric(a, 'price', 'max')
        if (sortOption === 'unit-asc') return getMetric(a, 'unit_price', 'min') - getMetric(b, 'unit_price', 'min')
        if (sortOption === 'unit-desc') return getMetric(b, 'unit_price', 'min') - getMetric(a, 'unit_price', 'min')
        return 0
      })
    }
    return filtered
  }, [data, filters, sortOption])

  if (isLoading) {
    return <Loading />
  }
  // Allow null data if still effective loading, but logic handled by isLoading
  if (!data) return <div className="error">Failed to load data.</div>

  // Ensure metadata exists, gracefully handle missing
  const { brands: bRaw, stores: sRaw } = data.metadata || {}

  // Helper to ensure we have {Name: Count} object for FilterGroup
  const ensureCountObject = (val: any): Record<string, number> => {
    if (!val) return {}
    if (Array.isArray(val)) {
      return val.reduce((acc: Record<string, number>, item: string) => {
        acc[item] = 0 // Default count if missing
        return acc
      }, {})
    }
    return val
  }

  const brands = ensureCountObject(bRaw)
  const stores = ensureCountObject(sRaw)

  return (
    <>
      <Header
        sortOption={sortOption}
        setSortOption={setSortOption}
        filteredCount={processedProducts.length}
        totalCount={data.metadata.total_products}
      />

      <div className="container">
        <Sidebar
          sources={sources}
          currentSource={currentSource}
          onSourceChange={(name) => navigate('/' + name)}
          filters={filters}
          toggleFilter={toggleFilter}
          setFilterSet={setFilterSet}
          resetFilters={resetFilters}
          clearSection={clearSection}
          brands={brands}
          stores={stores}
          products={data.products}
        />

        <main>
          <div className="product-grid">
            {processedProducts.map((p, i) => (
              <ProductCard
                key={i}
                product={p}
                selectedStores={filters.stores}
              />
            ))}
          </div>
        </main>
      </div>
    </>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/:source?" element={<Shop />} />
    </Routes>
  )
}

export default App
