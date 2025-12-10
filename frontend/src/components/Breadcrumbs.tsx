import { Link, useLocation } from 'react-router-dom'
import { useEffect } from 'react'

interface BreadcrumbItem {
  label: string
  path: string
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[]
}

export default function Breadcrumbs({ items }: BreadcrumbsProps) {
  const location = useLocation()

  // Generate breadcrumbs from path if items not provided
  const getBreadcrumbs = (): BreadcrumbItem[] => {
    if (items) return items

    const pathnames = location.pathname.split('/').filter((x) => x)
    const breadcrumbs: BreadcrumbItem[] = [
      { label: 'خانه', path: '/' }
    ]

    let currentPath = ''
    pathnames.forEach((name) => {
      currentPath += `/${name}`
      
      // Map path to Persian labels
      const labelMap: { [key: string]: string } = {
        'about': 'درباره ما',
        'tutorial': 'آموزش',
        'terms': 'قوانین و مقررات',
        'login': 'ورود',
        'blog': 'بلاگ',
        'guides': 'راهنما',
        'free-gold-api': 'راهنمای API طلای رایگان',
        'testing': 'تست استراتژی',
        'results': 'نتایج',
        'trading': 'معاملات زنده',
        'marketplace': 'بازار استراتژی',
        'tickets': 'تیکت‌ها',
        'profile': 'پروفایل',
        'admin': 'مدیریت',
        'security': 'امنیت',
        'users': 'کاربران',
        'settings': 'تنظیمات',
        'complete-profile': 'تکمیل پروفایل'
      }

      const label = labelMap[name] || name
      breadcrumbs.push({ label, path: currentPath })
    })

    return breadcrumbs
  }

  const breadcrumbs = getBreadcrumbs()

  // Add BreadcrumbList Schema.org
  useEffect(() => {
    const schema = {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: breadcrumbs.map((item, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        name: item.label,
        item: `https://myaibaz.ir${item.path}`
      }))
    }

    // Remove existing breadcrumb schema
    const existingScript = document.querySelector('script[data-breadcrumb-schema]')
    if (existingScript) {
      existingScript.remove()
    }

    // Add new breadcrumb schema
    const script = document.createElement('script')
    script.type = 'application/ld+json'
    script.setAttribute('data-breadcrumb-schema', 'true')
    script.textContent = JSON.stringify(schema)
    document.head.appendChild(script)

    return () => {
      const scriptToRemove = document.querySelector('script[data-breadcrumb-schema]')
      if (scriptToRemove) {
        scriptToRemove.remove()
      }
    }
  }, [breadcrumbs])

  if (breadcrumbs.length <= 1) return null

  return (
    <nav className="mb-4" aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2 space-x-reverse text-sm text-gray-400" style={{ direction: 'rtl' }}>
        {breadcrumbs.map((item, index) => (
          <li key={item.path} className="flex items-center">
            {index > 0 && (
              <svg
                className="w-4 h-4 mx-2 text-gray-500"
                fill="currentColor"
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            {index === breadcrumbs.length - 1 ? (
              <span className="text-gray-300 font-medium" aria-current="page">
                {item.label}
              </span>
            ) : (
              <Link
                to={item.path}
                className="hover:text-blue-400 transition-colors"
              >
                {item.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}

