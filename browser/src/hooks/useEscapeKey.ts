import { useEffect } from 'react'

/**
 * Hook that triggers a callback when the Escape key is pressed.
 * @param onEscape Callback function to run on Escape key press.
 */
export const useEscapeKey = (onEscape: () => void) => {
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                onEscape()
            }
        }

        window.addEventListener('keydown', handleKeyDown)

        return () => {
            window.removeEventListener('keydown', handleKeyDown)
        }
    }, [onEscape])
}
