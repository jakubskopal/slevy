import { SourceSelector } from '../filters/SourceSelector'
import { FilterGroup } from '../filters/FilterGroup'
import { CategoryTree } from '../filters/CategoryTree'
import { useData } from '../../context/DataContext'
import { useFilters } from '../../context/FilterContext'

export const Sidebar = () => {
    const { sources, currentSource, brandsMap, storesMap, currentData } = useData()
    const { filters, setSource, toggleFilter, toggleCategory, resetFilters, clearSection } = useFilters()

    const categories = currentData?.metadata.categories || []

    return (
        <aside className="sidebar">
            <SourceSelector
                sources={sources}
                currentSource={currentSource}
                onSourceChange={setSource}
            />

            {/* Stores */}
            <FilterGroup
                title="Stores"
                items={storesMap}
                type="stores"
                filters={filters}
                toggleFilter={toggleFilter}
                onClear={() => clearSection('stores')}
            />

            {/* Categories */}
            <CategoryTree
                categories={categories}
                filters={filters}
                toggleFilter={toggleFilter}
                onTitleClick={(id) => toggleCategory(id, true)}
                onClear={() => clearSection('categories')}
            />

            {/* Brands */}
            <FilterGroup
                title="Brands"
                items={brandsMap}
                type="brands"
                filters={filters}
                toggleFilter={toggleFilter}
                onClear={() => clearSection('brands')}
            />

            <button className="reset-btn" onClick={resetFilters}>
                Reset All Filters
            </button>
        </aside>
    )
}
