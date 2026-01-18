import React, { useState, useMemo } from 'react'
import { FilterState, CategoryNodeDef, Product } from '../../types'

interface CategoryNodeProps {
    node: CategoryNodeDef
    filters: FilterState
    toggleFilter: (type: keyof FilterState, value: string) => void
    hasSelectedParent?: boolean
}

const CategoryNode = ({ node, filters, toggleFilter, hasSelectedParent = false }: CategoryNodeProps) => {
    const [isExpanded, setIsExpanded] = useState(false)
    const hasChildren = Object.keys(node.children).length > 0
    const isChecked = filters.categories.has(node.name)
    const isExcluding = isChecked && hasSelectedParent

    const sortedChildren = useMemo(() => {
        return Object.values(node.children).sort((a, b) => a.name.localeCompare(b.name, 'cs'))
    }, [node.children])

    return (
        <div key={node.name} className="category-node">
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
                <label className="filter-item">
                    <input
                        type="checkbox"
                        className={isExcluding ? 'exclude' : ''}
                        checked={isChecked}
                        onChange={() => toggleFilter('categories', node.name)}
                    />
                    <span>{node.name}</span>
                    <span className="filter-count">{node.count}</span>
                </label>
            </div>
            {hasChildren && isExpanded && (
                <div className="category-children">
                    {sortedChildren.map(child => (
                        <CategoryNode
                            key={child.name}
                            node={child}
                            filters={filters}
                            toggleFilter={toggleFilter}
                            hasSelectedParent={hasSelectedParent || isChecked}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}

import { isFoodCategory } from '../../utils/categories'

// ... existing code ...

interface CategoryTreeProps {
    products: Product[]
    filters: FilterState
    toggleFilter: (type: keyof FilterState, value: string) => void
    setFilterSet: (type: keyof FilterState, values: Set<string>) => void
    onClear: () => void
}

export const CategoryTree = ({ products, filters, toggleFilter, setFilterSet, onClear }: CategoryTreeProps) => {
    // Build Tree (Memoized)
    const tree = useMemo(() => {
        const t: Record<string, CategoryNodeDef> = {}
        products.forEach(p => {
            const cats = p.categories
            if (!cats || cats.length === 0) return

            let currentLevel: Record<string, CategoryNodeDef> = t
            cats.forEach((c) => {
                if (!currentLevel[c]) {
                    currentLevel[c] = { name: c, count: 0, children: {} }
                }
                currentLevel[c].count += 1
                currentLevel = currentLevel[c].children
            })
        })
        return t
    }, [products])

    // Sort and Group
    const { foodRoots, otherRoots } = useMemo(() => {
        const food: CategoryNodeDef[] = []
        const other: CategoryNodeDef[] = []

        Object.values(tree).forEach(node => {
            if (isFoodCategory(node.name)) {
                food.push(node)
            } else {
                other.push(node)
            }
        })

        const sortFn = (a: CategoryNodeDef, b: CategoryNodeDef) => a.name.localeCompare(b.name, 'cs')

        return {
            foodRoots: food.sort(sortFn),
            otherRoots: other.sort(sortFn)
        }
    }, [tree])

    // Preset Handlers
    const selectFoodOnly = () => {
        const foodSet = new Set<string>()
        foodRoots.forEach(root => foodSet.add(root.name))
        setFilterSet('categories', foodSet)
    }

    return (
        <div className="filter-section">
            <div className="section-header">
                <h3>Categories</h3>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        className="preset-link"
                        onClick={selectFoodOnly}
                        title="Select only food categories"
                    >
                        Food
                    </button>
                    <button className="clear-link" onClick={onClear}>All</button>
                </div>
            </div>
            <div className="filter-group">
                {foodRoots.map(root => (
                    <CategoryNode
                        key={root.name}
                        node={root}
                        filters={filters}
                        toggleFilter={toggleFilter}
                    />
                ))}

                {foodRoots.length > 0 && otherRoots.length > 0 && (
                    <div className="category-divider" />
                )}

                {otherRoots.map(root => (
                    <CategoryNode
                        key={root.name}
                        node={root}
                        filters={filters}
                        toggleFilter={toggleFilter}
                    />
                ))}
            </div>
        </div>
    )
}
