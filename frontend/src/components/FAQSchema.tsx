import { useEffect } from 'react'

interface FAQItem {
  question: string
  answer: string
}

interface FAQSchemaProps {
  faqs: FAQItem[]
}

export default function FAQSchema({ faqs }: FAQSchemaProps) {
  useEffect(() => {
    if (!faqs || faqs.length === 0) return

    const schema = {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: faqs.map((faq) => ({
        '@type': 'Question',
        name: faq.question,
        acceptedAnswer: {
          '@type': 'Answer',
          text: faq.answer
        }
      }))
    }

    // Remove existing FAQ schema
    const existingScript = document.querySelector('script[data-faq-schema]')
    if (existingScript) {
      existingScript.remove()
    }

    // Add new FAQ schema
    const script = document.createElement('script')
    script.type = 'application/ld+json'
    script.setAttribute('data-faq-schema', 'true')
    script.textContent = JSON.stringify(schema)
    document.head.appendChild(script)

    return () => {
      const scriptToRemove = document.querySelector('script[data-faq-schema]')
      if (scriptToRemove) {
        scriptToRemove.remove()
      }
    }
  }, [faqs])

  return null
}

