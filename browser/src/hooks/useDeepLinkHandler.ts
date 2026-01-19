import { Data, Product } from '../types'

interface DeepLinkHandlers {
    handleProductLink: (store: string, url: string) => void
    handleCategoryLink: (source: string, categoryId: string, storeName?: string, productUrl?: string) => void
}

/**
 * Hook to handle deep links for products and categories.
 * Centralizes the logic for searching and resolving potential targets across different data sources.
 * 
 * @param allData Map of all loaded store data
 * @param applyDeepLink Function to apply the deep link state (view switch, filters)
 * @param onProductFound Callback when a product is successfully resolved from a link
 * @returns Object containing handlers for product and category links
 */
export const useDeepLinkHandler = (
    allData: Record<string, Data>,
    applyDeepLink: (source: string, categoryId: string, storeName?: string) => void,
    onProductFound: (product: Product, sourceName: string) => void
): DeepLinkHandlers => {

    const handleProductLink = (store: string, url: string) => {
        if (allData[store]) {
            const product = allData[store].products.find(p => p.product_url === url)
            if (product) {
                onProductFound(product, store)
            } else {
                console.warn("Product not found in store data", url)
            }
        } else {
            console.warn("Store data not loaded or unknown", store)
        }
    }

    const handleCategoryLink = (source: string, categoryId: string, storeName?: string, productUrl?: string) => {
        applyDeepLink(source, categoryId, storeName)

        // If product URL is provided, try to open it
        if (productUrl) {
            const targetStore = storeName || (allData[source] ? source : undefined)

            if (targetStore && allData[targetStore]) {
                const product = allData[targetStore].products.find(p => p.product_url === productUrl)
                if (product) {
                    onProductFound(product, targetStore)
                }
            } else {
                // Fallback: search all loaded data for this product URL
                for (const [sKey, sData] of Object.entries(allData)) {
                    const product = sData.products.find(p => p.product_url === productUrl)
                    if (product) {
                        onProductFound(product, sKey)
                        break
                    }
                }
            }
        }
    }

    return {
        handleProductLink,
        handleCategoryLink
    }
}
