import { useState, useEffect, useCallback } from 'react'
import { getStrategies, getLiveTrades, getAccountInfo, getMarketStatus, openTrade, closeTrade, syncPositions, getMT5Positions, TradingStrategy, LiveTrade, AccountInfo } from '../api/client'
import { useToast } from './ToastProvider'
import { useSymbol } from '../context/SymbolContext'
import AutoTradingSettings from './AutoTradingSettings'
import { useRateLimit } from '../hooks/useRateLimit'

export default function LiveTrading() {
  const [strategies, setStrategies] = useState<TradingStrategy[]>([])
  const [trades, setTrades] = useState<LiveTrade[]>([])
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null)
  const [marketOpen, setMarketOpen] = useState<boolean>(false)
  const [marketMessage, setMarketMessage] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const { showToast } = useToast()
  const rateLimitClickOpenTrade = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'liveTrading-openTrade' })
  const rateLimitClickCloseTrade = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'liveTrading-closeTrade' })
  const rateLimitClickSync = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'liveTrading-sync' })

  // Form state
  const [selectedStrategy, setSelectedStrategy] = useState<number | ''>('')
  const { selectedSymbol } = useSymbol()
  const [symbol, setSymbol] = useState('XAUUSD')
  const [tradeType, setTradeType] = useState<'buy' | 'sell'>('buy')
  const [volume, setVolume] = useState('0.01')
  const [stopLoss, setStopLoss] = useState('')
  const [takeProfit, setTakeProfit] = useState('')

  useEffect(() => {
    loadData()
    const interval = setInterval(() => {
      refreshData()
    }, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Keep form symbol aligned with global selection if user hasn't changed it manually
    setSymbol(selectedSymbol)
  }, [selectedSymbol])

  const loadData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        loadStrategies(),
        loadTrades(false), // show errors on initial load
        loadAccountInfo(),
        loadMarketStatus(),
      ])
    } catch (error: any) {
      showToast('خطا در بارگذاری داده‌ها: ' + (error.message || error), { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const refreshData = async () => {
    setRefreshing(true)
    try {
      await Promise.all([
        loadTrades(true), // silent mode - don't show errors during refresh
        loadAccountInfo(),
        loadMarketStatus(),
      ])
    } catch (error) {
      // Silent refresh errors
    } finally {
      setRefreshing(false)
    }
  }

  const loadStrategies = async () => {
    try {
      const response = await getStrategies()
      console.log('🔍 Strategies API response:', response)
      console.log('🔍 Response data type:', typeof response.data)
      console.log('🔍 Response data:', response.data)
      console.log('🔍 Is array?:', Array.isArray(response.data))
      
      // Handle pagination format from Django REST Framework
      let strategiesData: TradingStrategy[] = []
      
      // Check all possible response formats
      if (response.data) {
        if (Array.isArray(response.data)) {
          // Direct array
          strategiesData = response.data
          console.log('✅ Found direct array format')
        } else if (response.data.results && Array.isArray(response.data.results)) {
          // Paginated format
          strategiesData = response.data.results
          console.log('✅ Found paginated format (results)')
        } else if (Array.isArray(response.data.data)) {
          // Nested data format
          strategiesData = response.data.data
          console.log('✅ Found nested data format')
        } else {
          console.warn('⚠️ Unknown response format:', response.data)
        }
      } else {
        console.warn('⚠️ No data in response')
      }
      
      console.log('📊 Parsed strategies data:', strategiesData)
      console.log('📊 Number of strategies:', strategiesData.length)
      if (strategiesData.length > 0) {
        console.log('📊 First strategy:', strategiesData[0])
      }
      
      // نمایش همه استراتژی‌ها (فعال و غیرفعال) برای امکان انتخاب
      setStrategies(strategiesData)
      if (strategiesData.length > 0 && !selectedStrategy) {
        // ترجیحاً استراتژی فعال را انتخاب کن، در غیر این صورت اولین را
        const activeStrategy = strategiesData.find((s: TradingStrategy) => s.is_active)
        setSelectedStrategy(activeStrategy ? activeStrategy.id : strategiesData[0].id)
      }
    } catch (error: any) {
      console.error('❌ Error loading strategies:', error)
      console.error('❌ Error response:', error.response)
      console.error('❌ Error message:', error.message)
      showToast('خطا در بارگذاری استراتژی‌ها: ' + (error.response?.data?.detail || error.message || 'خطای ناشناخته'), { type: 'error' })
    }
  }

  const loadTrades = async (silent: boolean = false) => {
    try {
      const response = await getLiveTrades()
      // Handle pagination format from Django REST Framework
      let tradesData: LiveTrade[] = []
      if (response.data && Array.isArray(response.data)) {
        tradesData = response.data
      } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
        tradesData = response.data.results
      } else if (response.data && Array.isArray(response.data.data)) {
        tradesData = response.data.data
      }
      
      setTrades(tradesData)
    } catch (error: any) {
      console.error('Error loading trades:', error)
      
      // فقط در حالت non-silent پیام نمایش بده
      if (!silent) {
        // بررسی کن که آیا واقعاً خطا است یا فقط دیتابیس خالی است
        if (error.response?.status === 404 || (error.response?.status === 200 && !error.response?.data)) {
          // احتمالاً فقط خالی است، خطا نیست
          setTrades([])
          return
        }
        showToast('خطا در بارگذاری معاملات', { type: 'error' })
      }
      // در حالت silent هم آرایه خالی set کن تا UI خراب نشود
      setTrades([])
    }
  }

  const loadAccountInfo = async () => {
    try {
      const response = await getAccountInfo()
      if (response.data.status === 'success') {
        setAccountInfo(response.data.account)
        // Auto-set symbol based on account type if not manually set
        if (response.data.recommended_symbol && symbol === 'XAUUSD') {
          setSymbol(response.data.recommended_symbol)
        }
      }
    } catch (error: any) {
      // Account info may not be available
    }
  }

  const loadMarketStatus = async () => {
    try {
      const response = await getMarketStatus()
      if (response.data.status === 'success') {
        setMarketOpen(response.data.market_open)
        setMarketMessage(response.data.message)
      }
    } catch (error: any) {
      setMarketOpen(false)
      setMarketMessage('وضعیت بازار نامشخص است')
    }
  }

  const handleOpenTrade = useCallback(
    rateLimitClickOpenTrade(async () => {
      if (!selectedStrategy) {
        showToast('لطفاً یک استراتژی انتخاب کنید', { type: 'warning' })
        return
      }

      if (!marketOpen) {
        showToast(`بازار بسته است: ${marketMessage}`, { type: 'warning' })
        return
      }

      try {
        setLoading(true)
        const response = await openTrade({
          strategy_id: Number(selectedStrategy),
          symbol,
          trade_type: tradeType,
          volume: parseFloat(volume),
          stop_loss: stopLoss ? parseFloat(stopLoss) : undefined,
          take_profit: takeProfit ? parseFloat(takeProfit) : undefined,
        })

        if (response.data.status === 'success') {
          showToast('معامله با موفقیت باز شد!', { type: 'success' })
          await loadTrades(true) // silent mode after action
          await loadAccountInfo()
          // Reset form
          setStopLoss('')
          setTakeProfit('')
        } else {
          showToast(response.data.message || 'خطا در باز کردن معامله', { type: 'error' })
        }
      } catch (error: any) {
        const message = error.response?.data?.message || error.message || 'خطا در باز کردن معامله'
        showToast(message, { type: 'error' })
      } finally {
        setLoading(false)
      }
    }),
    [selectedStrategy, marketOpen, marketMessage, symbol, tradeType, volume, stopLoss, takeProfit, rateLimitClickOpenTrade, showToast, setLoading, loadTrades, loadAccountInfo, setStopLoss, setTakeProfit]
  )

  const handleCloseTrade = (tradeId: number) => {
    if (!confirm('آیا مطمئن هستید که می‌خواهید این معامله را ببندید؟')) {
      return
    }

    const closeTradeAction = rateLimitClickCloseTrade(async () => {
      try {
        setLoading(true)
        const response = await closeTrade(tradeId)

        if (response.data.status === 'success') {
          showToast('معامله با موفقیت بسته شد!', { type: 'success' })
          await loadTrades(true) // silent mode after action
          await loadAccountInfo()
        } else {
          showToast(response.data.message || 'خطا در بستن معامله', { type: 'error' })
        }
      } catch (error: any) {
        const message = error.response?.data?.message || error.message || 'خطا در بستن معامله'
        showToast(message, { type: 'error' })
      } finally {
        setLoading(false)
      }
    })
    
    closeTradeAction()
  }

  const handleSyncPositions = rateLimitClickSync(async () => {
    try {
      setLoading(true)
      const response = await syncPositions()
      if (response.data.status === 'success') {
        showToast(
          `همگام‌سازی انجام شد: ${response.data.synced} جدید، ${response.data.updated} به‌روز، ${response.data.closed} بسته شده`,
          { type: 'success' }
        )
        await loadTrades(true) // silent mode after action
      }
    } catch (error: any) {
      const message = error.response?.data?.message || error.message || 'خطا در همگام‌سازی'
      showToast(message, { type: 'error' })
    } finally {
      setLoading(false)
    }
  })

  const openTrades = trades.filter(t => t.status === 'open')
  const closedTrades = trades.filter(t => t.status === 'closed')

  return (
    <div className="space-y-3">
      {/* Auto Trading Settings */}
      <AutoTradingSettings />

      {/* Account Info */}
      {accountInfo && (
        <div className="bg-gray-800 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-white">اطلاعات حساب Litefinex</h2>
            {accountInfo.is_demo !== undefined && (
              <span className={`px-3 py-1 rounded text-sm font-semibold ${
                accountInfo.is_demo 
                  ? 'bg-yellow-600 text-white' 
                  : 'bg-green-600 text-white'
              }`}>
                {accountInfo.is_demo ? 'حساب دمو' : 'حساب واقعی'}
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <div>
              <div className="text-gray-400 text-xs">موجودی</div>
              <div className="text-white text-base font-semibold">{accountInfo.balance.toFixed(2)} {accountInfo.currency}</div>
            </div>
            <div>
              <div className="text-gray-400 text-xs">سرمایه</div>
              <div className="text-white text-base font-semibold">{accountInfo.equity.toFixed(2)} {accountInfo.currency}</div>
            </div>
            <div>
              <div className="text-gray-400 text-xs">حاشیه آزاد</div>
              <div className="text-white text-base font-semibold">{accountInfo.free_margin.toFixed(2)} {accountInfo.currency}</div>
            </div>
            <div>
              <div className="text-gray-400 text-xs">سطح حاشیه</div>
              <div className="text-white text-base font-semibold">{accountInfo.margin_level ? accountInfo.margin_level.toFixed(2) + '%' : 'N/A'}</div>
            </div>
          </div>
        </div>
      )}

      {/* Market Status */}
      <div className={`rounded-lg p-2 ${marketOpen ? 'bg-green-900 bg-opacity-30 border border-green-700' : 'bg-red-900 bg-opacity-30 border border-red-700'}`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-white text-sm font-semibold">
              وضعیت بازار: {marketOpen ? 'باز' : 'بسته'}
            </div>
            <div className="text-gray-300 text-xs">{marketMessage}</div>
          </div>
          <button
            onClick={handleSyncPositions}
            disabled={loading}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
          >
            {loading ? '...' : 'همگام‌سازی'}
          </button>
        </div>
      </div>

      {/* Open Trade Form */}
      <div className="bg-gray-800 rounded-lg p-3">
        <h2 className="text-lg font-semibold text-white mb-2">باز کردن معامله جدید</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-2">استراتژی</label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value ? Number(e.target.value) : '')}
              className="select-compact"
            >
              <option value="">انتخاب استراتژی...</option>
              {strategies.length === 0 ? (
                <option value="" disabled>
                  هیچ استراتژی یافت نشد
                </option>
              ) : (
                strategies.map((strategy) => (
                  <option key={strategy.id} value={strategy.id}>
                    {strategy.name} {!strategy.is_active ? '(غیرفعال)' : ''}
                  </option>
                ))
              )}
            </select>
            {strategies.length === 0 && (
              <p className="text-xs text-yellow-400 mt-1">
                ⚠️ هیچ استراتژی آپلود نشده است. لطفاً ابتدا استراتژی را در بخش داشبورد آپلود کنید.
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-2">نماد</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="input-compact"
              placeholder="XAUUSD"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-2">نوع معامله</label>
            <select
              value={tradeType}
              onChange={(e) => setTradeType(e.target.value as 'buy' | 'sell')}
              className="select-compact"
            >
              <option value="buy">خرید (Buy)</option>
              <option value="sell">فروش (Sell)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-2">حجم (لات)</label>
            <input
              type="number"
              value={volume}
              onChange={(e) => setVolume(e.target.value)}
              step="0.01"
              min="0.01"
              className="input-compact"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-2">حد ضرر - اختیاری</label>
            <input
              type="number"
              value={stopLoss}
              onChange={(e) => setStopLoss(e.target.value)}
              step="0.01"
              className="input-compact"
              placeholder="خالی"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-2">حد سود - اختیاری</label>
            <input
              type="number"
              value={takeProfit}
              onChange={(e) => setTakeProfit(e.target.value)}
              step="0.01"
              className="input-compact"
              placeholder="خالی"
            />
          </div>
        </div>

        <button
          onClick={handleOpenTrade}
          disabled={loading || !marketOpen || !selectedStrategy}
          className="mt-2 w-full md:w-auto btn-success"
        >
          {loading ? 'در حال باز کردن...' : 'باز کردن معامله'}
        </button>
      </div>

      {/* Open Trades */}
      <div className="bg-gray-800 rounded-lg p-3">
        <h2 className="text-lg font-semibold text-white mb-2">
          معاملات باز ({openTrades.length})
        </h2>
        {openTrades.length === 0 ? (
          <p className="text-gray-400 text-sm">معامله باز وجود ندارد</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-right text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="px-2 py-1 text-gray-300 text-xs">تیکت</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">نماد</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">نوع</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">حجم</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">قیمت باز</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">قیمت فعلی</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">سود/زیان</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {openTrades.map((trade) => (
                  <tr key={trade.id} className="border-b border-gray-700">
                    <td className="px-2 py-1 text-white">{trade.mt5_ticket}</td>
                    <td className="px-2 py-1 text-white">{trade.symbol}</td>
                    <td className={`px-2 py-1 ${trade.trade_type === 'buy' ? 'text-green-400' : 'text-red-400'}`}>
                      {trade.trade_type === 'buy' ? 'خرید' : 'فروش'}
                    </td>
                    <td className="px-2 py-1 text-white">{trade.volume}</td>
                    <td className="px-2 py-1 text-white">{trade.open_price.toFixed(5)}</td>
                    <td className="px-2 py-1 text-white">{trade.current_price?.toFixed(5) || 'N/A'}</td>
                    <td className={`px-2 py-1 font-semibold ${trade.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {trade.profit.toFixed(2)}
                    </td>
                    <td className="px-2 py-1">
                      <button
                        onClick={() => handleCloseTrade(trade.id)}
                        disabled={loading}
                        className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs transition disabled:opacity-50"
                      >
                        بستن
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Closed Trades */}
      {closedTrades.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-3">
          <h2 className="text-lg font-semibold text-white mb-2">
            معاملات بسته شده ({closedTrades.length})
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-right text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="px-2 py-1 text-gray-300 text-xs">تیکت</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">نماد</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">نوع</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">حجم</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">قیمت باز</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">قیمت بسته</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">سود/زیان</th>
                  <th className="px-2 py-1 text-gray-300 text-xs">زمان بسته</th>
                </tr>
              </thead>
              <tbody>
                {closedTrades.slice(0, 10).map((trade) => (
                  <tr key={trade.id} className="border-b border-gray-700">
                    <td className="px-2 py-1 text-white">{trade.mt5_ticket}</td>
                    <td className="px-2 py-1 text-white">{trade.symbol}</td>
                    <td className={`px-2 py-1 ${trade.trade_type === 'buy' ? 'text-green-400' : 'text-red-400'}`}>
                      {trade.trade_type === 'buy' ? 'خرید' : 'فروش'}
                    </td>
                    <td className="px-2 py-1 text-white">{trade.volume}</td>
                    <td className="px-2 py-1 text-white">{trade.open_price.toFixed(5)}</td>
                    <td className="px-2 py-1 text-white">{trade.close_price?.toFixed(5) || 'N/A'}</td>
                    <td className={`px-2 py-1 font-semibold ${trade.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {trade.profit.toFixed(2)}
                    </td>
                    <td className="px-2 py-1 text-gray-400 text-xs">
                      {trade.closed_at ? new Date(trade.closed_at).toLocaleString('fa-IR') : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

