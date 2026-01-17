import React from 'react'
import { Source } from '../../types'

interface SourceSelectorProps {
    sources: Source[]
    currentSource: Source | null
    onSourceChange: (sourceName: string) => void
}

export const SourceSelector = ({ sources, currentSource, onSourceChange }: SourceSelectorProps) => {
    if (sources.length === 0) return null

    return (
        <div className="filter-section source-selection">
            <div className="section-header">
                <h3>Data Source</h3>
            </div>
            <div className="filter-group">
                <select
                    value={currentSource?.name || ''}
                    onChange={(e) => onSourceChange(e.target.value)}
                    className="source-select-input"
                    style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
                >
                    {sources.map(s => (
                        <option key={s.name} value={s.name}>{s.name.toUpperCase()}</option>
                    ))}
                </select>
            </div>
        </div>
    )
}
