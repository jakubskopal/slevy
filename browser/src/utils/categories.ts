export const FOOD_CATEGORIES = new Set([
    // Fresh
    "Ovoce a zelenina", "OVOCE A ZELENINA",
    "Maso, uzeniny a ryby", "MASO A RYBY", "Maso a lahůdky",
    "Mléčné výrobky a vejce", "MLÉČNÉ A CHLAZENÉ", "Mléčné, vejce a margaríny",
    "Pečivo", "PEKÁRNA A CUKRÁRNA", "Pekárna", "PEČIVO",

    // Pantry / Cooking
    "Trvanlivé", "TRVANLIVÉ",
    "Konzervy",
    "Vaření a pečení",
    "Zdravá výživa", "Speciální výživa",

    // Snacks / Ready Meals
    "Lahůdky", "UZENINY A LAHŮDKY",
    "Sladkosti a slané snacky",

    // Frozen
    "Mražené a instantní potraviny", "MRAŽENÉ POTRAVINY", "Mražené"
])

export const isFoodCategory = (category: string) => {
    return FOOD_CATEGORIES.has(category)
}
