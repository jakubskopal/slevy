
import { Link } from 'react-router-dom'
import { useFilters } from '../../context/FilterContext'
import { useData } from '../../context/DataContext'

interface HeaderProps {
    showControls?: boolean
}

export const Header = ({ showControls = true }: HeaderProps) => {
    const { sortOption, setSortOption, filteredCount } = useFilters()
    const { currentData } = useData()
    const totalCount = currentData?.metadata.total_products || 0

    // Helper to preserve params is now handled by FilterContext usually? 
    // Wait, Sidebar/Header links usually use `searchParams` directly.
    // getLink implementation needs `searchParams`.
    // We can use `useSearchParams` here locally or get it from context?
    // Using simple local `useSearchParams` is fine for Link generation.
    // Or we can ask FilterContext for `getLink` helper? 
    // FilterContext doesn't accept targetView arg in `updateParams`.

    // Let's implement getLink locally as before.
    // Import useSearchParams.

    return (
        <header>
            <HeaderContent showControls={showControls} sortOption={sortOption} setSortOption={setSortOption} filteredCount={filteredCount} totalCount={totalCount} />
        </header>
    )
}

import { useSearchParams } from 'react-router-dom'

const HeaderContent = ({ showControls, sortOption, setSortOption, filteredCount, totalCount }: any) => {
    const [searchParams] = useSearchParams()

    const getLink = (targetView?: string) => {
        const newParams = new URLSearchParams(searchParams)
        if (targetView) {
            newParams.set('view', targetView)
        } else {
            newParams.delete('view')
        }
        return `/?${newParams.toString()}`
    }

    return (
        <>
            <div className="header-left">
                <h1>Agravity Deals</h1>
                <nav className="header-nav" style={{ marginLeft: '2rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <Link to={getLink()} style={{ color: 'white', textDecoration: 'none' }}>Explore Data Sources</Link>
                    <Link to={getLink('analysis')} style={{ color: 'white', textDecoration: 'none' }}>Analysis</Link>
                </nav>
            </div>

            {showControls && (
                <div className="controls">
                    <select
                        value={sortOption}
                        onChange={(e) => setSortOption(e.target.value)}
                        className="sort-select"
                    >
                        <option value="default">Default Sort</option>
                        <option value="price-asc">Price: Low to High</option>
                        <option value="price-desc">Price: High to Low</option>
                        <option value="unit-asc">Unit Price: Low to High</option>
                        <option value="unit-desc">Unit Price: High to Low</option>
                    </select>
                    <div className="stats">
                        {filteredCount} filtered / {totalCount} total
                    </div>
                </div>
            )}
        </>
    )
}
