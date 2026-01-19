
import { createContext, useContext, useMemo, useEffect, ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Data, FilterState, Product } from '../types'
import { useData } from './DataContext'
import { useProductFiltering } from '../hooks/useProductFiltering'

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
    applyDeepLink: (source: string, categoryId: string, storeName?: string) => void
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

    const applyDeepLink = (source: string, categoryId: string, storeName?: string) => {
        // NOTE: This atomic update is crucial. It transitions the view and sets the category in one go,
        // which preserves the user's context and crutially, the selected product.
        // Keep this implementation atomic to maintain this paradigm.
        updateParams(params => {
            // Exit analysis mode
            params.delete('view')

            // Set source
            params.set('source', source)

            // Reset filters
            params.delete('brands') // Only "included" brands supported currently

            // Set category exclusive
            params.delete('categories')
            params.delete('exclude_categories')
            params.append('categories', categoryId)

            // Handle store
            params.delete('stores')
            if (storeName) {
                params.append('stores', storeName)
            }
        })
    }

    // Filter Logic
    const processedProducts = useProductFiltering(currentData, filters, sortOption)

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
        isAnalysis,
        applyDeepLink
    }

    return <FilterContext.Provider value={value}>{children}</FilterContext.Provider>
}

export const useFilters = () => {
    const context = useContext(FilterContext)
    if (context === undefined) throw new Error('useFilters must be used within a FilterProvider')
    return context
}
