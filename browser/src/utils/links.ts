export interface ProductLinkData {
    store: string
    url: string
}

export interface CategoryLinkData {
    source: string
    categoryId: string
    storeName?: string
    productUrl?: string
}

/**
 * Parses a deep link string into structured data for product navigation.
 * Expected format: product://<store>::<url>
 * 
 * @param href The full link string (e.g. "product://tesco::https://...")
 * @returns ProductLinkData object or null if invalid scheme/format
 */
export const parseProductLink = (href: string): ProductLinkData | null => {
    if (!href.startsWith('product://')) return null

    // Format: product://<encoded_store>::<encoded_url>
    const path = href.replace('product://', '')
    const [encStore, encUrl] = path.split('::')

    if (!encStore || !encUrl) return null

    try {
        return {
            store: decodeURIComponent(encStore),
            url: decodeURIComponent(encUrl)
        }
    } catch (e) {
        console.error("Failed to decode product link", href, e)
        return null
    }
}

/**
 * Parses a deep link string into structured data for category navigation.
 * Expected format: category://<source>::<categoryId>?store_name=<name>&product_url=<url>
 * 
 * @param href The full link string
 * @returns CategoryLinkData object or null if invalid scheme/format
 */
export const parseCategoryLink = (href: string): CategoryLinkData | null => {
    if (!href.startsWith('category://')) return null

    // Format: category://<source>::<categoryId>?store_name=<store>&product_url=<url>
    const rawPath = href.replace('category://', '')

    // Split query
    const [pathPart, queryPart] = rawPath.split('?')

    // Parse path (source::categoryId)
    const [encSource, encCategory] = pathPart.split('::')

    if (!encSource || !encCategory) return null

    try {
        const source = decodeURIComponent(encSource)
        const categoryId = encCategory // IDs often don't need decoding, but we take it as is

        let storeName: string | undefined = undefined
        let productUrl: string | undefined = undefined

        if (queryPart) {
            const params = new URLSearchParams(queryPart)
            const encStore = params.get('store_name')
            if (encStore) storeName = decodeURIComponent(encStore)

            const encProduct = params.get('product_url')
            if (encProduct) productUrl = decodeURIComponent(encProduct)
        }

        return {
            source,
            categoryId,
            storeName,
            productUrl
        }
    } catch (e) {
        console.error("Failed to decode category link", href, e)
        return null
    }
}
