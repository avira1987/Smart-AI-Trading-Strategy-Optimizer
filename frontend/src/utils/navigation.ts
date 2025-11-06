/**
 * Navigation utility for use outside React components (e.g., in axios interceptors)
 */
let navigateFunction: ((path: string) => void) | null = null
let isNavigating = false // Flag to prevent multiple simultaneous navigation calls
let pendingNavigation: string | null = null // Queue for navigation if navigateFunction isn't ready yet

export const setNavigate = (navigate: (path: string) => void) => {
  navigateFunction = navigate
  
  // Process any pending navigation
  if (pendingNavigation) {
    navigateFunction(pendingNavigation)
    pendingNavigation = null
  }
}

export const navigateTo = (path: string) => {
  // Prevent multiple simultaneous navigation calls
  if (isNavigating) {
    console.warn('Navigation already in progress, skipping duplicate call')
    return
  }

  if (navigateFunction) {
    isNavigating = true
    try {
      navigateFunction(path)
    } finally {
      // Reset flag after a short delay to allow navigation to complete
      setTimeout(() => {
        isNavigating = false
      }, 100)
    }
  } else {
    // Queue the navigation if navigateFunction isn't ready yet
    // This prevents page refreshes and ensures navigation happens once React Router is ready
    console.warn('Navigate function not set yet, queuing navigation:', path)
    pendingNavigation = path
    
    // As a last resort, if navigateFunction isn't set after 500ms, 
    // use a safer method that doesn't cause full page refresh
    setTimeout(() => {
      if (!navigateFunction && pendingNavigation === path) {
        console.warn('Navigation function still not set after delay, using safe fallback')
        // Only change pathname if we're not already there
        if (window.location.pathname !== path) {
          // Use replaceState to avoid adding to history, but don't trigger full reload
          window.history.replaceState({}, '', path)
        }
        pendingNavigation = null
      }
    }, 500)
  }
}

