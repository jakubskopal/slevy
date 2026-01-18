import React, { useState } from 'react'
import { FilterState, CategoryNode } from '../../types'

interface CategoryNodeProps {
    node: CategoryNode
    filters: FilterState
    toggleFilter: (type: keyof FilterState, value: string) => void
    onTitleClick: (id: string) => void
}

const CategoryNodeItem = ({ node, filters, toggleFilter, onTitleClick }: CategoryNodeProps) => {
    const [isExpanded, setIsExpanded] = useState(false)
    const hasChildren = node.children && node.children.length > 0

    // Tri-state logic
    const isIncluded = filters.categories.has(node.id)
    const isExcluded = filters.excludeCategories.has(node.id)

    return (
        <div className="category-node">
            <div className="category-header">
                {hasChildren && (
                    <button
                        className={`expand-toggle ${isExpanded ? 'expanded' : ''}`}
                        onClick={() => setIsExpanded(!isExpanded)}
                        aria-label={isExpanded ? 'Collapse' : 'Expand'}
                    >
                        ▶
                    </button>
                )}
                <div className="filter-item" style={{ cursor: 'default' }}>
                    <input
                        type="checkbox"
                        checked={isIncluded || isExcluded}
                        onChange={() => toggleFilter('categories', node.id)}
                        className={isExcluded ? 'exclude' : ''}
                        style={{ cursor: 'pointer' }}
                    />
                    <span
                        className="category-title"
                        onClick={() => onTitleClick(node.id)}
                        style={{ cursor: 'pointer' }}
                    >
                        {node.name}
                    </span>
                    <span className="filter-count">{node.count}</span>
                </div>
            </div>
            {hasChildren && isExpanded && (
                <div className="category-children">
                    {node.children.map(child => (
                        <CategoryNodeItem
                            key={child.name}
                            node={child}
                            filters={filters}
                            toggleFilter={toggleFilter}
                            onTitleClick={onTitleClick}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}

interface CategoryTreeProps {
    categories: CategoryNode[]
    filters: FilterState
    toggleFilter: (type: keyof FilterState, value: string) => void
    onTitleClick: (id: string) => void
    onClear: () => void
}

export const CategoryTree = ({ categories, filters, toggleFilter, onTitleClick, onClear }: CategoryTreeProps) => {
    return (
        <div className="filter-section">
            <div className="section-header">
                <h3>Categories</h3>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="clear-link" onClick={onClear}>Clear All</button>
                </div>
            </div>
            <div className="filter-group">
                {categories.map(root => (
                    <CategoryNodeItem
                        key={root.name}
                        node={root}
                        filters={filters}
                        toggleFilter={toggleFilter}
                        onTitleClick={onTitleClick}
                    />
                ))}
            </div>
        </div>
    )
}
