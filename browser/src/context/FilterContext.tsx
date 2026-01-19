
import { createContext, useContext, useMemo, useEffect, ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import { FilterState, Product } from '../types'
import { useData } from './DataContext'

interface FilterContextType {
    filters: FilterState
    sortOption: string
    setSortOption: (val: string) => void
    toggleFilter: (type: keyof FilterState, value: string) => void
    toggleCategory: (id: string, forceInclude?: boolean) => void
    resetFilters: () => void
    clearSection: (type: keyof FilterState) => void
    processedProducts: Product[]
    filteredCount: number
    setSource: (name: string) => void
    view: string | null
    isAnalysis: boolean
}

const FilterContext = createContext<FilterContextType | undefined>(undefined)

export function FilterProvider({ children }: { children: ReactNode }) {
    const [searchParams, setSearchParams] = useSearchParams()
    const { currentData, sources, isLoading } = useData()

    // Default Source Logic
    useEffect(() => {
        if (isLoading || sources.length === 0) return

        const currentSource = searchParams.get('source')
        if (!currentSource) {
            // User requested 'kupi' as default if available
            const kupiExists = sources.some(s => s.name === 'kupi')
            const defaultSource = kupiExists ? 'kupi' : sources[0].name

            setSearchParams(prev => {
                const p = new URLSearchParams(prev)
                p.set('source', defaultSource)
                return p
            }, { replace: true })
        }
    }, [isLoading, sources, searchParams, setSearchParams])

    const updateParams = (updater: (params: URLSearchParams) => void) => {
        setSearchParams(prev => {
            const newParams = new URLSearchParams(prev)
            updater(newParams)
            return newParams
        })
    }

    const view = searchParams.get('view')
    const sortOption = searchParams.get('sort') || 'default'
    const isAnalysis = view === 'analysis'

    // Derived Filters
    const filters = useMemo<FilterState>(() => ({
        brands: new Set(searchParams.getAll('brands')),
        categories: new Set(searchParams.getAll('categories')),
        excludeCategories: new Set(searchParams.getAll('exclude_categories')),
        stores: new Set(searchParams.getAll('stores'))
    }), [searchParams])

    // Actions
    const setSource = (name: string) => {
        updateParams(p => p.set('source', name))
    }

    const toggleCategory = (id: string, forceInclude = false) => {
        updateParams(params => {
            const inc = new Set(params.getAll('categories'))
            const exc = new Set(params.getAll('exclude_categories'))

            if (forceInclude) {
                params.delete('categories')
                params.append('categories', id)
                return
            }

            const isInc = inc.has(id)
            const isExc = exc.has(id)

            if (!isInc && !isExc) {
                inc.add(id)
            } else if (isInc) {
                inc.delete(id)
                exc.add(id)
            } else if (isExc) {
                exc.delete(id)
            }

            params.delete('categories')
            inc.forEach(v => params.append('categories', v))

            params.delete('exclude_categories')
            exc.forEach(v => params.append('exclude_categories', v))
        })
    }

    const toggleFilter = (type: keyof FilterState, value: string) => {
        if (type === 'categories') {
            toggleCategory(value)
            return
        }
        updateParams(params => {
            const current = new Set(params.getAll(type))
            if (current.has(value)) current.delete(value)
            else current.add(value)
            params.delete(type)
            current.forEach(v => params.append(type, v))
        })
    }

    const resetFilters = () => {
        updateParams(params => {
            params.delete('brands')
            params.delete('categories')
            params.delete('exclude_categories')
            params.delete('stores')
        })
    }

    const clearSection = (type: keyof FilterState) => {
        updateParams(params => {
            params.delete(type)
            if (type === 'categories') params.delete('exclude_categories')
        })
    }

    const setSortOption = (val: string) => {
        updateParams(params => {
            if (val === 'default') params.delete('sort')
            else params.set('sort', val)
        })
    }

    // Filter Logic
    const processedProducts = useMemo(() => {
        if (!currentData) return []

        let filtered = currentData.products.filter(p => {
            if (filters.brands.size > 0 && p.brand && !filters.brands.has(p.brand)) return false

            if (filters.excludeCategories.size > 0) {
                const productIds = p.category_ids || []
                if (productIds.some(id => filters.excludeCategories.has(id))) return false
            }

            if (filters.categories.size > 0) {
                const productIds = p.category_ids || []
                if (!productIds.some(id => filters.categories.has(id))) return false
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
    }, [currentData, filters, sortOption])

    const value = {
        filters,
        sortOption,
        setSortOption,
        toggleFilter,
        toggleCategory,
        resetFilters,
        clearSection,
        processedProducts,
        filteredCount: processedProducts.length,
        setSource,
        view,
        isAnalysis
    }

    return <FilterContext.Provider value={value}>{children}</FilterContext.Provider>
}

export const useFilters = () => {
    const context = useContext(FilterContext)
    if (context === undefined) throw new Error('useFilters must be used within a FilterProvider')
    return context
}
