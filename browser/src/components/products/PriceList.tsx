import React, { useState, useMemo } from 'react'
import { Price } from '../../types'
import { formatPrice } from '../../utils/format'

const PriceRow = ({ pr }: { pr: Price }) => (
    <div className="price-item">
        <div className="price-item-header">
            <div className="store-info">
                <span className="store-name">{pr.store_name}</span>
            </div>
            {pr.validity && <span className="price-validity">{pr.validity}</span>}
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
        // 1. Sort all by unit price ascending
        const sorted = [...prices].sort((a, b) => {
            const upA = a.unit_price ?? Infinity
            const upB = b.unit_price ?? Infinity
            return upA - upB
        })

        // 2. If no stores selected, show all
        if (selectedStores.size === 0) {
            return { visible: sorted, hidden: [], hiddenRange: null }
        }

        // 3. Filter
        const visible: Price[] = []
        const hidden: Price[] = []

        sorted.forEach(p => {
            if (selectedStores.has(p.store_name)) {
                visible.push(p)
            } else {
                hidden.push(p)
            }
        })

        let hiddenRange: string | null = null
        if (hidden.length > 0) {
            const vals = hidden.map(p => p.price).filter((v): v is number => v !== null)
            if (vals.length > 0) {
                const min = Math.min(...vals)
                const max = Math.max(...vals)
                hiddenRange = min === max ? formatPrice(min) : `${formatPrice(min)} - ${formatPrice(max)}`
            } else {
                hiddenRange = "unknown price"
            }
        }

        return { visible, hidden, hiddenRange }
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
