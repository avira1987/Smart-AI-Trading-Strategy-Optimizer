import LiveTrading from '../components/LiveTrading'

export default function LiveTradingPage() {
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

