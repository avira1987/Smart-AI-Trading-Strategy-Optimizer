import LiveTrading from '../components/LiveTrading'
import { useFeatureFlags } from '../context/FeatureFlagsContext'

export default function LiveTradingPage() {
  const { liveTradingEnabled, isLoading } = useFeatureFlags()

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-6 py-3 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
        <div className="bg-gray-800 rounded-lg p-6 text-center">
          <div className="inline-block animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-gray-300">در حال بارگذاری تنظیمات سیستم...</p>
        </div>
      </div>
    )
  }

  if (!liveTradingEnabled) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
        <div className="bg-gray-800 border border-gray-700 rounded-2xl p-8 text-center shadow-xl">
          <h1 className="text-2xl font-bold text-white mb-4">بخش معاملات زنده موقتاً غیرفعال است</h1>
          <p className="text-gray-300 leading-relaxed">
            این بخش به منظور بهبود تجربه کاربران و بررسی‌های فنی تا اطلاع ثانوی در دسترس نیست. به زودی دوباره فعال خواهد شد.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-6 py-3 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="mb-3">
        <h1 className="text-xl font-bold text-white">معاملات زنده Litefinex</h1>
        <p className="mt-1 text-sm text-gray-400">مدیریت و اجرای معاملات بر اساس استراتژی‌های شما از طریق صرافی Litefinex</p>
      </div>
      <LiveTrading />
    </div>
  )
}

