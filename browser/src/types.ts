export interface Price {
    store_name: string
    price: number | null
    unit_price: number | null
    unit: string | null
    package_size: string | null
    condition: string | null
    discount_pct?: number | null
    original_price?: number | null
    validity?: string | null
    validity_start?: string | null
    validity_end?: string | null
}

export interface Product {
    name: string
    brand: string | null
    image_url: string | null
    categories: string[]
    category_ids: string[]
    prices: Price[]
    description?: string | null
    product_url?: string | null
    ai_findings?: string[]
}

export interface Metadata {
    total_products: number
    generated_at: string
    brands: Record<string, number> | string[]
    categories: CategoryNode[]
    stores: Record<string, number> | string[]
}

export interface Data {
    products: Product[]
    metadata: Metadata
}

export interface Source {
    name: string
    file: string
}

export interface FilterState {
    brands: Set<string>
    categories: Set<string>
    excludeCategories: Set<string>
    stores: Set<string>
}

// Category Tree Node
export interface CategoryNode {
    id: string
    name: string
    count: number
    children: CategoryNode[]
}
