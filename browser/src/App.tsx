
import { useState } from 'react'
import { Product } from './types'

// Contexts
import { DataProvider, useData } from './context/DataContext'
import { FilterProvider, useFilters } from './context/FilterContext'

// Components
import { Loading } from './components/common/Loading'
import { Header } from './components/layout/Header'
import { Sidebar } from './components/layout/Sidebar'
import { ProductCard } from './components/products/ProductCard'
import { ProductDetail } from './components/products/ProductDetail'
import { AnalysisPage } from './components/analysis/AnalysisPage'

function DataSource({ onProductClick }: { onProductClick: (p: Product) => void }) {
  const { processedProducts, filters } = useFilters()

  return (
    <div className="container">
      <Sidebar />
      <main>
        <div className="product-grid">
          {processedProducts.map((p, i) => (
            <ProductCard
              key={i}
              product={p}
              selectedStores={filters.stores}
              onProductClick={onProductClick}
            />
          ))}
        </div>
      </main>
    </div>
  )
}

function AppContent() {
  const { isAnalysis } = useFilters()
  const { allData, isLoading, currentData, currentSource } = useData()

  // Local UI State (Modal)
  const [selectedProduct, setSelectedProduct] = useState<{ product: Product, sourceName: string } | null>(null)

  const handleProductClick = (product: Product) => {
    if (currentSource) {
      setSelectedProduct({ product, sourceName: currentSource.name })
    }
  }

  // Deep Link Handler
  const handleProductLink = (store: string, url: string) => {
    if (allData[store]) {
      const product = allData[store].products.find(p => p.product_url === url)
      if (product) {
        setSelectedProduct({ product, sourceName: store })
      } else {
        console.warn("Product not found in store data", url)
      }
    } else {
      console.warn("Store data not loaded or unknown", store)
    }
  }

  if (isLoading) return <Loading />

  return (
    <>
      <Header showControls={!isAnalysis} />

      {isAnalysis ? (
        <AnalysisPage onProductLink={handleProductLink} />
      ) : (
        currentData ? (
          <DataSource onProductClick={handleProductClick} />
        ) : (
          <div className="container" style={{ marginTop: '2rem' }}>
            <div className="error">Data source not found or loading...</div>
          </div>
        )
      )}

      {selectedProduct && (
        <ProductDetail
          product={selectedProduct.product}
          dataSourceName={selectedProduct.sourceName}
          onClose={() => setSelectedProduct(null)}
        />
      )}
    </>
  )
}

function App() {
  return (
    <DataProvider>
      <FilterProvider>
        <AppContent />
      </FilterProvider>
    </DataProvider>
  )
}

export default App
