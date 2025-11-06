import { useState, useEffect } from 'react'
import { getMT5Candles } from '../api/client'
import { useSymbol } from '../context/SymbolContext'

type Candle = {
  datetime: string
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

export default function MT5Candles() {
  const { selectedSymbol } = useSymbol()
  const [symbol, setSymbol] = useState(selectedSymbol)
  
  // Sync with global symbol selection
  useEffect(() => {
    setSymbol(selectedSymbol)
  }, [selectedSymbol])
  const [count, setCount] = useState(500)
  const [loading, setLoading] = useState(false)
  const [candles, setCandles] = useState<Candle[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleFetch = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await getMT5Candles(symbol.trim(), count)
      if (res.data?.status === 'success' && Array.isArray(res.data.candles)) {
        setCandles(res.data.candles)
      } else {
        setError(res.data?.message || 'Failed to load candles')
        setCandles([])
      }
    } catch (err: any) {
      setError(err?.response?.data?.message || String(err))
      setCandles([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 mb-6 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">کندل‌های دقیقه‌ای Litefinex</h2>
      </div>

      <form onSubmit={handleFetch} className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">نماد</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="input-compact"
            placeholder="XAUUSD_l (طلا)"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">تعداد</label>
          <input
            type="number"
            value={count}
            min={1}
            max={2000}
            onChange={(e) => setCount(parseInt(e.target.value || '0', 10))}
            className="input-compact"
          />
        </div>
        <div className="flex items-end">
          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded transition"
          >
            {loading ? 'در حال بارگذاری ...' : 'دریافت داده'}
          </button>
        </div>
      </form>

      {error && (
        <div className="bg-red-700 text-white px-3 py-2 rounded mb-4">{error}</div>
      )}

      {candles.length === 0 ? (
        <div className="text-gray-400 text-sm">اطلاعات کندل هنوز دریافت نشده است.</div>
      ) : (
        <div className="overflow-auto max-h-96 border border-gray-700 rounded">
          <table className="min-w-full text-sm text-gray-200">
            <thead className="bg-gray-700 sticky top-0">
              <tr>
                <th className="text-right px-3 py-2">تاریخ/ساعت</th>
                <th className="text-right px-3 py-2">شروع</th>
                <th className="text-right px-3 py-2">بیشترین</th>
                <th className="text-right px-3 py-2">کمترین</th>
                <th className="text-right px-3 py-2">پایان</th>
                <th className="text-right px-3 py-2">حجم</th>
              </tr>
            </thead>
            <tbody>
              {candles.map((c, idx) => (
                <tr key={idx} className={idx % 2 ? 'bg-gray-800' : 'bg-gray-900'}>
                  <td className="px-3 py-2 whitespace-nowrap">{new Date(c.datetime).toLocaleString()}</td>
                  <td className="px-3 py-2 text-right">{c.open.toFixed(5)}</td>
                  <td className="px-3 py-2 text-right">{c.high.toFixed(5)}</td>
                  <td className="px-3 py-2 text-right">{c.low.toFixed(5)}</td>
                  <td className="px-3 py-2 text-right">{c.close.toFixed(5)}</td>
                  <td className="px-3 py-2 text-right">{(c.volume ?? 0).toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}


