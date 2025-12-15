// Utility functions for tracking blog post views

const VIEWS_STORAGE_KEY = 'blog_post_views'

interface BlogViews {
  [slug: string]: number
}

/**
 * Get all view counts from localStorage
 */
export function getBlogViews(): BlogViews {
  if (typeof window === 'undefined') {
    return {}
  }

  try {
    const stored = localStorage.getItem(VIEWS_STORAGE_KEY)
    if (!stored) {
      return {}
    }
    return JSON.parse(stored) as BlogViews
  } catch (error) {
    console.error('Error reading blog views from localStorage:', error)
    return {}
  }
}

/**
 * Get view count for a specific blog post
 */
export function getBlogViewCount(slug: string): number {
  const views = getBlogViews()
  return views[slug] || 0
}

/**
 * Increment view count for a blog post
 */
export function incrementBlogView(slug: string): void {
  if (typeof window === 'undefined') {
    return
  }

  try {
    const views = getBlogViews()
    views[slug] = (views[slug] || 0) + 1
    localStorage.setItem(VIEWS_STORAGE_KEY, JSON.stringify(views))
  } catch (error) {
    console.error('Error saving blog view to localStorage:', error)
  }
}

/**
 * Format view count for display (e.g., 1234 -> "1.2K")
 */
export function formatViewCount(count: number): string {
  if (count < 1000) {
    return count.toString()
  }
  if (count < 1000000) {
    return (count / 1000).toFixed(1) + 'K'
  }
  return (count / 1000000).toFixed(1) + 'M'
}

