import React from 'react'
import { Metadata } from '../../types'

interface HeaderProps {
    sortOption: string
    setSortOption: (val: string) => void
    filteredCount: number
    totalCount: number
}

export const Header = ({ sortOption, setSortOption, filteredCount, totalCount }: HeaderProps) => {
    return (
        <header>
            <div className="header-left">
                <h1>Agravity Deals</h1>
            </div>

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
        </header>
    )
}
