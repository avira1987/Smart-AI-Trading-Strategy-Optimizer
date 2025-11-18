import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useFeatureFlags } from '../context/FeatureFlagsContext'

export default function Landing() {
  const { isAuthenticated } = useAuth()
  const { liveTradingEnabled } = useFeatureFlags()

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
              سامانه مدیریت هوشمند معاملات فارکس
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
              با استفاده از هوش مصنوعی، استراتژی‌های معاملاتی خود را بهینه کنید و معاملات خودکار انجام دهید
            </p>
            {!isAuthenticated && (
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Link
                  to="/login"
                  className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white text-lg font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl"
                >
                  شروع کنید
                </Link>
                <Link
                  to="/about"
                  className="px-8 py-4 bg-gray-700 hover:bg-gray-600 text-white text-lg font-semibold rounded-lg transition-all duration-200"
                >
                  بیشتر بدانید
                </Link>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-white text-center mb-12">
            ویژگی‌های کلیدی
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
              <h3 className="text-xl font-semibold text-white mb-3">تحلیل هوشمند با AI</h3>
              <p className="text-gray-400 leading-relaxed">
                استراتژی‌های معاملاتی خود را با استفاده از هوش مصنوعی Gemini تجزیه و تحلیل کنید و به کد تبدیل کنید
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
              <h3 className="text-xl font-semibold text-white mb-3">بهینه‌سازی استراتژی</h3>
              <p className="text-gray-400 leading-relaxed">
                با استفاده از الگوریتم‌های بهینه‌سازی ML و DL، پارامترهای استراتژی خود را بهبود دهید
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
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                1
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">آپلود استراتژی</h3>
              <p className="text-gray-400 text-sm">
                استراتژی معاملاتی خود را به صورت فایل آپلود کنید
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                2
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">تجزیه با AI</h3>
              <p className="text-gray-400 text-sm">
                سیستم با استفاده از AI استراتژی را تجزیه می‌کند
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                3
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">تست Backtest</h3>
              <p className="text-gray-400 text-sm">
                استراتژی را بر روی داده‌های تاریخی تست کنید
              </p>
            </div>
            {liveTradingEnabled && (
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-white">
                  4
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">معامله زنده</h3>
                <p className="text-gray-400 text-sm">
                  معاملات خودکار را شروع کنید
                </p>
              </div>
            )}
            <div className="text-center">
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

      {/* CTA Section */}
      {!isAuthenticated && (
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto text-center bg-gray-800 rounded-xl p-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              آماده شروع هستید؟
            </h2>
            <p className="text-xl text-gray-300 mb-8">
              همین حالا ثبت‌نام کنید و از قدرت هوش مصنوعی در معاملات خود بهره‌مند شوید
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

      {/* Footer */}
      <footer className="py-8 px-4 sm:px-6 lg:px-8 border-t border-gray-700">
        <div className="max-w-7xl mx-auto text-center text-gray-400">
          <p>© 2024 سامانه مدیریت هوشمند معاملات فارکس. تمامی حقوق محفوظ است.</p>
        </div>
      </footer>
    </div>
  )
}

