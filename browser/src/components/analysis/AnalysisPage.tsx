import { useState, useEffect, useRef } from 'react'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import 'github-markdown-css/github-markdown.css'
import { Loading } from '../common/Loading'
import { parseCategoryLink, parseProductLink } from '../../utils/links'

interface AnalysisPageProps {
    onProductLink?: (store: string, url: string) => void
    onCategoryLink?: (source: string, categoryId: string, storeName?: string, productUrl?: string) => void
    initialScrollY?: number
    onSaveScrollY?: (y: number) => void
}

export function AnalysisPage({
    onProductLink,
    onCategoryLink,
    initialScrollY = 0,
    onSaveScrollY
}: AnalysisPageProps) {
    const [content, setContent] = useState<string>('')
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Callback ref to ensure we always use the latest handler on unmount
    const saveSortRef = useRef(onSaveScrollY)
    saveSortRef.current = onSaveScrollY

    // Scroll Restoration
    useEffect(() => {
        if (!isLoading && initialScrollY > 0) {
            // Slight delay to ensure layout is stable
            setTimeout(() => window.scrollTo(0, initialScrollY), 100)
        }
    }, [isLoading, initialScrollY])

    // Scroll Saving (On Unmount)
    useEffect(() => {
        return () => {
            if (saveSortRef.current) {
                saveSortRef.current(window.scrollY)
            }
        }
    }, [])

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

    // Custom Link Renderer to intercept product:// and category:// links
    const components = {
        a: ({ node, ...props }: any) => {
            const href = props.href || ''

            const productData = parseProductLink(href)
            if (productData) {
                return (
                    <a
                        {...props}
                        href="#"
                        onClick={(e) => {
                            e.preventDefault()
                            if (onProductLink) {
                                onProductLink(productData.store, productData.url)
                            } else {
                                console.warn("Missing handler for product link", href)
                            }
                        }}
                        style={{ color: '#58a6ff', textDecoration: 'none', cursor: 'pointer', fontWeight: 'bold' }}
                    >
                        {props.children}
                    </a>
                )
            }

            const categoryData = parseCategoryLink(href)
            if (categoryData) {
                return (
                    <a
                        {...props}
                        href="#"
                        onClick={(e) => {
                            e.preventDefault()
                            if (onCategoryLink) {
                                onCategoryLink(
                                    categoryData.source,
                                    categoryData.categoryId,
                                    categoryData.storeName,
                                    categoryData.productUrl
                                )
                            } else {
                                console.warn("Missing handler for category link", href)
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
                            if (uri.startsWith('category://')) return uri
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
