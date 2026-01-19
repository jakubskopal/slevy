import React from 'react'
import { Product } from '../../types'
import { PriceList } from './PriceList'
import { formatPrice } from '../../utils/format'
import { useEscapeKey } from '../../hooks/useEscapeKey'

interface ProductDetailProps {
    product: Product
    dataSourceName: string
    onClose: () => void
}

export const ProductDetail: React.FC<ProductDetailProps> = ({ product, dataSourceName, onClose }) => {
    // Stop propagation when clicking modal content to prevent closing
    const handleContentClick = (e: React.MouseEvent) => {
        e.stopPropagation()
    }

    // Close on Escape key
    useEscapeKey(onClose)

    // Determine brand info
    const brand = product.brand || 'Unknown Brand'

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={handleContentClick}>
                <button className="modal-close" onClick={onClose}>
                    &times;
                </button>

                <div className="modal-header">
                    <span className="modal-brand">{brand}</span>
                    <h2 className="modal-title">{product.name}</h2>
                    <div className="modal-categories">
                        {[
                            dataSourceName,
                            ...product.categories
                        ].join(' > ')}
                    </div>
                </div>

                <div className="modal-body">
                    <div className="modal-image-container">
                        {product.image_url ? (
                            <img
                                src={product.image_url}
                                alt={product.name}
                                className="modal-image"
                            />
                        ) : (
                            <div className="modal-no-image">No Image</div>
                        )}
                    </div>

                    <div className="modal-details">
                        {product.description && (
                            <div className="modal-section">
                                <h3>Description</h3>
                                <p className="modal-description">{product.description}</p>
                            </div>
                        )}

                        {product.product_url && (
                            <div className="modal-section">
                                <a
                                    href={product.product_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="modal-external-link"
                                >
                                    View on Store Website &rarr;
                                </a>
                            </div>
                        )}

                        <div className="modal-section">
                            <h3>Price Offers</h3>
                            {/* Pass empty set to show ALL prices */}
                            <PriceList prices={product.prices} selectedStores={new Set()} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
