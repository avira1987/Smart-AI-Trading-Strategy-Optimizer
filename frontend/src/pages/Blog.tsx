import { Link } from 'react-router-dom'
import SEO from '../components/SEO'
import Breadcrumbs from '../components/Breadcrumbs'
import { getBlogPostsArray } from '../data/blogPosts'

export default function Blog() {
  const blogPosts = getBlogPostsArray()
  
  // تست: بررسی تعداد مقالات
  console.log('🔍 تست - تعداد کل مقالات:', blogPosts.length)
  console.log('🔍 تست - لیست مقالات:', blogPosts.map((p, index) => `${index + 1}. ${p.title} (${p.slug})`))
  
  return (
    <>
      <SEO
        title="بلاگ | مقالات ترید با هوش مصنوعی | آموزش معاملات هوشمند"
        description="مقالات و راهنماهای جامع درباره ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی. یاد بگیرید چگونه از AI برای بهبود معاملات خود استفاده کنید."
        keywords="بلاگ ترید با هوش مصنوعی, مقالات معاملات هوشمند, آموزش ترید با AI, راهنمای ترید به کمک هوش مصنوعی"
        canonical="https://myaibaz.ir/blog"
        ogTitle="بلاگ ترید با هوش مصنوعی"
        ogDescription="مقالات و راهنماهای جامع درباره ترید با هوش مصنوعی"
        ogUrl="https://myaibaz.ir/blog"
      />
      <div className="min-h-screen bg-gray-900 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Breadcrumbs />
          
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
              بلاگ ترید با هوش مصنوعی
            </h1>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              مقالات و راهنماهای جامع درباره ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی
            </p>
            {/* تست: نمایش تعداد مقالات */}
            <div className="mt-4 p-4 bg-yellow-900/30 border border-yellow-600 rounded-lg">
              <p className="text-yellow-300 text-sm">
                🔍 تست: تعداد مقالات یافت شده: <strong className="text-yellow-200">{blogPosts.length}</strong>
              </p>
              <details className="mt-2 text-xs text-yellow-400">
                <summary className="cursor-pointer">لیست مقالات (کلیک کنید)</summary>
                <ul className="mt-2 text-right space-y-1">
                  {blogPosts.map((post, index) => (
                    <li key={post.id}>
                      {index + 1}. {post.title} ({post.slug})
                    </li>
                  ))}
                </ul>
              </details>
            </div>
          </div>

          {/* Blog Posts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            {blogPosts.map((post) => (
              <Link
                key={post.id}
                to={`/blog/${post.slug}`}
                className="bg-gray-800 rounded-xl overflow-hidden hover:bg-gray-750 transition-all duration-200 shadow-lg hover:shadow-xl group"
              >
                <div className="relative h-48 overflow-hidden">
                  <img
                    src={post.image}
                    alt={`تصویر مقاله: ${post.title} - ${post.category}`}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    loading="lazy"
                    width="800"
                    height="400"
                  />
                  <div className="absolute top-4 right-4">
                    <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-xs font-semibold">
                      {post.category}
                    </span>
                  </div>
                </div>
                <div className="p-6">
                  <div className="flex items-center gap-3 text-sm text-gray-400 mb-3">
                    <span>{post.date}</span>
                    <span>•</span>
                    <span>{post.readTime} مطالعه</span>
                  </div>
                  <h2 className="text-xl font-bold text-white mb-3 group-hover:text-blue-400 transition-colors">
                    {post.title}
                  </h2>
                  <p className="text-gray-300 leading-relaxed mb-4">
                    {post.excerpt}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">نویسنده: {post.author}</span>
                    <span className="text-blue-400 group-hover:text-blue-300 transition-colors text-sm font-semibold">
                      ادامه مطلب →
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {/* CTA Section */}
          <div className="bg-gradient-to-r from-blue-900/50 to-purple-900/50 rounded-xl p-8 text-center border border-blue-500/30">
            <h2 className="text-2xl font-bold text-white mb-4">
              آماده شروع ترید با هوش مصنوعی هستید؟
            </h2>
            <p className="text-gray-300 mb-6">
              همین حالا ثبت‌نام کنید و از قدرت هوش مصنوعی در معاملات خود بهره‌مند شوید
            </p>
            <Link
              to="/login"
              className="inline-block px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg"
            >
              شروع کنید
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}

