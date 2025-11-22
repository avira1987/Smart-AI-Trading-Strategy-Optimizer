import { useState, useEffect } from 'react'
import { getStrategies, getJobs, createJob, precheckBacktest, getJobStatus, getMT5Symbols, MT5Symbol } from '../api/client'
import { useToast } from '../components/ToastProvider'
import { useSymbol } from '../context/SymbolContext'

interface Strategy {
  id: number
  name: string
  description: string
  uploaded_at: string
  is_primary: boolean
}

// Job interface removed - not used

const TECHNICAL_INDICATORS = [
  { id: 'rsi', name: 'RSI (شاخص قدرت نسبی)', label: 'RSI' },
  { id: 'macd', name: 'MACD (میانگین متحرک همگرا واگرا)', label: 'MACD' },
  { id: 'sma', name: 'SMA (میانگین متحرک ساده)', label: 'SMA' },
  { id: 'ema', name: 'EMA (میانگین متحرک نمایی)', label: 'EMA' },
  { id: 'bollinger', name: 'Bollinger Bands (باندهای بولینگر)', label: 'Bollinger' },
  { id: 'stochastic', name: 'Stochastic (استوکاستیک)', label: 'Stochastic' },
  { id: 'williams_r', name: 'Williams %R', label: 'Williams %R' },
  { id: 'atr', name: 'ATR (میانگین محدوده واقعی)', label: 'ATR' },
  { id: 'adx', name: 'ADX (شاخص میانگین جهت)', label: 'ADX' },
  { id: 'cci', name: 'CCI (شاخص کانال کالا)', label: 'CCI' },
]

export default function StrategyTesting() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [selectedStrategy, setSelectedStrategy] = useState<number | null>(null)
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>([])
  const [timeframe, setTimeframe] = useState('7')
  const [initialCapital, setInitialCapital] = useState('10000')
  const { selectedSymbol } = useSymbol()
  const [symbol, setSymbol] = useState('XAUUSD')
  const [availableSymbols, setAvailableSymbols] = useState<MT5Symbol[]>([])
  const [loadingSymbols, setLoadingSymbols] = useState(false)
  const [runningJob, setRunningJob] = useState<number | null>(null)
  const [jobStatus, setJobStatus] = useState('')
  const [error, setError] = useState('')
  const { showToast } = useToast()

  useEffect(() => {
    loadStrategies()
    loadJobs()
    loadMT5Symbols()
  }, [])

  useEffect(() => {
    setSymbol(selectedSymbol)
  }, [selectedSymbol])

  const loadStrategies = async () => {
    try {
      const response = await getStrategies()
      console.log('Strategies response:', response) // Debug log
      
      // Handle Django REST Framework pagination format
      let strategiesData = []
      if (response.data && response.data.results) {
        strategiesData = response.data.results
      } else if (Array.isArray(response.data)) {
        strategiesData = response.data
      }
      
      console.log('Strategies data:', strategiesData) // Debug log
      const normalizedStrategies = strategiesData as Strategy[]
      setStrategies(normalizedStrategies)
      setSelectedStrategy((prev) => {
        if (prev !== null && normalizedStrategies.some((strategy) => strategy.id === prev)) {
          return prev
        }
        const primaryStrategy = normalizedStrategies.find((strategy) => strategy.is_primary)
        if (primaryStrategy) {
          return primaryStrategy.id
        }
        return normalizedStrategies.length > 0 ? normalizedStrategies[0].id : null
      })
    } catch (error) {
      console.error('Error loading strategies:', error)
    }
  }

  const loadJobs = async () => {
    try {
      const response = await getJobs()
      if (response.data && response.data.length > 0) {
        const latestJob = response.data[0]
        if (latestJob.status === 'running' || latestJob.status === 'pending') {
          setRunningJob(latestJob.id)
          checkJobStatus(latestJob.id)
        }
      }
    } catch (error) {
      console.error('Error loading jobs:', error)
    }
  }

  const loadMT5Symbols = async () => {
    setLoadingSymbols(true)
    try {
      const response = await getMT5Symbols(true) // only available symbols
      if (response.data?.status === 'success' && response.data.symbols) {
        const symbols = response.data.symbols as MT5Symbol[]
        setAvailableSymbols(symbols)
        // Set default symbol to first available or XAUUSD
        if (symbols.length > 0 && !symbol) {
          const defaultSymbol = symbols.find(s => s.name?.includes('XAU')) || symbols[0]
          if (defaultSymbol) {
            setSymbol(defaultSymbol.name || 'XAUUSD')
          }
        }
      }
    } catch (error) {
      console.error('Error loading MT5 symbols:', error)
      // Fallback to default symbols if API fails
      setAvailableSymbols([
        { name: 'XAUUSD', description: 'Gold/USD', is_available: true },
        { name: 'XAUUSD_l', description: 'Gold/USD (Live)', is_available: true },
        { name: 'XAUUSD_o', description: 'Gold/USD (Demo)', is_available: true },
      ])
    } finally {
      setLoadingSymbols(false)
    }
  }

  const checkJobStatus = async (jobId: number) => {
    try {
      const response = await getJobStatus(jobId)
      const data = response.data
      setJobStatus(data.status)
      
      if (data.status === 'completed') {
        setRunningJob(null)
        // Check if there are actual results
        if (data.result_id) {
          showToast('بک‌تست با موفقیت انجام شد! برای مشاهده نتایج، صفحه نتایج را بررسی کنید.', { type: 'success' })
        } else {
          showToast('بک‌تست تکمیل شد اما نتیجه‌ای ثبت نشد. لطفاً لاگ‌ها را بررسی کنید.', { type: 'warning' })
        }
      } else if (data.status === 'failed') {
        setRunningJob(null)
        const msg = data.error_message || 'بک‌تست ناموفق. جزئیات در دسترس نیست.'
        setError(msg)
        showToast(`خطا: ${msg}`, { type: 'error' })
      } else if (data.status === 'running' || data.status === 'pending') {
        // Continue polling
        setTimeout(() => checkJobStatus(jobId), 2000)
      } else {
        // Unknown status, continue polling
        setTimeout(() => checkJobStatus(jobId), 2000)
      }
    } catch (error) {
      console.error('Error checking job status:', error)
      // Continue polling even on error (network issues)
      setTimeout(() => checkJobStatus(jobId), 2000)
    }
  }

  const handleRunBacktest = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedStrategy) {
      setError('لطفاً یک استراتژی را انتخاب کنید')
      return
    }

    setError('')
    
    try {
      // Precheck data availability for the selected strategy
      const pre = await precheckBacktest(selectedStrategy)
      const preStatus = pre.data?.status
      const preMsg = pre.data?.message || 'پیش‌بررسی انجام شد'
      if (preStatus === 'not_ready' || preStatus === 'error') {
        showToast(preMsg, { type: 'error' })
        setError(preMsg)
        return
      }
      if (preStatus === 'ready_with_fallback') {
        showToast(preMsg, { type: 'warning' })
      } else if (preStatus === 'ready') {
        showToast(preMsg, { type: 'success' })
      }

      const response = await createJob({
        strategy: selectedStrategy,
        job_type: 'backtest',
        timeframe_days: Number(timeframe),
        symbol: symbol,
        initial_capital: Number(initialCapital),
        selected_indicators: selectedIndicators
      })
      
      setRunningJob(response.data.id)
      setJobStatus(response.data.status || 'running')
      checkJobStatus(response.data.id)
      showToast('بک‌تست شروع شد! در حال پردازش...', { type: 'info' })
      if (Number(timeframe) >= 365) {
        showToast('بک‌تست برای بازه‌های زمانی طولانی ممکن است چند دقیقه طول بکشد. لطفاً منتظر بمانید.', {
          type: 'warning'
        })
      }
      
      // Redirect to results page after 3 seconds on success only (handled in status poll)
    } catch (error: any) {
      console.error('Error running backtest:', error)
      if (error?.code === 'ECONNABORTED' || (typeof error?.message === 'string' && error.message.toLowerCase().includes('timeout'))) {
        const timeoutMessage = 'بک‌تست برای بازه زمانی انتخاب شده بیش از حد زمان نیاز داشت و متوقف شد. لطفاً کمی صبر کنید یا بازه زمانی را کاهش دهید.'
        showToast(timeoutMessage, { type: 'warning' })
        setError(timeoutMessage)
        return
      }
      setError('خطا در شروع بازیابی: ' + (error.message || 'خطای نامشخص'))
    }
  }

  const selectedStrategyData = strategies.find(s => s.id === selectedStrategy)

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">تست استراتژی</h1>
        <p className="text-gray-400">برای تست استراتژی معامله‌گری و بهینه‌سازی، پارامترهای مورد نظر خود را انتخاب کنید.</p>
      </div>

      {/* Main Testing Form */}
      <div className="card-standard mb-6">
        <form onSubmit={handleRunBacktest}>
          {/* Strategy Selection */}
          <div className="mb-6">
            <label className="label-standard">
              انتخاب استراتژی
            </label>
            <select
              value={selectedStrategy || ''}
              onChange={(e) => setSelectedStrategy(Number(e.target.value))}
              className="select-standard"
              disabled={runningJob !== null}
            >
              <option value="">یک استراتژی انتخاب کنید...</option>
              {strategies.map((strategy) => (
                <option key={strategy.id} value={strategy.id}>
                  {strategy.name}
                  {strategy.is_primary ? ' (استراتژی اصلی)' : ''}
                  {' - '}
                  {new Date(strategy.uploaded_at).toLocaleDateString()}
                </option>
              ))}
            </select>
            
            {selectedStrategyData && (
              <div className="mt-3 p-3 bg-gray-700 rounded">
                <p className="text-gray-300 text-sm">
                  <strong>توضیحات:</strong> {selectedStrategyData.description || 'بدون توضیح'}
                </p>
              </div>
            )}
          </div>

          {/* Technical Indicators Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              اندیکاتورهای تکنیکال (اختیاری)
            </label>
            <p className="text-xs text-gray-400 mb-3">
              در صورت تمایل می‌توانید یک یا چند اندیکاتور تکنیکال را انتخاب کنید تا با استراتژی متنی شما ترکیب شود. 
              در غیر این صورت فقط با استراتژی متنی که از فایل اپلودی شما استخراج شده بک‌تست انجام می‌شود.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 p-4 bg-gray-700 rounded-lg">
              {TECHNICAL_INDICATORS.map((indicator) => (
                <label
                  key={indicator.id}
                  className="flex items-center space-x-2 space-x-reverse cursor-pointer hover:bg-gray-600 p-2 rounded transition"
                >
                  <input
                    type="checkbox"
                    checked={selectedIndicators.includes(indicator.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedIndicators([...selectedIndicators, indicator.id])
                      } else {
                        setSelectedIndicators(selectedIndicators.filter(id => id !== indicator.id))
                      }
                    }}
                    disabled={runningJob !== null}
                    className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-300">{indicator.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Backtest Settings */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="label-standard">
                بازه زمانی
              </label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="select-compact"
                disabled={runningJob !== null}
              >
                <option value="1">۱ روز</option>
                <option value="7">۷ روز</option>
                <option value="30">۳۰ روز</option>
                <option value="90">۳ ماه</option>
                <option value="365">۱ سال</option>
              </select>
            </div>

            <div>
              <label className="label-standard">
                سرمایه اولیه (دلار)
              </label>
              <input
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(e.target.value)}
                className="input-compact"
                disabled={runningJob !== null}
              />
            </div>

            <div>
              <label className="label-standard">
                نماد معاملاتی (جفت ارز)
              </label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="select-compact"
                disabled={runningJob !== null || loadingSymbols}
              >
                {loadingSymbols ? (
                  <option value="">در حال بارگذاری...</option>
                ) : availableSymbols.length > 0 ? (
                  <>
                    <option value="">انتخاب جفت ارز...</option>
                    {availableSymbols
                      .filter(s => s.is_available)
                      .map((sym) => (
                        <option key={sym.name} value={sym.name}>
                          {sym.name} {sym.description ? `(${sym.description})` : ''}
                        </option>
                      ))}
                  </>
                ) : (
                  <>
                    <option value="XAUUSD">XAUUSD (Gold/USD)</option>
                    <option value="XAUUSD_l">XAUUSD_l (Gold/USD Live)</option>
                    <option value="XAUUSD_o">XAUUSD_o (Gold/USD Demo)</option>
                  </>
                )}
              </select>
              {availableSymbols.length > 0 && (
                <p className="text-xs text-gray-400 mt-1">
                  {availableSymbols.filter(s => s.is_available).length} جفت ارز در دسترس از MetaTrader 5
                </p>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-900 text-red-200 rounded">
              <span className="font-bold">خطا: </span>{error}
            </div>
          )}

          {/* Run Button */}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={runningJob !== null || !selectedStrategy}
              className={`btn-success ${
                runningJob !== null || !selectedStrategy
                  ? 'opacity-50 cursor-not-allowed'
                  : ''
              }`}
            >
              {runningJob !== null ? (
                <span className="flex items-center justify-center">
                  <span className="animate-spin mr-2">⏳</span>
                  تست در حال انجام...
                </span>
              ) : (
                'شروع تست'
              )}
            </button>

            <a
              href="/results"
              className="btn-primary px-6 py-2.5"
            >
              مشاهده نتایج
            </a>
          </div>
        </form>
      </div>

      {/* Status Display */}
      {runningJob !== null && (
        <div className={`rounded-lg p-4 border ${
          jobStatus === 'failed' 
            ? 'bg-red-900 bg-opacity-30 border-red-500' 
            : jobStatus === 'completed'
            ? 'bg-green-900 bg-opacity-30 border-green-500'
            : 'bg-blue-900 bg-opacity-30 border-blue-500'
        }`}>
          <p className={`${
            jobStatus === 'failed' 
              ? 'text-red-200' 
              : jobStatus === 'completed'
              ? 'text-green-200'
              : 'text-blue-200'
          }`}>
            <strong>وضعیت بک‌تست:</strong> {
              jobStatus === 'running' ? 'در حال اجرا...' :
              jobStatus === 'pending' ? 'در انتظار شروع...' :
              jobStatus === 'completed' ? 'تکمیل شد ✓' :
              jobStatus === 'failed' ? 'ناموفق ✗' :
              'نامشخص'
            } | شماره تست: {runningJob}
          </p>
          <p className={`${
            jobStatus === 'failed' 
              ? 'text-red-300' 
              : jobStatus === 'completed'
              ? 'text-green-300'
              : 'text-blue-300'
          } text-sm mt-2`}>
            {jobStatus === 'running' || jobStatus === 'pending' 
              ? 'بک‌تست استراتژی شما در حال پردازش است. نتیجه تست را در صفحه نتایج مشاهده خواهید کرد.'
              : jobStatus === 'completed'
              ? 'بک‌تست با موفقیت انجام شد. برای مشاهده جزئیات، صفحه نتایج را بررسی کنید.'
              : 'بک‌تست با خطا مواجه شد. لطفاً پارامترها و تنظیمات را بررسی کنید.'
            }
          </p>
          {(jobStatus === 'running' || jobStatus === 'pending') && (
            <div className="mt-3">
              <div className="w-full bg-gray-700 rounded-full h-2.5">
                <div className="bg-blue-600 h-2.5 rounded-full animate-pulse" style={{ width: '60%' }}></div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Information Box */}
      <div className="card-standard">
        <h2 className="text-lg font-semibold text-white mb-4 text-right">راهنمای تست استراتژی</h2>
        <ul className="text-gray-400 space-y-2 text-right">
          <li>۱. استراتژی مورد نظر خود را انتخاب کنید</li>
          <li>۲. پارامترهای تست (بازه زمانی، سرمایه، نماد) را وارد کنید</li>
          <li>۳. برای شروع تحلیل، دکمه "شروع تست" را بزنید</li>
          <li>۴. نتایج را در صفحه نتایج مشاهده نمایید</li>
        </ul>
      </div>
    </div>
  )
}

