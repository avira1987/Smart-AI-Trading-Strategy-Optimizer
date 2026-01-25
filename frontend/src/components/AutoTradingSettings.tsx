import { useState, useEffect } from 'react'
import { 
  getStrategies, 
  getAutoTradingSettings, 
  createOrUpdateAutoTradingSettings,
  toggleAutoTrading,
  testAutoTradeSignal,
  getAccountInfo,
  TradingStrategy,
  AutoTradingSettings as AutoTradingSettingsType
} from '../api/client'
import { useToast } from './ToastProvider'
import { useSymbol } from '../context/SymbolContext'

export default function AutoTradingSettings() {
  const [strategies, setStrategies] = useState<TradingStrategy[]>([])
  const [settings, setSettings] = useState<AutoTradingSettingsType[]>([])
  const [selectedStrategy, setSelectedStrategy] = useState<number | ''>('')
  const [loading, setLoading] = useState(false)
  const [testingSignal, setTestingSignal] = useState<number | null>(null)
  const { showToast } = useToast()
  const { selectedSymbol } = useSymbol()

  // Form state for new/edit settings
  const [formData, setFormData] = useState({
    symbol: 'XAUUSD',
    timeframe: 'M15',
    volume: 0.01,
    max_open_trades: 3,
    check_interval_minutes: 5,
    use_stop_loss: true,
    use_take_profit: true,
    stop_loss_pips: 50,
    take_profit_pips: 100,
    risk_per_trade_percent: 2.0,
    is_enabled: false,
  })

  useEffect(() => {
    loadData()
    loadRecommendedSymbol()
  }, [])

  useEffect(() => {
    // Sync form symbol with global selection when user hasn't customized it
    setFormData(prev => ({ ...prev, symbol: selectedSymbol }))
  }, [selectedSymbol])

  const loadRecommendedSymbol = async () => {
    try {
      const response = await getAccountInfo()
      if (response.data.status === 'success') {
        // Account info loaded successfully
        // Note: recommended_symbol is not part of the API response type
      }
    } catch (error) {
      // Account info may not be available
    }
  }

  const loadData = async () => {
    try {
      setLoading(true)
      await Promise.all([loadStrategies(), loadSettings()])
    } catch (error: any) {
      showToast('خطا در بارگذاری داده‌ها: ' + (error.message || error), { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const loadStrategies = async () => {
    try {
      const response = await getStrategies()
      console.log('🔍 AutoTradingSettings - Strategies API response:', response)
      console.log('🔍 Response data:', response.data)
      
      // Handle pagination format from Django REST Framework
      let strategiesData: TradingStrategy[] = []
      if (Array.isArray(response.data)) {
        strategiesData = response.data
        console.log('✅ Found direct array format')
      } else if (response.data && 'results' in response.data && Array.isArray((response.data as any).results)) {
        strategiesData = (response.data as any).results
        console.log('✅ Found paginated format (results)')
      } else if (response.data && 'data' in response.data && Array.isArray((response.data as any).data)) {
        strategiesData = (response.data as any).data
        console.log('✅ Found nested data format')
      }
      
      console.log('📊 All strategies:', strategiesData.length)
      console.log('📊 Strategies data:', strategiesData)
      
      // نمایش همه استراتژی‌ها (فعال، غیرفعال، پردازش شده و پردازش نشده)
      // کاربر می‌تواند هر استراتژی را انتخاب کند
      setStrategies(strategiesData)
      
      if (strategiesData.length > 0 && !selectedStrategy) {
        // ترجیحاً استراتژی پردازش شده و فعال را انتخاب کن
        const preferredStrategy = strategiesData.find(
          (s: TradingStrategy) => s.processing_status === 'processed' && s.is_active
        ) || strategiesData.find(
          (s: TradingStrategy) => s.is_active
        ) || strategiesData[0]
        
        setSelectedStrategy(preferredStrategy.id)
        loadSettingsForStrategy(preferredStrategy.id)
      }
    } catch (error: any) {
      console.error('❌ Error loading strategies:', error)
      console.error('❌ Error response:', error.response)
      showToast('خطا در بارگذاری استراتژی‌ها: ' + (error.response?.data?.detail || error.message || 'خطای ناشناخته'), { type: 'error' })
    }
  }

  const loadSettings = async () => {
    try {
      const response = await getAutoTradingSettings()
      // Handle pagination format from Django REST Framework
      let settingsData: AutoTradingSettingsType[] = []
      if (Array.isArray(response.data)) {
        settingsData = response.data
      } else if (response.data && 'results' in response.data && Array.isArray((response.data as any).results)) {
        settingsData = (response.data as any).results
      } else if (response.data && 'data' in response.data && Array.isArray((response.data as any).data)) {
        settingsData = (response.data as any).data
      }
      
      setSettings(settingsData)
    } catch (error: any) {
      console.error('Error loading settings:', error)
      showToast('خطا در بارگذاری تنظیمات', { type: 'error' })
    }
  }

  const loadSettingsForStrategy = async (strategyId: number) => {
    try {
      const response = await getAutoTradingSettings(strategyId)
      // Handle pagination format from Django REST Framework
      let settingsData: AutoTradingSettingsType[] = []
      if (Array.isArray(response.data)) {
        settingsData = response.data
      } else if (response.data && 'results' in response.data && Array.isArray((response.data as any).results)) {
        settingsData = (response.data as any).results
      } else if (response.data && 'data' in response.data && Array.isArray((response.data as any).data)) {
        settingsData = (response.data as any).data
      }
      
      if (settingsData.length > 0) {
        const setting = settingsData[0]
        setFormData({
          symbol: setting.symbol,
          timeframe: setting.timeframe || 'M15',
          volume: setting.volume,
          max_open_trades: setting.max_open_trades,
          check_interval_minutes: setting.check_interval_minutes,
          use_stop_loss: setting.use_stop_loss,
          use_take_profit: setting.use_take_profit,
          stop_loss_pips: setting.stop_loss_pips,
          take_profit_pips: setting.take_profit_pips,
          risk_per_trade_percent: setting.risk_per_trade_percent,
          is_enabled: setting.is_enabled,
        })
      } else {
        // Reset to defaults
        setFormData({
          symbol: selectedSymbol || 'XAUUSD',
          timeframe: 'M15',
          volume: 0.01,
          max_open_trades: 3,
          check_interval_minutes: 5,
          use_stop_loss: true,
          use_take_profit: true,
          stop_loss_pips: 50,
          take_profit_pips: 100,
          risk_per_trade_percent: 2.0,
          is_enabled: false,
        })
      }
    } catch (error) {
      // Strategy might not have settings yet
    }
  }

  useEffect(() => {
    if (selectedStrategy) {
      loadSettingsForStrategy(Number(selectedStrategy))
    }
  }, [selectedStrategy])

  const handleSave = async () => {
    if (!selectedStrategy) {
      showToast('لطفاً یک استراتژی انتخاب کنید', { type: 'warning' })
      return
    }

    try {
      setLoading(true)
      const response = await createOrUpdateAutoTradingSettings({
        strategy_id: Number(selectedStrategy),
        ...formData,
      })

      if (response.data.status === 'success') {
        showToast('تنظیمات با موفقیت ذخیره شد!', { type: 'success' })
        await loadSettings()
      } else {
        showToast(response.data.message || 'خطا در ذخیره تنظیمات', { type: 'error' })
      }
    } catch (error: any) {
      const message = error.response?.data?.message || error.message || 'خطا در ذخیره تنظیمات'
      showToast(message, { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = async (settingId: number) => {
    try {
      setLoading(true)
      const response = await toggleAutoTrading(settingId)
      if (response.data.status === 'success') {
        showToast(response.data.message, { type: 'success' })
        await loadSettings()
        if (selectedStrategy) {
          await loadSettingsForStrategy(Number(selectedStrategy))
        }
      }
    } catch (error: any) {
      const message = error.response?.data?.message || error.message || 'خطا'
      showToast(message, { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleTestSignal = async () => {
    if (!selectedStrategy) {
      showToast('لطفاً یک استراتژی انتخاب کنید', { type: 'warning' })
      return
    }

    try {
      setTestingSignal(Number(selectedStrategy))
      const response = await testAutoTradeSignal(Number(selectedStrategy), formData.symbol, formData.timeframe)
      
      if (response.data.status === 'success') {
        const signal = response.data.signal
        const signalText = {
          'buy': 'خرید',
          'sell': 'فروش',
          'hold': 'نگاه داشتن'
        }[signal.signal] || signal.signal
        
        showToast(
          `سیگنال: ${signalText} | اعتماد: ${(signal.confidence * 100).toFixed(1)}% | دلیل: ${signal.reason}`,
          { type: signal.signal !== 'hold' ? 'success' : 'info' }
        )
      }
    } catch (error: any) {
      const message = error.response?.data?.message || error.message || 'خطا در تست سیگنال'
      showToast(message, { type: 'error' })
    } finally {
      setTestingSignal(null)
    }
  }

  const handleAddToMonitoring = async () => {
    if (!selectedStrategy) {
      showToast('ابتدا یک استراتژی انتخاب کنید', { type: 'warning' })
      return
    }
    try {
      setLoading(true)
      const payload = {
        strategy_id: Number(selectedStrategy),
        is_enabled: true,
        symbol: formData.symbol,
        volume: formData.volume,
        max_open_trades: formData.max_open_trades,
        check_interval_minutes: formData.check_interval_minutes,
        use_stop_loss: formData.use_stop_loss,
        use_take_profit: formData.use_take_profit,
        stop_loss_pips: formData.stop_loss_pips,
        take_profit_pips: formData.take_profit_pips,
        risk_per_trade_percent: formData.risk_per_trade_percent,
      }
      const resp = await createOrUpdateAutoTradingSettings(payload)
      if (resp.data.status === 'success') {
        showToast('استراتژی به فهرست پایش اضافه شد', { type: 'success' })
        await loadSettings()
        await loadSettingsForStrategy(Number(selectedStrategy))
      } else {
        showToast(resp.data.message || 'خطا در افزودن به پایش', { type: 'error' })
      }
    } catch (e: any) {
      showToast(e?.message || 'خطا در افزودن به پایش', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const monitored = settings.filter(s => s.is_enabled)

  const currentSetting = settings.find(s => s.strategy === Number(selectedStrategy))

  return (
    <div className="bg-gray-800 rounded-lg p-3 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">تنظیمات معامله خودکار</h2>
        {currentSetting && (
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded text-sm font-semibold ${
              currentSetting.is_enabled 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-600 text-gray-200'
            }`}>
              {currentSetting.is_enabled ? 'فعال' : 'غیرفعال'}
            </span>
            <button
              onClick={() => handleToggle(currentSetting.id!)}
              disabled={loading}
              className={`px-4 py-2 rounded ${
                currentSetting.is_enabled
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              } disabled:opacity-50`}
            >
              {currentSetting.is_enabled ? 'غیرفعال کردن' : 'فعال کردن'}
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        <div>
          <label className="block text-xs font-medium text-gray-300 mb-2">استراتژی</label>
          <select
            value={selectedStrategy}
            onChange={(e) => {
              const newStrategyId = e.target.value ? Number(e.target.value) : ''
              setSelectedStrategy(newStrategyId)
              if (newStrategyId) {
                loadSettingsForStrategy(Number(newStrategyId))
              }
            }}
            className="select-compact"
          >
            <option value="">انتخاب استراتژی...</option>
            {strategies.length === 0 ? (
              <option value="" disabled>
                هیچ استراتژی یافت نشد
              </option>
            ) : (
              strategies.map((strategy) => {
                const statusLabels = []
                if (strategy.processing_status !== 'processed') {
                  statusLabels.push('پردازش نشده')
                }
                if (!strategy.is_active) {
                  statusLabels.push('غیرفعال')
                }
                const statusText = statusLabels.length > 0 ? ` (${statusLabels.join(', ')})` : ''
                
                return (
                  <option key={strategy.id} value={strategy.id}>
                    {strategy.name}{statusText}
                  </option>
                )
              })
            )}
          </select>
          {strategies.length === 0 && (
            <p className="text-xs text-yellow-400 mt-1">
              ⚠️ هیچ استراتژی آپلود نشده است. لطفاً ابتدا استراتژی را در بخش داشبورد آپلود کنید.
            </p>
          )}
          {strategies.length > 0 && (
            <p className="text-xs text-gray-400 mt-1">
              همه استراتژی‌ها نمایش داده می‌شوند. استراتژی‌های پردازش شده و فعال برای معامله خودکار مناسب‌تر هستند.
            </p>
          )}
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-300 mb-2">نماد</label>
          <input
            type="text"
            value={formData.symbol}
            onChange={(e) => setFormData({ ...formData, symbol: e.target.value.toUpperCase() })}
            className="input-compact"
            placeholder="XAUUSD"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-300 mb-2">تایم‌فریم (مثلاً M1, M5, M15, H1)</label>
          <input
            type="text"
            value={formData.timeframe}
            onChange={(e) => setFormData({ ...formData, timeframe: e.target.value.toUpperCase() })}
            className="input-compact"
            placeholder="M15"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-300 mb-2">حجم معامله (لات)</label>
          <input
            type="number"
            value={formData.volume}
            onChange={(e) => setFormData({ ...formData, volume: parseFloat(e.target.value) || 0.01 })}
            step="0.01"
            min="0.01"
            className="input-compact"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-300 mb-2">حداکثر معاملات باز همزمان</label>
          <input
            type="number"
            value={formData.max_open_trades}
            onChange={(e) => setFormData({ ...formData, max_open_trades: parseInt(e.target.value) || 3 })}
            min="1"
            max="10"
            className="input-compact"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-300 mb-2">
            فاصله زمانی بررسی (دقیقه)
          </label>
          <input
            type="number"
            value={formData.check_interval_minutes}
            onChange={(e) => setFormData({ ...formData, check_interval_minutes: parseInt(e.target.value) || 5 })}
            min="1"
            max="60"
            className="input-compact"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-300 mb-2">ریسک در هر معامله (%)</label>
          <input
            type="number"
            value={formData.risk_per_trade_percent}
            onChange={(e) => setFormData({ ...formData, risk_per_trade_percent: parseFloat(e.target.value) || 2.0 })}
            step="0.1"
            min="0.1"
            max="10"
            className="input-compact"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-300 mb-2">حد ضرر (پیپ)</label>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.use_stop_loss}
              onChange={(e) => setFormData({ ...formData, use_stop_loss: e.target.checked })}
              className="w-4 h-4"
            />
            <input
              type="number"
              value={formData.stop_loss_pips}
              onChange={(e) => setFormData({ ...formData, stop_loss_pips: parseFloat(e.target.value) || 50 })}
              step="1"
              min="0"
              disabled={!formData.use_stop_loss}
              className="input-compact disabled:opacity-50"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-300 mb-2">حد سود (پیپ)</label>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.use_take_profit}
              onChange={(e) => setFormData({ ...formData, use_take_profit: e.target.checked })}
              className="w-4 h-4"
            />
            <input
              type="number"
              value={formData.take_profit_pips}
              onChange={(e) => setFormData({ ...formData, take_profit_pips: parseFloat(e.target.value) || 100 })}
              step="1"
              min="0"
              disabled={!formData.use_take_profit}
              className="input-compact disabled:opacity-50"
            />
          </div>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={loading || !selectedStrategy}
          className="px-4 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'در حال ذخیره...' : 'ذخیره تنظیمات'}
        </button>
        
        <button
          onClick={handleTestSignal}
          disabled={testingSignal !== null || !selectedStrategy}
          className="px-4 py-1 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {testingSignal ? 'در حال تست...' : 'تست سیگنال'}
        </button>
        <button
          onClick={handleAddToMonitoring}
          disabled={loading || !selectedStrategy}
          className="px-4 py-1 text-sm bg-green-600 hover:bg-green-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          افزودن به پایش خودکار
        </button>
      </div>

      {/* Monitored strategies list */}
      <div className="bg-gray-700 rounded p-2 mt-2">
        <h3 className="text-white text-sm font-semibold mb-2">استراتژی‌های در حال پایش (معامله خودکار فعال)</h3>
        {monitored.length === 0 ? (
          <p className="text-xs text-gray-300">هیچ استراتژی فعالی ثبت نشده است. از دکمه «افزودن به پایش خودکار» استفاده کنید یا از لیست زیر «فعال کردن» را بزنید.</p>
        ) : (
          <ul className="space-y-2">
            {monitored.map(m => (
              <li key={m.id} className="flex items-center justify-between bg-gray-800 rounded px-2 py-2">
                <div className="text-sm text-white">
                  <div className="font-semibold">{m.strategy_name || `استراتژی #${m.strategy}`}</div>
                  <div className="text-xs text-gray-400">نماد: {m.symbol} | حجم پایه: {m.volume} | ریسک/معامله: {m.risk_per_trade_percent}% | حداکثر معاملات باز: {m.max_open_trades}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-0.5 rounded bg-green-700 text-white">فعال</span>
                  <button
                    onClick={() => m.id && handleToggle(m.id)}
                    disabled={loading}
                    className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded"
                  >
                    حذف از پایش
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Info Box */}
      <div className="bg-blue-900 bg-opacity-30 border border-blue-700 rounded p-2">
        <h3 className="text-white text-sm font-semibold mb-1">ℹ️ اطلاعات مهم:</h3>
        <ul className="text-gray-300 text-xs space-y-0.5 list-disc list-inside">
          <li>سیستم هر {formData.check_interval_minutes} دقیقه یکبار استراتژی را بررسی می‌کند</li>
          <li>برای معامله خودکار، MT5 باید همیشه باز و متصل باشد</li>
          <li>معاملات فقط در زمان باز بودن بازار (24/5) انجام می‌شوند</li>
        </ul>
      </div>

      {/* Current Settings Status */}
      {currentSetting && (
        <div className="bg-gray-700 rounded p-2">
          <h3 className="text-white text-sm font-semibold mb-1">وضعیت فعلی:</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <div>
              <span className="text-gray-400">وضعیت:</span>
              <span className={`ml-1 font-semibold ${currentSetting.is_enabled ? 'text-green-400' : 'text-red-400'}`}>
                {currentSetting.is_enabled ? 'فعال' : 'غیرفعال'}
              </span>
            </div>
            <div>
              <span className="text-gray-400">آخرین بررسی:</span>
              <span className="ml-1 text-white text-xs">
                {currentSetting.last_check_time 
                  ? new Date(currentSetting.last_check_time).toLocaleString('fa-IR')
                  : 'هنوز انجام نشده'}
              </span>
            </div>
            <div>
              <span className="text-gray-400">نماد:</span>
              <span className="ml-1 text-white">{currentSetting.symbol}</span>
            </div>
            <div>
              <span className="text-gray-400">حجم:</span>
              <span className="ml-1 text-white">{currentSetting.volume} لات</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

