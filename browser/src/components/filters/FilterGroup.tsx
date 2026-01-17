import React from 'react'
import { FilterState } from '../../types'

interface FilterGroupProps {
    title: string
    items: Record<string, number>
    type: keyof FilterState
    filters: FilterState
    toggleFilter: (type: keyof FilterState, value: string) => void
    onClear: () => void
}

export const FilterGroup = ({ title, items, type, filters, toggleFilter, onClear }: FilterGroupProps) => (
    <div className="filter-section">
        <div className="section-header">
            <h3>{title}</h3>
            <button className="clear-link" onClick={onClear}>Clear</button>
        </div>
        <div className="filter-group">
            {Object.entries(items).map(([name, count]) => (
                <label key={name} className="filter-item">
                    <input
                        type="checkbox"
                        checked={filters[type].has(name)}
                        onChange={() => toggleFilter(type, name)}
                    />
                    <span>{name}</span>
                    <span className="filter-count">{count}</span>
                </label>
            ))}
        </div>
    </div>
)
