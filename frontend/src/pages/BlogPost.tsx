import { useParams, Link } from 'react-router-dom'
import SEO from '../components/SEO'
import Breadcrumbs from '../components/Breadcrumbs'
import ArticleSchema from '../components/ArticleSchema'
import { blogPostsData, getBlogPostBySlug } from '../data/blogPosts'

export default function BlogPost() {
  const { slug } = useParams<{ slug: string }>()
  
  // تست: بررسی slug از URL
  console.log('🔍 تست BlogPost - slug از useParams:', slug)
  console.log('🔍 تست BlogPost - تمام کلیدهای blogPostsData:', Object.keys(blogPostsData))
  
  const post = slug ? getBlogPostBySlug(slug) : null
  
  console.log('🔍 تست BlogPost - نتیجه getBlogPostBySlug:', post ? `مقاله یافت شد: ${post.title}` : 'مقاله یافت نشد')

  if (!post) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-4">مقاله یافت نشد</h1>
          <Link to="/blog" className="text-blue-400 hover:text-blue-300">
            بازگشت به بلاگ
          </Link>
        </div>
      </div>
    )
  }

  // Get related posts
  const relatedPosts = Object.values(blogPostsData)
    .filter((p) => p.id !== post.id)
    .slice(0, 3)

  return (
    <>
      <SEO
        title={`${post.title} | بلاگ ترید با هوش مصنوعی`}
        description={post.excerpt}
        keywords={`${post.title}, ترید با هوش مصنوعی, ترید به کمک هوش مصنوعی, ${post.category}`}
        canonical={`https://myaibaz.ir/blog/${post.slug}`}
        ogTitle={post.title}
        ogDescription={post.excerpt}
        ogImage={post.image}
        ogUrl={`https://myaibaz.ir/blog/${post.slug}`}
      />
      <ArticleSchema
        title={post.title}
        description={post.excerpt}
        author={post.author}
        datePublished={post.date}
        dateModified={post.dateModified || post.date}
        image={post.image}
        url={`https://myaibaz.ir/blog/${post.slug}`}
      />
      <div className="min-h-screen bg-gray-900 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Breadcrumbs items={[
            { label: 'خانه', path: '/' },
            { label: 'بلاگ', path: '/blog' },
            { label: post.title, path: `/blog/${post.slug}` }
          ]} />

          {/* Article Header */}
          <article className="bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
            <div className="relative h-64 md:h-96">
              <img
                src={post.image}
                alt={`تصویر اصلی مقاله: ${post.title} - ${post.category}`}
                className="w-full h-full object-cover"
                loading="lazy"
                width="800"
                height="400"
              />
              <div className="absolute top-4 right-4">
                <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                  {post.category}
                </span>
              </div>
            </div>

            <div className="p-6 md:p-8">
              <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
                {post.title}
              </h1>

              <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400 mb-6 pb-6 border-b border-gray-700">
                <span>نویسنده: {post.author}</span>
                <span>•</span>
                <span>{post.date}</span>
                <span>•</span>
                <span>{post.readTime} مطالعه</span>
              </div>

              {/* Article Content */}
              {post.content && (
                <div
                  className="prose prose-invert max-w-none text-gray-300 leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: post.content }}
                  style={{
                    direction: 'rtl',
                    textAlign: 'right'
                  }}
                />
              )}

              {/* CTA */}
              <div className="mt-8 pt-8 border-t border-gray-700">
                <div className="bg-gradient-to-r from-blue-900/50 to-purple-900/50 rounded-lg p-6 text-center">
                  <h3 className="text-xl font-bold text-white mb-3">
                    آماده شروع ترید با هوش مصنوعی هستید؟
                  </h3>
                  <p className="text-gray-300 mb-4">
                    همین حالا ثبت‌نام کنید و از قدرت AI در معاملات خود استفاده کنید
                  </p>
                  <Link
                    to="/login"
                    className="inline-block px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
                  >
                    شروع کنید
                  </Link>
                </div>
              </div>
            </div>
          </article>

          {/* Related Posts */}
          {relatedPosts.length > 0 && (
            <div className="mt-12">
              <h2 className="text-2xl font-bold text-white mb-6">مقالات مرتبط</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {relatedPosts.map((relatedPost) => (
                  <Link
                    key={relatedPost.id}
                    to={`/blog/${relatedPost.slug}`}
                    className="bg-gray-800 rounded-lg overflow-hidden hover:bg-gray-750 transition-all duration-200 shadow-lg hover:shadow-xl group"
                  >
                    <div className="relative h-32 overflow-hidden">
                      <img
                        src={relatedPost.image}
                        alt={`تصویر مقاله مرتبط: ${relatedPost.title}`}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        loading="lazy"
                        width="400"
                        height="200"
                      />
                    </div>
                    <div className="p-4">
                      <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors line-clamp-2">
                        {relatedPost.title}
                      </h3>
                      <p className="text-sm text-gray-400">{relatedPost.readTime}</p>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Back to Blog */}
          <div className="mt-8 text-center">
            <Link
              to="/blog"
              className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
            >
              ← بازگشت به بلاگ
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}

