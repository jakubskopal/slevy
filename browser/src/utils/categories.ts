export const FOOD_KEYWORDS = [
    "potraviny",
    "ovoce", "zelenina", "bylinky", "houby",
    "maso", "ryby", "drůbež", "uzeniny", "šunka", "salám", "klobás", "párky", "paštiky",
    "mléč", "sýr", "jogurt", "tvaroh", "máslo", "tuky", "vejce", "smetan",
    "pečivo", "pekárn", "chléb", "chleb", "rohlík", "koláč", "bábovk", "baget",
    "trvanlivé", "konzerv", "zavař", "džem", "med", "sirup",
    "vaření", "pečení", "těstoviny", "rýže", "luštěniny", "mouka", "cukr", "sůl", "olej", "ocet", "koření",
    "lahůdky", "pomazán", "salát",
    "mražené", "zmrzlin", "hotová jídla", "polotovary", "pizza",
    "zdravá výživa", "speciální výživa", "cereálie", "müsli", "kaše"
]

export const NON_FOOD_KEYWORDS = [
    "krmivo", "zvířata", "psi", "kočky", "pes", "kočka", "mazlíčci",
    "drogerie", "kosmetika", "hygiena", "domácnost", "úklid", "papír", "tablety", "ubrousky",
    "sladkosti", "cukrovinky", "bonbony", "čokoláda", "oplatky", "sušenky",
    "protein", "čajové", "sladké"
]

export const isFoodCategory = (category: string) => {
    const lower = category.toLowerCase()

    // Check exclusion first
    if (NON_FOOD_KEYWORDS.some(kw => lower.includes(kw))) {
        return false
    }

    // Check inclusion
    return FOOD_KEYWORDS.some(kw => lower.includes(kw))
}
