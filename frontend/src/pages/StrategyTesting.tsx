import { useState, useEffect } from 'react'
import { getStrategies, getJobs, createJob, precheckBacktest, getJobStatus, getMT5Symbols, MT5Symbol } from '../api/client'
import { useToast } from '../components/ToastProvider'
import { useSymbol } from '../context/SymbolContext'
import { updateProfile } from '../api/auth'

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
  const [aiProvider, setAiProvider] = useState<string>('auto') // 'auto', 'gapgpt', 'gemini', 'openai'
  const { selectedSymbol, setSelectedSymbol } = useSymbol()
  // Initialize symbol from localStorage first (for immediate display), then context will override if available
  const [symbol, setSymbol] = useState(() => {
    return localStorage.getItem('backtest_symbol') || ''
  })
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
    // If context has a symbol, use it (it comes from profile and is more reliable)
    // Only update if current symbol is empty or different from context
    if (selectedSymbol && selectedSymbol.trim() !== '') {
      if (!symbol || symbol !== selectedSymbol) {
        setSymbol(selectedSymbol)
        localStorage.setItem('backtest_symbol', selectedSymbol)
      }
    } else {
      // If context doesn't have symbol but localStorage does, use localStorage
      const savedSymbol = localStorage.getItem('backtest_symbol')
      if (savedSymbol && savedSymbol.trim() !== '' && !symbol) {
        setSymbol(savedSymbol)
      }
    }
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

  // Popularity ranking for currency pairs (higher number = more popular)
  const getSymbolPopularity = (symbolName: string): number => {
    const name = symbolName.toUpperCase()
    
    // Gold - Most popular
    if (name === 'XAUUSD') return 1000
    if (name.includes('XAU')) return 900
    
    // Major Forex Pairs (Most traded)
    const majorPairs: { [key: string]: number } = {
      'EURUSD': 950,
      'GBPUSD': 940,
      'USDJPY': 930,
      'USDCHF': 920,
      'AUDUSD': 910,
      'USDCAD': 900,
      'NZDUSD': 890,
      'EURGBP': 880,
      'EURJPY': 870,
      'GBPJPY': 860,
      'EURCHF': 850,
      'AUDJPY': 840,
      'EURAUD': 830,
      'EURCAD': 820,
      'GBPAUD': 810,
      'GBPCAD': 800,
      'AUDCAD': 790,
      'AUDNZD': 780,
      'NZDCAD': 770,
      'NZDJPY': 760,
    }
    
    if (majorPairs[name]) return majorPairs[name]
    
    // Minor Forex Pairs
    const minorPairs: { [key: string]: number } = {
      'USDSEK': 700,
      'USDNOK': 690,
      'USDDKK': 680,
      'USDZAR': 670,
      'USDMXN': 660,
      'USDBRL': 650,
      'USDTRY': 640,
      'USDCNH': 630,
      'USDSGD': 620,
      'USDHKD': 610,
      'EURSEK': 600,
      'EURNOK': 590,
      'EURDKK': 580,
      'EURTRY': 570,
      'EURPLN': 560,
      'EURZAR': 550,
      'GBPSEK': 540,
      'GBPNOK': 530,
      'GBPTRY': 520,
      'GBPZAR': 510,
    }
    
    if (minorPairs[name]) return minorPairs[name]
    
    // Popular Crypto
    const cryptoPairs: { [key: string]: number } = {
      'BTCUSD': 850,
      'ETHUSD': 840,
      'BNBUSD': 830,
      'ADAUSD': 820,
      'SOLUSD': 810,
      'XRPUSD': 800,
      'DOTUSD': 790,
      'DOGEUSD': 780,
      'AVAXUSD': 770,
      'MATICUSD': 760,
      'LINKUSD': 750,
      'UNIUSD': 740,
      'LTCUSD': 730,
      'ATOMUSD': 720,
      'ALGOUSD': 710,
    }
    
    if (cryptoPairs[name]) return cryptoPairs[name]
    
    // Check if it's a crypto pair
    if (name.includes('BTC') || name.includes('ETH') || name.includes('CRYPTO') || 
        name.includes('USDT') || name.includes('USDC')) {
      return 500
    }
    
    // Check if it's a forex pair (contains common currency codes)
    const forexPattern = /(USD|EUR|GBP|JPY|CHF|AUD|CAD|NZD|SEK|NOK|DKK|ZAR|MXN|BRL|TRY|CNH|SGD|HKD|PLN)/
    if (forexPattern.test(name)) {
      return 400
    }
    
    // Unknown/Exotic pairs - lowest priority
    return 100
  }
  
  // Categorize symbol
  const getSymbolCategory = (symbolName: string): 'gold' | 'major_forex' | 'minor_forex' | 'crypto' | 'other' => {
    const name = symbolName.toUpperCase()
    
    if (name.includes('XAU') || name.includes('GOLD')) {
      return 'gold'
    }
    
    if (name.includes('BTC') || name.includes('ETH') || name.includes('CRYPTO') || 
        name.includes('USDT') || name.includes('USDC') || name.includes('BNB') ||
        name.includes('ADA') || name.includes('SOL') || name.includes('XRP') ||
        name.includes('DOT') || name.includes('DOGE') || name.includes('AVAX') ||
        name.includes('MATIC') || name.includes('LINK') || name.includes('UNI') ||
        name.includes('LTC') || name.includes('ATOM') || name.includes('ALGO')) {
      return 'crypto'
    }
    
    // Major pairs
    const majorPairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 
                       'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY', 'EURCHF', 'AUDJPY',
                       'EURAUD', 'EURCAD', 'GBPAUD', 'GBPCAD', 'AUDCAD', 'AUDNZD',
                       'NZDCAD', 'NZDJPY']
    if (majorPairs.includes(name)) {
      return 'major_forex'
    }
    
    // Check if it's a forex pair
    const forexPattern = /(USD|EUR|GBP|JPY|CHF|AUD|CAD|NZD|SEK|NOK|DKK|ZAR|MXN|BRL|TRY|CNH|SGD|HKD|PLN)/
    if (forexPattern.test(name)) {
      return 'minor_forex'
    }
    
    return 'other'
  }

  const loadMT5Symbols = async () => {
    setLoadingSymbols(true)
    try {
      const response = await getMT5Symbols(true) // only available symbols
      if (response.data?.status === 'success' && response.data.symbols) {
        const symbols = response.data.symbols as MT5Symbol[]
        // Sort symbols by popularity and category
        const sortedSymbols = symbols
          .filter(s => s.is_available)
          .sort((a, b) => {
            const catA = getSymbolCategory(a.name)
            const catB = getSymbolCategory(b.name)
            
            // Category order: gold > major_forex > minor_forex > crypto > other
            const categoryOrder: { [key: string]: number } = {
              'gold': 1,
              'major_forex': 2,
              'minor_forex': 3,
              'crypto': 4,
              'other': 5
            }
            
            const catDiff = categoryOrder[catA] - categoryOrder[catB]
            if (catDiff !== 0) return catDiff
            
            // Within same category, sort by popularity
            const popA = getSymbolPopularity(a.name)
            const popB = getSymbolPopularity(b.name)
            return popB - popA // Higher popularity first
          })
        setAvailableSymbols(sortedSymbols)
        // Don't auto-select symbol - user must choose
        // Only set if symbol is completely empty and we have a selectedSymbol from context
        if (sortedSymbols.length > 0 && !symbol && selectedSymbol) {
          setSymbol(selectedSymbol)
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

    if (!symbol || symbol.trim() === '') {
      setError('لطفاً نماد معاملاتی (جفت ارز) را انتخاب کنید')
      showToast('لطفاً نماد معاملاتی (جفت ارز) را انتخاب کنید', { type: 'error' })
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
        selected_indicators: selectedIndicators,
        ai_provider: aiProvider !== 'auto' ? aiProvider : undefined
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
        // اگر timeout رخ داد، ممکن است job ایجاد شده باشد اما response برنگشته باشد
        // در این صورت، job را از طریق polling بررسی می‌کنیم
        const timeoutMessage = 'درخواست بک تست زمان زیادی طول کشید. در حال بررسی وضعیت...'
        showToast(timeoutMessage, { type: 'info' })
        
        // سعی می‌کنیم آخرین job کاربر را پیدا کنیم
        try {
          const jobsResponse = await getJobs()
          if (jobsResponse.data && jobsResponse.data.length > 0) {
            const latestJob = jobsResponse.data[0]
            if (latestJob.status === 'pending' || latestJob.status === 'running') {
              // Job ایجاد شده است، polling را شروع می‌کنیم
              setRunningJob(latestJob.id)
              setJobStatus(latestJob.status || 'running')
              checkJobStatus(latestJob.id)
              showToast('بک تست در حال اجرا است. لطفاً منتظر بمانید...', { type: 'info' })
              return
            }
          }
        } catch (pollError) {
          console.error('Error checking jobs:', pollError)
        }
        
        // اگر job پیدا نشد، خطا را نمایش می‌دهیم
        const finalErrorMessage = 'بک‌تست برای بازه زمانی انتخاب شده بیش از حد زمان نیاز داشت. لطفاً کمی صبر کنید یا بازه زمانی را کاهش دهید. اگر مشکل ادامه داشت، صفحه را رفرش کنید و دوباره تلاش کنید.'
        showToast(finalErrorMessage, { type: 'warning' })
        setError(finalErrorMessage)
        return
      }
      setError('خطا در شروع بک تست: ' + (error.message || 'خطای نامشخص'))
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
                نماد معاملاتی (جفت ارز) <span className="text-red-400">*</span>
              </label>
              <select
                value={symbol}
                onChange={async (e) => {
                  const newSymbol = e.target.value
                  setSymbol(newSymbol)
                  // Save immediately when user selects
                  if (newSymbol && newSymbol.trim() !== '') {
                    localStorage.setItem('backtest_symbol', newSymbol)
                    setSelectedSymbol(newSymbol)
                    // Save to profile in background
                    try {
                      await updateProfile(undefined, undefined, newSymbol)
                    } catch (err) {
                      console.error('Failed to save symbol to profile:', err)
                      // Don't show error, localStorage is enough
                    }
                  }
                }}
                className={`select-compact ${!symbol || symbol.trim() === '' ? 'border-red-500' : ''}`}
                disabled={runningJob !== null || loadingSymbols}
                required
              >
                {loadingSymbols ? (
                  <option value="">در حال بارگذاری...</option>
                ) : availableSymbols.length > 0 ? (
                  (() => {
                    // Group symbols by category
                    const grouped: { [key: string]: MT5Symbol[] } = {
                      gold: [],
                      major_forex: [],
                      minor_forex: [],
                      crypto: [],
                      other: []
                    }
                    
                    availableSymbols.forEach(sym => {
                      const category = getSymbolCategory(sym.name)
                      grouped[category].push(sym)
                    })
                    
                    return (
                      <>
                        <option value="">انتخاب جفت ارز...</option>
                        {grouped.gold.length > 0 && (
                          <optgroup label="🥇 طلا (Gold)">
                            {grouped.gold.map((sym) => (
                              <option key={sym.name} value={sym.name}>
                                {sym.name} {sym.description ? `- ${sym.description}` : ''}
                              </option>
                            ))}
                          </optgroup>
                        )}
                        {grouped.major_forex.length > 0 && (
                          <optgroup label="💱 فارکس اصلی (Major Forex)">
                            {grouped.major_forex.map((sym) => (
                              <option key={sym.name} value={sym.name}>
                                {sym.name} {sym.description ? `- ${sym.description}` : ''}
                              </option>
                            ))}
                          </optgroup>
                        )}
                        {grouped.minor_forex.length > 0 && (
                          <optgroup label="💱 فارکس فرعی (Minor Forex)">
                            {grouped.minor_forex.map((sym) => (
                              <option key={sym.name} value={sym.name}>
                                {sym.name} {sym.description ? `- ${sym.description}` : ''}
                              </option>
                            ))}
                          </optgroup>
                        )}
                        {grouped.crypto.length > 0 && (
                          <optgroup label="₿ کریپتو (Cryptocurrency)">
                            {grouped.crypto.map((sym) => (
                              <option key={sym.name} value={sym.name}>
                                {sym.name} {sym.description ? `- ${sym.description}` : ''}
                              </option>
                            ))}
                          </optgroup>
                        )}
                        {grouped.other.length > 0 && (
                          <optgroup label="📊 سایر (Other)">
                            {grouped.other.map((sym) => (
                              <option key={sym.name} value={sym.name}>
                                {sym.name} {sym.description ? `- ${sym.description}` : ''}
                              </option>
                            ))}
                          </optgroup>
                        )}
                      </>
                    )
                  })()
                ) : (
                  <>
                    <option value="">انتخاب جفت ارز...</option>
                    <optgroup label="🥇 طلا (Gold)">
                      <option value="XAUUSD">XAUUSD - Gold/USD</option>
                      <option value="XAUUSD_l">XAUUSD_l - Gold/USD (Live)</option>
                      <option value="XAUUSD_o">XAUUSD_o - Gold/USD (Demo)</option>
                    </optgroup>
                  </>
                )}
              </select>
              {(!symbol || symbol.trim() === '') && (
                <p className="text-xs text-red-400 mt-1">
                  انتخاب جفت ارز اجباری است
                </p>
              )}
              {availableSymbols.length > 0 && symbol && symbol.trim() !== '' && (
                <p className="text-xs text-gray-400 mt-1">
                  {availableSymbols.filter(s => s.is_available).length} جفت ارز در دسترس از MetaTrader 5
                </p>
              )}
            </div>
          </div>

          {/* AI Provider Selection */}
          <div className="mb-6">
            <label className="label-standard">
              🔮 مدل هوش مصنوعی برای تحلیل بک تست
            </label>
            <select
              value={aiProvider}
              onChange={(e) => setAiProvider(e.target.value)}
              className="select-standard"
              disabled={runningJob !== null}
            >
              <option value="auto">🤖 خودکار (پیش‌فرض) - سیستم بهترین مدل را انتخاب می‌کند</option>
              <option value="gapgpt">🔮 GapGPT - مدل تخصصی تحلیل معاملات (هزینه: ~0.001 تومان/کلمه)</option>
              <option value="gemini">💎 Gemini AI - مدل سریع و مقرون‌به‌صرفه گوگل (هزینه: رایگان تا ~0.0003 تومان/کلمه)</option>
              <option value="openai">⚡ OpenAI GPT-4o-mini - مدل قدرتمند OpenAI (هزینه: ~0.0008 تومان/کلمه)</option>
            </select>
            <div className="mt-2 p-3 bg-gray-800 rounded-lg border border-gray-700">
              {aiProvider === 'auto' && (
                <div>
                  <p className="text-sm text-gray-300 mb-2">
                    <strong className="text-white">🤖 حالت خودکار:</strong> سیستم به طور خودکار بهترین مدل در دسترس را بر اساس تنظیمات شما انتخاب می‌کند.
                  </p>
                  <p className="text-xs text-gray-400">
                    <strong>هزینه:</strong> بستگی به مدل انتخاب شده دارد (معمولاً Gemini یا OpenAI)
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    <strong>مناسب برای:</strong> کاربرانی که می‌خواهند سیستم بهینه‌ترین انتخاب را انجام دهد
                  </p>
                </div>
              )}
              {aiProvider === 'gapgpt' && (
                <div>
                  <p className="text-sm text-gray-300 mb-2">
                    <strong className="text-white">🔮 GapGPT:</strong> مدل تخصصی طراحی شده برای تحلیل استراتژی‌های معاملاتی و نتایج بک تست. این مدل به طور خاص برای درک و تحلیل داده‌های مالی و معاملاتی بهینه شده است.
                  </p>
                  <p className="text-xs text-gray-400">
                    <strong>💰 هزینه:</strong> تقریباً 0.001 تومان به ازای هر کلمه (ورودی + خروجی)
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    <strong>✅ مناسب برای:</strong> تحلیل‌های تخصصی معاملات، بررسی دقیق نتایج بک تست، دریافت توصیه‌های حرفه‌ای برای بهینه‌سازی استراتژی
                  </p>
                  <p className="text-xs text-yellow-400 mt-2">
                    ⚠️ برای استفاده، ابتدا کلید API GapGPT را در تنظیمات اضافه کنید.
                  </p>
                </div>
              )}
              {aiProvider === 'gemini' && (
                <div>
                  <p className="text-sm text-gray-300 mb-2">
                    <strong className="text-white">💎 Gemini AI (Google):</strong> مدل سریع و کارآمد گوگل با قابلیت پردازش متن‌های طولانی. این مدل برای تحلیل‌های عمومی و سریع ایده‌آل است.
                  </p>
                  <p className="text-xs text-gray-400">
                    <strong>💰 هزینه:</strong> رایگان در سطح محدود، یا تقریباً 0.0003 تومان به ازای هر کلمه در نسخه پرداختی
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    <strong>✅ مناسب برای:</strong> تحلیل‌های سریع و روزمره، کاربرانی که به دنبال تعادل بین کیفیت و هزینه هستند، تحلیل‌های با حجم متوسط
                  </p>
                </div>
              )}
              {aiProvider === 'openai' && (
                <div>
                  <p className="text-sm text-gray-300 mb-2">
                    <strong className="text-white">⚡ OpenAI GPT-4o-mini:</strong> مدل قدرتمند و پیشرفته OpenAI با دقت بالا در تحلیل و تولید متن. این مدل برای تحلیل‌های پیچیده و دقیق مناسب است.
                  </p>
                  <p className="text-xs text-gray-400">
                    <strong>💰 هزینه:</strong> تقریباً 0.0008 تومان به ازای هر کلمه (ورودی + خروجی)
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    <strong>✅ مناسب برای:</strong> تحلیل‌های دقیق و حرفه‌ای، تولید گزارش‌های جامع، تحلیل‌های پیچیده با جزئیات زیاد
                  </p>
                </div>
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
              disabled={runningJob !== null || !selectedStrategy || !symbol || symbol.trim() === ''}
              className={`btn-success ${
                runningJob !== null || !selectedStrategy || !symbol || symbol.trim() === ''
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

