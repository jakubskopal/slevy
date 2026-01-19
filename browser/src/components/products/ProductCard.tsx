import React from 'react'
import { Product } from '../../types'
import { PriceList } from './PriceList'

interface ProductCardProps {
    product: Product
    selectedStores: Set<string>
    onProductClick: (p: Product) => void
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, selectedStores, onProductClick }) => {
    return (
        <div className="product-card">
            <div
                className="product-image-wrapper"
                onClick={() => onProductClick(product)}
                style={{ cursor: 'pointer' }}
            >
                <img
                    src={product.image_url || undefined}
                    alt={product.name}
                    className="product-image"
                    loading="lazy"
                    referrerPolicy="no-referrer"
                />
            </div>
            <div className="product-content">
                <div className="product-brand">{product.brand}</div>
                <h2
                    className="product-title"
                    onClick={() => onProductClick(product)}
                    style={{ cursor: 'pointer' }}
                >
                    {product.name}
                </h2>
                <div className="product-categories">
                    {product.categories.slice(0, 2).join(' › ')}
                </div>

                <PriceList prices={product.prices} selectedStores={selectedStores} />
            </div>
        </div>
    )
}
