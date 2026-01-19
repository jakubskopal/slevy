
import { createContext, useContext, useState, useEffect, ReactNode, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Data, Source, Product } from '../types'

interface DataContextType {
    sources: Source[]
    allData: Record<string, Data>
    isLoading: boolean
    currentData: Data | null
    currentSource: Source | null
    storesMap: Record<string, number>
    brandsMap: Record<string, number>
}

const DataContext = createContext<DataContextType | undefined>(undefined)

export function DataProvider({ children }: { children: ReactNode }) {
    const [sources, setSources] = useState<Source[]>([])
    const [allData, setAllData] = useState<Record<string, Data>>({})
    const [isLoading, setIsLoading] = useState(true)
    const [searchParams] = useSearchParams()

    // Initial Load
    useEffect(() => {
        const loadAll = async () => {
            try {
                const idxRes = await fetch('index.json')
                const idx = await idxRes.json()

                if (idx.sources && idx.sources.length > 0) {
                    setSources(idx.sources)
                    const promises = idx.sources.map((s: Source) =>
                        fetch(s.file).then(r => r.json()).then(data => ({ name: s.name, data }))
                    )
                    const results = await Promise.all(promises)
                    const dataMap: Record<string, Data> = {}
                    results.forEach((r: any) => dataMap[r.name] = r.data)
                    setAllData(dataMap)
                }
            } catch (e) {
                console.error("Failed to load data", e)
            } finally {
                setIsLoading(false)
            }
        }
        loadAll()
    }, [])

    const sourceName = searchParams.get('source')
    const currentData = (sourceName && allData[sourceName]) ? allData[sourceName] : null
    const currentSource = sources.find(s => s.name === sourceName) || null

    // Derived Metadata Helpers
    const { brands: bRaw, stores: sRaw } = currentData?.metadata || {}
    const ensureCountObject = (val: any): Record<string, number> => {
        if (!val) return {}
        if (Array.isArray(val)) {
            return val.reduce((acc: Record<string, number>, item: string) => {
                acc[item] = 0
                return acc
            }, {})
        }
        return val
    }
    const brandsMap = useMemo(() => ensureCountObject(bRaw), [bRaw])
    const storesMap = useMemo(() => ensureCountObject(sRaw), [sRaw])

    const value = { sources, allData, isLoading, currentData, currentSource, brandsMap, storesMap }

    return <DataContext.Provider value={value}>{children}</DataContext.Provider>
}

export const useData = () => {
    const context = useContext(DataContext)
    if (context === undefined) throw new Error('useData must be used within a DataProvider')
    return context
}
