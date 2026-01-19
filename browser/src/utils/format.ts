import dayjs from 'dayjs'
import 'dayjs/locale/cs'

// Set locale globally
dayjs.locale('cs')

/**
 * Formats a numeric price into a localized currency string (CZK).
 * Handles null/undefined by returning an em-dash.
 * 
 * @param price The price to format
 * @returns Formatted string (e.g. "123,45 Kč") or "—"
 */
export const formatPrice = (price: number | null | undefined) => {
    if (price === null || price === undefined) return '—'
    return new Intl.NumberFormat('cs-CZ', {
        style: 'currency',
        currency: 'CZK',
        minimumFractionDigits: 2
    }).format(price)
}

/**
 * Formats a date string into a user-friendly relative or absolute format.
 * (e.g. "dnes", "zítra", "15. 1.")
 * 
 * @param dateStr ISO date string or compatible format
 * @returns Localized date string
 */
export const formatDate = (dateStr: string): string => {
    try {
        const d = dayjs(dateStr)
        if (!d.isValid()) return dateStr

        const now = dayjs()
        // Calculate difference in days between start of dates (ignoring time)
        const diffDays = d.startOf('day').diff(now.startOf('day'), 'day')

        if (diffDays === 0) return 'dnes'
        if (diffDays === 1) return 'zítra'

        return d.format('D. M.')
    } catch (e) {
        return dateStr
    }
}

/**
 * Formats a date range into a concise string.
 * Handles missing start/end dates gracefully.
 * 
 * @param start Start date string
 * @param end End date string
 * @returns Formatted range (e.g. "od 1. 1.", "do 5. 1.", "1. 1. – 5. 1.")
 */
export const formatDateRange = (start?: string | null, end?: string | null): string => {
    if (!start && !end) return ''

    const sFmt = start ? formatDate(start) : null
    const eFmt = end ? formatDate(end) : null

    // Both present
    if (sFmt && eFmt) {
        return `${sFmt} – ${eFmt}`
    }

    // Only end
    if (eFmt) {
        return `do ${eFmt}`
    }

    // Only start
    if (sFmt) {
        if (sFmt === 'dnes') return 'ode dneška'
        return `od ${sFmt}`
    }

    return ''
}
