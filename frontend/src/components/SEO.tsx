import { useEffect } from 'react'

interface SEOProps {
  title?: string
  description?: string
  keywords?: string
  canonical?: string
  ogTitle?: string
  ogDescription?: string
  ogImage?: string
  ogUrl?: string
  twitterTitle?: string
  twitterDescription?: string
  twitterImage?: string
}

export default function SEO({
  title,
  description,
  keywords,
  canonical,
  ogTitle,
  ogDescription,
  ogImage = 'https://myaibaz.ir/og-image.jpg',
  ogUrl,
  twitterTitle,
  twitterDescription,
  twitterImage = 'https://myaibaz.ir/og-image.jpg',
}: SEOProps) {
  useEffect(() => {
    // Update document title
    if (title) {
      document.title = title
    }

    // Helper function to update or create meta tag
    const updateMetaTag = (name: string, content: string, attribute: string = 'name') => {
      if (!content) return
      
      let element = document.querySelector(`meta[${attribute}="${name}"]`) as HTMLMetaElement
      if (!element) {
        element = document.createElement('meta')
        element.setAttribute(attribute, name)
        document.head.appendChild(element)
      }
      element.setAttribute('content', content)
    }

    // Update meta tags
    if (description) {
      updateMetaTag('description', description)
    }

    if (keywords) {
      updateMetaTag('keywords', keywords)
    }

    // Update Open Graph tags
    if (ogTitle) {
      updateMetaTag('og:title', ogTitle, 'property')
    }

    if (ogDescription) {
      updateMetaTag('og:description', ogDescription, 'property')
    }

    if (ogImage) {
      updateMetaTag('og:image', ogImage, 'property')
    }

    if (ogUrl) {
      updateMetaTag('og:url', ogUrl, 'property')
    }

    // Set default OG tags if not already set
    const defaultOgType = document.querySelector('meta[property="og:type"]')
    if (!defaultOgType) {
      updateMetaTag('og:type', 'website', 'property')
    }

    const defaultOgLocale = document.querySelector('meta[property="og:locale"]')
    if (!defaultOgLocale) {
      updateMetaTag('og:locale', 'fa_IR', 'property')
    }

    const defaultOgSiteName = document.querySelector('meta[property="og:site_name"]')
    if (!defaultOgSiteName) {
      updateMetaTag('og:site_name', 'MyAibaz', 'property')
    }

    // Update Twitter Card tags
    if (twitterTitle) {
      updateMetaTag('twitter:title', twitterTitle)
    }

    if (twitterDescription) {
      updateMetaTag('twitter:description', twitterDescription)
    }

    if (twitterImage) {
      updateMetaTag('twitter:image', twitterImage)
    }

    // Set default Twitter Card type if not already set
    const defaultTwitterCard = document.querySelector('meta[name="twitter:card"]')
    if (!defaultTwitterCard) {
      updateMetaTag('twitter:card', 'summary_large_image')
    }

    // Update canonical link
    if (canonical) {
      let canonicalLink = document.querySelector('link[rel="canonical"]') as HTMLLinkElement
      if (!canonicalLink) {
        canonicalLink = document.createElement('link')
        canonicalLink.setAttribute('rel', 'canonical')
        document.head.appendChild(canonicalLink)
      }
      canonicalLink.setAttribute('href', canonical)
    }

    // Cleanup function (optional - restore defaults if needed)
    return () => {
      // You can restore default values here if needed
    }
  }, [title, description, keywords, canonical, ogTitle, ogDescription, ogImage, ogUrl, twitterTitle, twitterDescription, twitterImage])

  return null
}

