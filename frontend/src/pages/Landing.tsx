import { Link } from 'react-router-dom'
import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useFeatureFlags } from '../context/FeatureFlagsContext'
import SEO from '../components/SEO'
import FAQSchema from '../components/FAQSchema'

export default function Landing() {
  const { isAuthenticated } = useAuth()
  const { liveTradingEnabled } = useFeatureFlags()
  const [shouldLoadVideo, setShouldLoadVideo] = useState(false)
  const videoRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setShouldLoadVideo(true)
            observer.disconnect()
          }
        })
      },
      { rootMargin: '100px' } // شروع لود 100px قبل از رسیدن به ویدیو
    )

    if (videoRef.current) {
      observer.observe(videoRef.current)
    }

    return () => observer.disconnect()
  }, [])

  return (
    <>
      <SEO
        title="ترید با هوش مصنوعی | ترید به کمک هوش مصنوعی | سامانه معاملات هوشمند AI"
        description="ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی - سامانه پیشرفته معاملات هوشمند با AI. بهینه‌سازی استراتژی‌های معاملاتی با هوش مصنوعی، بک‌تست خودکار و معاملات هوشمند فارکس"
        keywords="ترید با هوش مصنوعی, ترید به کمک هوش مصنوعی, معاملات هوشمند, AI Trading, ترید هوشمند, معاملات با AI"
        canonical="https://myaibaz.ir/"
        ogTitle="ترید با هوش مصنوعی | ترید به کمک هوش مصنوعی"
        ogDescription="ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی - سامانه پیشرفته معاملات هوشمند"
        ogUrl="https://myaibaz.ir/"
      />
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
              ترید با هوش مصنوعی | ترید به کمک هوش مصنوعی
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
              سامانه پیشرفته ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی. با استفاده از هوش مصنوعی، استراتژی‌های معاملاتی خود را بهینه کنید و معاملات هوشمند خودکار انجام دهید. برای یادگیری بیشتر، <Link to="/blog" className="text-blue-400 hover:text-blue-300 underline">مقالات بلاگ</Link> ما را مطالعه کنید.
            </p>
            
            {/* Video Section - Optimized with Lazy Loading */}
            <div ref={videoRef} className="mb-8 max-w-4xl mx-auto">
              {shouldLoadVideo ? (
                <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-blue-500/30 bg-gray-900/50 backdrop-blur-sm">
                  <video
                    className="w-full h-auto"
                    controls
                    preload="metadata"
                    playsInline
                  >
                    <source src="/pro_vid.mp4" type="video/mp4" />
                    مرورگر شما از پخش ویدیو پشتیبانی نمی‌کند.
                  </video>
                </div>
              ) : (
                <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-blue-500/30 bg-gray-900/50 backdrop-blur-sm aspect-video flex items-center justify-center">
                  <div className="text-gray-400 text-lg animate-pulse">
                    <svg className="w-16 h-16 mx-auto mb-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p>در حال بارگذاری ویدیو...</p>
                  </div>
                </div>
              )}
            </div>

            {!isAuthenticated && (
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Link
                  to="/login"
                  className="px-8 py-4 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 active:scale-95 text-white text-lg font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                >
                  شروع کنید
                </Link>
                <Link
                  to="/about"
                  className="px-8 py-4 bg-gray-700 hover:bg-gray-600 active:bg-gray-800 active:scale-95 text-white text-lg font-semibold rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                >
                  بیشتر بدانید
                </Link>
              </div>
            )}
          </div>

          {/* بخش محرک - انواع استراتژی‌های قابل بک‌تست */}
          <div className="mt-16 bg-gradient-to-r from-blue-900/50 via-purple-900/50 to-blue-900/50 rounded-2xl p-8 border border-blue-500/30">
            <div className="text-center mb-8">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                🚀 بیش از 10 نوع استراتژی معاملاتی را بک‌تست کنید!
              </h2>
              <p className="text-lg text-gray-300 max-w-3xl mx-auto">
                از استراتژی‌های مبتنی بر اندیکاتور تا استراتژی‌های متنی سفارشی - هر آنچه که فکر می‌کنید را تست کنید
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-blue-500/20 hover:border-blue-400/50 transition-all">
                <div className="text-2xl mb-3">📊</div>
                <h3 className="text-lg font-semibold text-blue-300 mb-2">اندیکاتورهای تکنیکال</h3>
                <p className="text-gray-300 text-sm">
                  RSI, MACD, SMA, EMA, Bollinger, Stochastic و 5+ اندیکاتور دیگر
                </p>
              </div>
              
              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-green-500/20 hover:border-green-400/50 transition-all">
                <div className="text-2xl mb-3">✍️</div>
                <h3 className="text-lg font-semibold text-green-300 mb-2">استراتژی‌های متنی</h3>
                <p className="text-gray-300 text-sm">
                  فایل Word/Docx خود را آپلود کنید - سیستم خودکار تجزیه می‌کند
                </p>
              </div>
              
              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-purple-500/20 hover:border-purple-400/50 transition-all">
                <div className="text-2xl mb-3">🔀</div>
                <h3 className="text-lg font-semibold text-purple-300 mb-2">استراتژی‌های ترکیبی</h3>
                <p className="text-gray-300 text-sm">
                  ترکیب چند اندیکاتور و شرایط سفارشی با منطق AND/OR
                </p>
              </div>
              
              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-yellow-500/20 hover:border-yellow-400/50 transition-all">
                <div className="text-2xl mb-3">📈</div>
                <h3 className="text-lg font-semibold text-yellow-300 mb-2">Price Action</h3>
                <p className="text-gray-300 text-sm">
                  استراتژی‌های مبتنی بر رفتار قیمت و الگوهای کندل استیک
                </p>
              </div>
              
              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-red-500/20 hover:border-red-400/50 transition-all">
                <div className="text-2xl mb-3">🛡️</div>
                <h3 className="text-lg font-semibold text-red-300 mb-2">مدیریت ریسک</h3>
                <p className="text-gray-300 text-sm">
                  Stop Loss, Take Profit و مدیریت حجم معامله
                </p>
              </div>
              
              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-teal-500/20 hover:border-teal-400/50 transition-all">
                <div className="text-2xl mb-3">🌍</div>
                <h3 className="text-lg font-semibold text-teal-300 mb-2">چند نماد</h3>
                <p className="text-gray-300 text-sm">
                  طلا، EUR/USD, GBP/USD و سایر نمادهای فارکس
                </p>
              </div>

              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-orange-500/20 hover:border-orange-400/50 transition-all">
                <div className="text-2xl mb-3">📉</div>
                <h3 className="text-lg font-semibold text-orange-300 mb-2">استراتژی‌های نوسانی</h3>
                <p className="text-gray-300 text-sm">
                  معاملات در محدوده‌های نوسانی و شناسایی نقاط ورود و خروج
                </p>
              </div>

              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-pink-500/20 hover:border-pink-400/50 transition-all">
                <div className="text-2xl mb-3">🎯</div>
                <h3 className="text-lg font-semibold text-pink-300 mb-2">استراتژی‌های روندی</h3>
                <p className="text-gray-300 text-sm">
                  شناسایی و معامله در جهت روندهای قوی بازار
                </p>
              </div>

              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-cyan-500/20 hover:border-cyan-400/50 transition-all">
                <div className="text-2xl mb-3">⚡</div>
                <h3 className="text-lg font-semibold text-cyan-300 mb-2">اسکالپینگ</h3>
                <p className="text-gray-300 text-sm">
                  معاملات سریع با سودهای کوچک و تایم فریم‌های کوتاه
                </p>
              </div>

              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-lime-500/20 hover:border-lime-400/50 transition-all">
                <div className="text-2xl mb-3">🔄</div>
                <h3 className="text-lg font-semibold text-lime-300 mb-2">استراتژی‌های معکوس</h3>
                <p className="text-gray-300 text-sm">
                  شناسایی نقاط بازگشت روند و معامله در خلاف جهت
                </p>
              </div>

              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-rose-500/20 hover:border-rose-400/50 transition-all">
                <div className="text-2xl mb-3">📊</div>
                <h3 className="text-lg font-semibold text-rose-300 mb-2">تحلیل حجم معاملات</h3>
                <p className="text-gray-300 text-sm">
                  استفاده از حجم معاملات برای تایید سیگنال‌های معاملاتی
                </p>
              </div>

              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-violet-500/20 hover:border-violet-400/50 transition-all">
                <div className="text-2xl mb-3">🎲</div>
                <h3 className="text-lg font-semibold text-violet-300 mb-2">استراتژی‌های الگوریتمی</h3>
                <p className="text-gray-300 text-sm">
                  معاملات خودکار بر اساس الگوریتم‌های پیچیده و شرط‌های چندگانه
                </p>
              </div>

              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-amber-500/20 hover:border-amber-400/50 transition-all">
                <div className="text-2xl mb-3">🌐</div>
                <h3 className="text-lg font-semibold text-amber-300 mb-2">تحلیل چند بازاری</h3>
                <p className="text-gray-300 text-sm">
                  همبستگی بین نمادهای مختلف و تحلیل همزمان چند بازار
                </p>
              </div>

              <div className="bg-gray-800/80 backdrop-blur-sm rounded-xl p-5 border border-emerald-500/20 hover:border-emerald-400/50 transition-all">
                <div className="text-2xl mb-3">⏰</div>
                <h3 className="text-lg font-semibold text-emerald-300 mb-2">استراتژی‌های زمانی</h3>
                <p className="text-gray-300 text-sm">
                  معاملات بر اساس زمان‌های خاص روز و الگوهای زمانی
                </p>
              </div>
            </div>

            <div className="mt-8 text-center">
              <p className="text-gray-300 mb-4">
                💡 <strong className="text-white">نکته:</strong> قبل از ورود به بازار واقعی، استراتژی خود را با داده‌های تاریخی تست کنید و از عملکرد آن اطمینان حاصل کنید!
              </p>
              {!isAuthenticated && (
                <Link
                  to="/login"
                  className="inline-block px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg"
                >
                  همین حالا شروع کنید و اولین بک‌تست خود را انجام دهید →
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* AI Trading Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-800/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              چرا ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی؟
            </h2>
            <p className="text-lg text-gray-300 max-w-3xl mx-auto">
              ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی، انقلابی در دنیای معاملات است. با استفاده از الگوریتم‌های پیشرفته AI، می‌توانید استراتژی‌های معاملاتی خود را بهینه کرده و تصمیمات دقیق‌تری بگیرید. سیستم ما با ترکیب هوش مصنوعی و تجزیه و تحلیل داده‌ها، امکان ترید هوشمند و خودکار را فراهم می‌کند.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 rounded-xl p-6 border border-blue-500/30">
              <h3 className="text-xl font-semibold text-blue-300 mb-3">ترید با هوش مصنوعی</h3>
              <p className="text-gray-300">
                استفاده از هوش مصنوعی برای تحلیل بازار و شناسایی فرصت‌های معاملاتی بهینه. سیستم ما با یادگیری از داده‌های تاریخی، الگوهای معاملاتی را شناسایی می‌کند.
              </p>
            </div>
            <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 rounded-xl p-6 border border-purple-500/30">
              <h3 className="text-xl font-semibold text-purple-300 mb-3">ترید به کمک هوش مصنوعی</h3>
              <p className="text-gray-300">
                هوش مصنوعی به عنوان دستیار معاملاتی شما عمل می‌کند. استراتژی‌های شما را تجزیه و تحلیل کرده و پیشنهادات بهینه برای بهبود عملکرد ارائه می‌دهد.
              </p>
            </div>
            <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 rounded-xl p-6 border border-green-500/30">
              <h3 className="text-xl font-semibold text-green-300 mb-3">معاملات هوشمند</h3>
              <p className="text-gray-300">
                ترکیب هوش مصنوعی با تجزیه و تحلیل تکنیکال برای انجام معاملات هوشمند. سیستم به صورت خودکار بهترین نقاط ورود و خروج را شناسایی می‌کند.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-white text-center mb-12">
            ویژگی‌های کلیدی ترید با هوش مصنوعی
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <button
              type="button"
              className="bg-gray-800 rounded-xl p-6 hover:bg-gray-750 transition-all duration-200 shadow-lg hover:shadow-xl text-left w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">تحلیل هوشمند با AI برای ترید</h3>
              <p className="text-gray-400 leading-relaxed">
                ترید با هوش مصنوعی: استراتژی‌های معاملاتی خود را با استفاده از هوش مصنوعی تجزیه و تحلیل کنید و به کد تبدیل کنید. سیستم به صورت خودکار بهترین استراتژی‌ها را شناسایی می‌کند.
              </p>
            </button>

            {/* Feature 2 */}
            <button
              type="button"
              className="bg-gray-800 rounded-xl p-6 hover:bg-gray-750 transition-all duration-200 shadow-lg hover:shadow-xl text-left w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">تست Backtest دقیق</h3>
              <p className="text-gray-400 leading-relaxed">
                استراتژی‌های خود را بر روی داده‌های تاریخی تست کنید و عملکرد آن‌ها را با نمودارها و آمار دقیق بررسی کنید
              </p>
            </button>

            {/* Feature 3 */}
            <button
              type="button"
              className="bg-gray-800 rounded-xl p-6 hover:bg-gray-750 transition-all duration-200 shadow-lg hover:shadow-xl text-left w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <div className="w-12 h-12 bg-teal-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">فواید بک‌تست قبل از معامله زنده</h3>
              <p className="text-gray-400 leading-relaxed">
                ابتدا استراتژی خود را بک‌تست کنید تا نقاط ضعف روشن شود، سپس با اطمینان وارد بازار واقعی شوید و ریسک ضررهای غیرمنتظره را کاهش دهید
              </p>
            </button>

            {/* Feature 4 */}
            <button
              type="button"
              aria-disabled={!liveTradingEnabled}
              className={`bg-gray-800 rounded-xl p-6 transition-all duration-200 shadow-lg text-left w-full focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                liveTradingEnabled ? 'hover:bg-gray-750 hover:shadow-xl' : 'opacity-75 cursor-not-allowed'
              }`}
            >
              <div className="w-12 h-12 bg-yellow-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">
                {liveTradingEnabled ? 'معاملات خودکار' : 'معاملات خودکار (به‌زودی)'}
              </h3>
              <p className="text-gray-400 leading-relaxed">
                {liveTradingEnabled
                  ? 'معاملات زنده را با استفاده از حساب معاملاتی Litefinex به صورت خودکار انجام دهید'
                  : 'در حال آماده‌سازی زیرساخت‌های امن برای شروع معاملات خودکار هستیم'}
              </p>
            </button>

            {/* Feature 5 */}
            <button
              type="button"
              className="bg-gray-800 rounded-xl p-6 hover:bg-gray-750 transition-all duration-200 shadow-lg hover:shadow-xl text-left w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">بهینه‌سازی استراتژی با AI</h3>
              <p className="text-gray-400 leading-relaxed">
                ترید به کمک هوش مصنوعی: با استفاده از الگوریتم‌های بهینه‌سازی ML و DL، پارامترهای استراتژی خود را بهبود دهید. هوش مصنوعی بهترین تنظیمات را برای شما پیدا می‌کند.
              </p>
            </button>

            {/* Feature 6 */}
            <button
              type="button"
              className="bg-gray-800 rounded-xl p-6 hover:bg-gray-750 transition-all duration-200 shadow-lg hover:shadow-xl text-left w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <div className="w-12 h-12 bg-indigo-600 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">مدیریت ریسک</h3>
              <p className="text-gray-400 leading-relaxed">
                با تنظیم حد ضرر و حد سود، ریسک معاملات خود را مدیریت کنید
              </p>
            </button>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-800/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-white text-center mb-12">
            چگونه کار می‌کند؟
          </h2>
          <div className="flex flex-wrap justify-center gap-6">
            <div className="text-center max-w-[200px]">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                1
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">آپلود استراتژی</h3>
              <p className="text-gray-400 text-sm">
                استراتژی معاملاتی خود را به صورت فایل آپلود کنید
              </p>
            </div>
            <div className="text-center max-w-[200px]">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                2
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">تجزیه با AI</h3>
              <p className="text-gray-400 text-sm">
                سیستم با استفاده از AI استراتژی را تجزیه می‌کند
              </p>
            </div>
            <div className="text-center max-w-[200px]">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                3
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">تست Backtest</h3>
              <p className="text-gray-400 text-sm">
                استراتژی را بر روی داده‌های تاریخی تست کنید
              </p>
            </div>
            {liveTradingEnabled && (
              <div className="text-center max-w-[200px]">
                <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                  4
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">معامله زنده</h3>
                <p className="text-gray-400 text-sm">
                  معاملات خودکار را شروع کنید
                </p>
              </div>
            )}
            <div className="text-center max-w-[200px]">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                5
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">بررسی و بهینه‌سازی</h3>
              <p className="text-gray-400 text-sm">
                نتایج را بررسی کنید و استراتژی را بهینه کنید
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-800/50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-white text-center mb-12">
            سوالات متداول درباره ترید با هوش مصنوعی
          </h2>
          <div className="space-y-4">
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-blue-400 mb-3">ترید با هوش مصنوعی چیست؟</h3>
              <p className="text-gray-300 leading-relaxed">
                ترید با هوش مصنوعی به معنای استفاده از الگوریتم‌های هوش مصنوعی و یادگیری ماشین برای تحلیل بازار و انجام معاملات است. سیستم ما با استفاده از هوش مصنوعی، الگوهای معاملاتی را شناسایی کرده و بهترین استراتژی‌ها را برای شما پیشنهاد می‌دهد.
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-blue-400 mb-3">ترید به کمک هوش مصنوعی چگونه کار می‌کند؟</h3>
              <p className="text-gray-300 leading-relaxed">
                ترید به کمک هوش مصنوعی به این صورت است که هوش مصنوعی به عنوان دستیار معاملاتی شما عمل می‌کند. استراتژی‌های شما را تجزیه و تحلیل کرده، بر روی داده‌های تاریخی تست می‌کند و پیشنهادات بهینه برای بهبود عملکرد ارائه می‌دهد.
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-blue-400 mb-3">آیا ترید با هوش مصنوعی امن است؟</h3>
              <p className="text-gray-300 leading-relaxed">
                بله، سیستم ما با استفاده از آخرین استانداردهای امنیتی طراحی شده است. تمام اطلاعات شما رمزگذاری شده و محافظت می‌شود. همچنین قبل از انجام معاملات واقعی، می‌توانید استراتژی خود را بر روی داده‌های تاریخی تست کنید.
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-blue-400 mb-3">چگونه می‌توانم شروع کنم؟</h3>
              <p className="text-gray-300 leading-relaxed">
                برای شروع، ابتدا ثبت‌نام کنید و سپس استراتژی معاملاتی خود را به صورت فایل آپلود کنید. سیستم به صورت خودکار استراتژی را با هوش مصنوعی تجزیه می‌کند و می‌توانید آن را بر روی داده‌های تاریخی تست کنید.
              </p>
            </div>
          </div>
        </div>
        <FAQSchema
          faqs={[
            {
              question: 'ترید با هوش مصنوعی چیست؟',
              answer: 'ترید با هوش مصنوعی به معنای استفاده از الگوریتم‌های هوش مصنوعی و یادگیری ماشین برای تحلیل بازار و انجام معاملات است. سیستم ما با استفاده از هوش مصنوعی، الگوهای معاملاتی را شناسایی کرده و بهترین استراتژی‌ها را برای شما پیشنهاد می‌دهد.'
            },
            {
              question: 'ترید به کمک هوش مصنوعی چگونه کار می‌کند؟',
              answer: 'ترید به کمک هوش مصنوعی به این صورت است که هوش مصنوعی به عنوان دستیار معاملاتی شما عمل می‌کند. استراتژی‌های شما را تجزیه و تحلیل کرده، بر روی داده‌های تاریخی تست می‌کند و پیشنهادات بهینه برای بهبود عملکرد ارائه می‌دهد.'
            },
            {
              question: 'آیا ترید با هوش مصنوعی امن است؟',
              answer: 'بله، سیستم ما با استفاده از آخرین استانداردهای امنیتی طراحی شده است. تمام اطلاعات شما رمزگذاری شده و محافظت می‌شود. همچنین قبل از انجام معاملات واقعی، می‌توانید استراتژی خود را بر روی داده‌های تاریخی تست کنید.'
            },
            {
              question: 'چگونه می‌توانم شروع کنم؟',
              answer: 'برای شروع، ابتدا ثبت‌نام کنید و سپس استراتژی معاملاتی خود را به صورت فایل آپلود کنید. سیستم به صورت خودکار استراتژی را با هوش مصنوعی تجزیه می‌کند و می‌توانید آن را بر روی داده‌های تاریخی تست کنید.'
            }
          ]}
        />
      </section>

      {/* CTA Section */}
      {!isAuthenticated && (
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto text-center bg-gray-800 rounded-xl p-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              آماده شروع هستید؟
            </h2>
            <p className="text-xl text-gray-300 mb-8">
              همین حالا ثبت‌نام کنید و تجربه ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی را آغاز کنید. از قدرت هوش مصنوعی در معاملات خود بهره‌مند شوید
            </p>
            <Link
              to="/login"
              className="inline-block px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white text-lg font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg"
            >
              ورود / ثبت‌نام
            </Link>
          </div>
        </section>
      )}
    </div>
    </>
  )
}

