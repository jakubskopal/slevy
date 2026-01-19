import { useState, useEffect } from 'react'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import 'github-markdown-css/github-markdown.css'
import { Loading } from '../common/Loading'

interface AnalysisPageProps {
    onProductLink?: (store: string, url: string) => void
}

export function AnalysisPage({ onProductLink }: AnalysisPageProps) {
    const [content, setContent] = useState<string>('')
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        // Fetch from root public directory
        fetch('/nutrition.analysis.md')
            .then(res => {
                if (!res.ok) throw new Error('Failed to load analysis report')
                return res.text()
            })
            .then(text => {
                setContent(text)
                setIsLoading(false)
            })
            .catch(err => {
                console.error(err)
                setError('Failed to load nutrition analysis. Please try again later.')
                setIsLoading(false)
            })
    }, [])

    if (isLoading) return <Loading />
    if (error) return <div className="error">{error}</div>

    // Custom Link Renderer to intercept product:// links
    const components = {
        a: ({ node, ...props }: any) => {
            const href = props.href || ''
            if (href.startsWith('product://')) {
                return (
                    <a
                        {...props}
                        href="#"
                        onClick={(e) => {
                            e.preventDefault()
                            // Format: product://<encoded_store>::<encoded_url>
                            const path = href.replace('product://', '')
                            const [encStore, encUrl] = path.split('::')

                            if (encStore && encUrl && onProductLink) {
                                try {
                                    const store = decodeURIComponent(encStore)
                                    const url = decodeURIComponent(encUrl)
                                    onProductLink(store, url)
                                } catch (e) {
                                    console.error("Failed to decode product link", href, e)
                                }
                            } else {
                                console.warn("Invalid product link or missing handler", href)
                            }
                        }}
                        style={{ color: '#58a6ff', textDecoration: 'none', cursor: 'pointer', fontWeight: 'bold' }}
                    >
                        {props.children}
                    </a>
                )
            }
            // Fallback for normal links
            return <a {...props} target="_blank" rel="noopener noreferrer" style={{ color: '#58a6ff' }} />
        }
    }

    return (
        <div className="analysis-page" style={{ minHeight: '100vh', backgroundColor: '#0d1117' }}>

            <div className="container analysis-container" style={{ paddingBottom: '4rem' }}>
                <main className="markdown-body" style={{
                    maxWidth: '900px',
                    margin: '0 auto',
                    padding: '2rem',
                    backgroundColor: '#0d1117',
                    color: '#c9d1d9',
                    fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif'
                }}>
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={components}
                        urlTransform={(uri) => {
                            if (uri.startsWith('product://')) return uri
                            return uri
                        }}
                    >
                        {content}
                    </ReactMarkdown>
                </main>
            </div>
        </div>
    )
}
