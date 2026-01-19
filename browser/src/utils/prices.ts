import { Price } from '../types'
import { formatPrice } from './format'

export interface PartitionedPrices {
    visible: Price[]
    hidden: Price[]
    hiddenRange: string | null
}

/**
 * Partitions a list of prices into visible and hidden sets based on selected stores.
 * Also calculates a price range string for the hidden items.
 * 
 * @param prices Array of Price objects to process
 * @param selectedStores Set of store names that should be visible. If empty, all are visible.
 * @returns PartitionedPrices object containing visible list, hidden list, and a summary string for hidden prices.
 */
export const partitionPrices = (prices: Price[], selectedStores: Set<string>): PartitionedPrices => {
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
}
