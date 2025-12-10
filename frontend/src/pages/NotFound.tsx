import { Link } from 'react-router-dom'
import SEO from '../components/SEO'
import Breadcrumbs from '../components/Breadcrumbs'

export default function NotFound() {
  return (
    <>
      <SEO
        title="صفحه پیدا نشد | 404 | ترید با هوش مصنوعی"
        description="صفحه مورد نظر یافت نشد. بازگشت به صفحه اصلی سامانه ترید با هوش مصنوعی و ترید به کمک هوش مصنوعی"
        keywords="404, صفحه پیدا نشد, ترید با هوش مصنوعی"
        canonical="https://myaibaz.ir/404"
      />
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center px-4 py-8 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
        <div className="max-w-2xl mx-auto text-center">
          <Breadcrumbs items={[{ label: 'خانه', path: '/' }, { label: 'صفحه پیدا نشد', path: '/404' }]} />
          
          <div className="bg-gray-800 rounded-xl shadow-2xl p-8 md:p-12">
            <div className="mb-6">
              <h1 className="text-9xl font-bold text-blue-500 mb-4">404</h1>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                صفحه مورد نظر یافت نشد
              </h2>
              <p className="text-lg text-gray-300 mb-8">
                متأسفانه صفحه‌ای که به دنبال آن هستید وجود ندارد یا به آدرس دیگری منتقل شده است.
              </p>
            </div>

            <div className="space-y-4 mb-8">
              <p className="text-gray-400">
                ممکن است به دنبال یکی از صفحات زیر باشید:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-right">
                <Link
                  to="/"
                  className="bg-gray-700 hover:bg-gray-600 rounded-lg p-4 transition-colors block"
                >
                  <div className="text-blue-400 font-semibold mb-1">صفحه اصلی</div>
                  <div className="text-sm text-gray-300">ترید با هوش مصنوعی</div>
                </Link>
                <Link
                  to="/about"
                  className="bg-gray-700 hover:bg-gray-600 rounded-lg p-4 transition-colors block"
                >
                  <div className="text-blue-400 font-semibold mb-1">درباره ما</div>
                  <div className="text-sm text-gray-300">درباره سامانه ترید با هوش مصنوعی</div>
                </Link>
                <Link
                  to="/tutorial"
                  className="bg-gray-700 hover:bg-gray-600 rounded-lg p-4 transition-colors block"
                >
                  <div className="text-blue-400 font-semibold mb-1">آموزش</div>
                  <div className="text-sm text-gray-300">راهنمای ترید به کمک هوش مصنوعی</div>
                </Link>
                <Link
                  to="/login"
                  className="bg-gray-700 hover:bg-gray-600 rounded-lg p-4 transition-colors block"
                >
                  <div className="text-blue-400 font-semibold mb-1">ورود</div>
                  <div className="text-sm text-gray-300">ورود به سامانه معاملات هوشمند</div>
                </Link>
              </div>
            </div>

            <div className="pt-6 border-t border-gray-700">
              <Link
                to="/"
                className="inline-block px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg"
              >
                بازگشت به صفحه اصلی
              </Link>
            </div>

            <div className="mt-8 text-sm text-gray-500">
              <p>
                اگر فکر می‌کنید این یک خطا است، لطفاً با پشتیبانی تماس بگیرید.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

