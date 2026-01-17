import React from 'react'
import { Product } from '../../types'
import { PriceList } from './PriceList'

interface ProductCardProps {
    product: Product
    selectedStores: Set<string>
}

export const ProductCard = ({ product, selectedStores }: ProductCardProps) => {
    return (
        <div className="product-card">
            <img
                src={product.image_url || undefined}
                alt={product.name}
                className="product-image"
                loading="lazy"
                referrerPolicy="no-referrer"
            />
            <div className="product-content">
                <div className="product-brand">{product.brand}</div>
                <h2 className="product-title">{product.name}</h2>
                <div className="product-categories">
                    {product.categories.join(' › ')}
                </div>

                <PriceList prices={product.prices} selectedStores={selectedStores} />
            </div>
        </div>
    )
}
