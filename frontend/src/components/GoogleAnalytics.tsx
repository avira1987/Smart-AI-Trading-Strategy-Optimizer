import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

// Google Analytics 4 component
// This component tracks page views when routes change in React Router
// The main Google Analytics script is loaded in index.html
export default function GoogleAnalytics() {
  const location = useLocation()
  const measurementId = 'G-QEG36LQTJ4' // Hardcoded since it's also in index.html

  // Track page views on route change
  useEffect(() => {
    // Wait for gtag to be available (loaded from index.html)
    if (typeof window === 'undefined' || !(window as any).gtag) {
      return
    }

    // Track page view when route changes
    ;(window as any).gtag('config', measurementId, {
      page_path: location.pathname + location.search,
      page_title: document.title,
    })
  }, [location])

  return null
}


