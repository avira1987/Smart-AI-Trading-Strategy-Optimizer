import { useEffect } from 'react'

interface ArticleSchemaProps {
  title: string
  description: string
  author?: string
  datePublished?: string
  dateModified?: string
  image?: string
  url?: string
}

export default function ArticleSchema({
  title,
  description,
  author = 'تک ایده پویان',
  datePublished,
  dateModified,
  image = 'https://myaibaz.ir/og-image.jpg',
  url
}: ArticleSchemaProps) {
  useEffect(() => {
    const schema = {
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: title,
      description: description,
      author: {
        '@type': 'Person',
        name: author
      },
      publisher: {
        '@type': 'Organization',
        name: 'تک ایده پویان',
        logo: {
          '@type': 'ImageObject',
          url: 'https://myaibaz.ir/favicon.svg'
        }
      },
      image: Array.isArray(image) ? image : [image],
      datePublished: datePublished || new Date().toISOString(),
      dateModified: dateModified || new Date().toISOString(),
      mainEntityOfPage: {
        '@type': 'WebPage',
        '@id': url || window.location.href
      },
      inLanguage: 'fa-IR'
    }

    // Remove existing article schema
    const existingScript = document.querySelector('script[data-article-schema]')
    if (existingScript) {
      existingScript.remove()
    }

    // Add new article schema
    const script = document.createElement('script')
    script.type = 'application/ld+json'
    script.setAttribute('data-article-schema', 'true')
    script.textContent = JSON.stringify(schema)
    document.head.appendChild(script)

    return () => {
      const scriptToRemove = document.querySelector('script[data-article-schema]')
      if (scriptToRemove) {
        scriptToRemove.remove()
      }
    }
  }, [title, description, author, datePublished, dateModified, image, url])

  return null
}

