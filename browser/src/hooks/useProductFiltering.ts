import { useMemo } from 'react'
import { Data, FilterState, Product } from '../types'

/**
 * Custom hook to filter and sort products based on the current filter state.
 * Memoizes the result to prevent unnecessary recalculations.
 * 
 * @param currentData The currently loaded data source
 * @param filters Current active filters (brands, categories, stores)
 * @param sortOption Current sort mode (e.g. 'price-asc')
 * @returns Array of filtered and sorted Product objects
 */
export const useProductFiltering = (
    currentData: Data | null,
    filters: FilterState,
    sortOption: string
) => {
    return useMemo(() => {
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
}
