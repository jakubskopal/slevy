export const formatPrice = (price: number | null | undefined) => {
    if (price === null || price === undefined) return '—'
    return new Intl.NumberFormat('cs-CZ', {
        style: 'currency',
        currency: 'CZK',
        minimumFractionDigits: 2
    }).format(price)
}
