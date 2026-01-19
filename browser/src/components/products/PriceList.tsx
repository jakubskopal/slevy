import React, { useState, useMemo } from 'react'
import { Price } from '../../types'
import { formatPrice, formatDateRange } from '../../utils/format'
import { partitionPrices } from '../../utils/prices'

const PriceRow = ({ pr }: { pr: Price }) => (
    <div className="price-item">
        <div className="price-item-header">
            <div className="store-info">
                <span className="store-name">{pr.store_name}</span>
            </div>
            {(pr.validity || pr.validity_start || pr.validity_end) && (
                <span className="price-validity">
                    {formatDateRange(pr.validity_start, pr.validity_end) || pr.validity}
                </span>
            )}
        </div>

        {pr.condition && <div className="price-condition">{pr.condition}</div>}

        <div className="price-details">
            {/* Package Info */}
            {pr.package_size && (
                <span className="package-size">{pr.package_size}</span>
            )}

            <div className="price-values">
                <span className="price-main">
                    {formatPrice(pr.price)}
                </span>

                {/* Discount */}
                {pr.discount_pct && (
                    <span className="discount">-{pr.discount_pct}%</span>
                )}
            </div>
        </div>

        {/* Unit Price */}
        {(pr.unit_price) && (
            <div className="unit-price">
                ({formatPrice(pr.unit_price)} / {pr.unit || 'unit'})
            </div>
        )}
    </div>
)

export const PriceList = ({ prices, selectedStores }: { prices: Price[], selectedStores: Set<string> }) => {
    const [expanded, setExpanded] = useState(false)

    const { visible, hidden, hiddenRange } = useMemo(() => {
        return partitionPrices(prices, selectedStores)
    }, [prices, selectedStores])

    return (
        <div className="price-list">
            {visible.map((pr, idx) => <PriceRow key={idx} pr={pr} />)}

            {hidden.length > 0 && (
                <>
                    {!expanded ? (
                        <div className="more-offers" onClick={() => setExpanded(true)}>
                            +{hidden.length} more offers for {hiddenRange}
                        </div>
                    ) : (
                        hidden.map((pr, idx) => <PriceRow key={`h-${idx}`} pr={pr} />)
                    )}
                </>
            )}
        </div>
    )
}
