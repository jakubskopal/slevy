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
}

export interface Product {
    name: string
    brand: string | null
    image_url: string | null
    categories: string[]
    prices: Price[]
    description?: string | null
}

export interface Metadata {
    total_products: number
    generated_at: string
    brands: Record<string, number> | string[]
    categories: Record<string, number> | string[]
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
    stores: Set<string>
}

// Category Tree Node
export interface CategoryNodeDef {
    name: string
    count: number
    children: Record<string, CategoryNodeDef>
}
