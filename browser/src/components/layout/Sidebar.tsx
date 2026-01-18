import React from 'react'
import { FilterState, Source, CategoryNode } from '../../types'
import { FilterGroup } from '../filters/FilterGroup'
import { CategoryTree } from '../filters/CategoryTree'
import { SourceSelector } from '../filters/SourceSelector'

interface SidebarProps {
    sources: Source[]
    currentSource: Source | null
    onSourceChange: (name: string) => void
    filters: FilterState
    toggleFilter: (type: keyof FilterState, value: string) => void
    resetFilters: () => void
    clearSection: (type: keyof FilterState) => void
    brands: Record<string, number>
    stores: Record<string, number>
    categories: CategoryNode[]
    onTitleClick: (id: string) => void
}

export const Sidebar = ({
    sources,
    currentSource,
    onSourceChange,
    filters,
    toggleFilter,
    resetFilters,
    clearSection,
    brands,
    stores,
    categories,
    onTitleClick
}: SidebarProps) => {
    return (
        <aside>
            <SourceSelector
                sources={sources}
                currentSource={currentSource}
                onSourceChange={onSourceChange}
            />

            <div className="sidebar-header">
                <h2>Filters</h2>
                <button className="reset-button" onClick={resetFilters}>Clear All</button>
            </div>

            {Object.keys(stores).length > 1 && (
                <FilterGroup
                    title="Stores"
                    items={stores}
                    type="stores"
                    filters={filters}
                    toggleFilter={toggleFilter}
                    onClear={() => clearSection('stores')}
                />
            )}

            <CategoryTree
                categories={categories}
                filters={filters}
                toggleFilter={toggleFilter}
                onTitleClick={onTitleClick}
                onClear={() => clearSection('categories')}
            />

            <FilterGroup
                title="Brands"
                items={brands}
                type="brands"
                filters={filters}
                toggleFilter={toggleFilter}
                onClear={() => clearSection('brands')}
            />
        </aside>
    )
}
