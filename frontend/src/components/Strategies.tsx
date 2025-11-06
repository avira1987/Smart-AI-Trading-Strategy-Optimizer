import { useState, useEffect, useRef } from 'react'
import { getStrategies, addStrategy, deleteStrategy as apiDeleteStrategy, processStrategy, getAPIConfigurations } from '../api/client'
import { useToast } from './ToastProvider'
import StrategyQuestions from './StrategyQuestions'
import StrategyOptimizer from './StrategyOptimizer'
import AIRecommendations from './AIRecommendations'

interface TradingStrategy {
  id: number
  name: string
  description: string
  strategy_file: string
  is_active: boolean
  uploaded_at: string
  parsed_strategy_data?: any
  processing_status?: 'not_processed' | 'processing' | 'processed' | 'failed'
  processed_at?: string
  processing_error?: string
}

export default function Strategies() {
  const [strategies, setStrategies] = useState<TradingStrategy[]>([])
  const [showModal, setShowModal] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [expandedStrategyId, setExpandedStrategyId] = useState<number | null>(null)
  const [collapsedQuestionsStrategyIds, setCollapsedQuestionsStrategyIds] = useState<Set<number>>(new Set())
  const [hasGeminiAPI, setHasGeminiAPI] = useState(false)
  const { showToast } = useToast()
  const expandedStrategyIdRef = useRef<number | null>(null)
  
  // Sync ref with state
  useEffect(() => {
    expandedStrategyIdRef.current = expandedStrategyId
  }, [expandedStrategyId])

  useEffect(() => {
    loadStrategies()
    checkGeminiAPI()
    
    // Check Gemini API status periodically (every 30 seconds)
    // But only update if the value actually changed to avoid unnecessary re-renders
    const interval = setInterval(() => {
      checkGeminiAPI()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])



  const checkGeminiAPI = async () => {
    try {
      const response = await getAPIConfigurations()
      let apisData = []
      if (response.data && response.data.results) {
        apisData = response.data.results
      } else if (Array.isArray(response.data)) {
        apisData = response.data
      }
      
      // Check if there's an active Gemini API configuration
      const geminiApi = apisData.find((api: any) => 
        api.provider === 'gemini' && api.is_active === true
      )
      const hasApi = !!geminiApi
      
      // Only update state if the value actually changed to avoid unnecessary re-renders
      setHasGeminiAPI(prev => prev !== hasApi ? hasApi : prev)
    } catch (error) {
      console.error('Error checking Gemini API:', error)
      // Only update if it was previously true
      setHasGeminiAPI(prev => prev ? false : prev)
    }
  }

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
      
      // Preserve expandedStrategyId if the strategy still exists
      const currentExpanded = expandedStrategyIdRef.current
      setStrategies(strategiesData)
      
      // Clean up collapsedQuestionsStrategyIds for strategies that no longer exist
      setCollapsedQuestionsStrategyIds(prev => {
        const newSet = new Set<number>()
        const existingIds = new Set(strategiesData.map((s: TradingStrategy) => s.id))
        // Keep collapsed state only for strategies that still exist
        prev.forEach(id => {
          if (existingIds.has(id)) {
            newSet.add(id)
          }
        })
        return newSet
      })
      
      // Restore expanded state if the strategy still exists
      if (currentExpanded) {
        const strategyStillExists = strategiesData.find((s: TradingStrategy) => s.id === currentExpanded)
        if (strategyStillExists) {
          // Restore expanded state after state update
          setExpandedStrategyId(currentExpanded)
        } else {
          setExpandedStrategyId(null)
        }
      }
    } catch (error) {
      console.error('Error loading strategies:', error)
      setStrategies([])
      showToast('Failed to load strategies', { type: 'error' })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      showToast('Please select a file', { type: 'warning' })
      return
    }

    try {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('description', description)
      formData.append('strategy_file', file)

      console.log('Submitting strategy:', { name, description, file: file.name }) // Debug log
      
      const response = await addStrategy(formData)
      console.log('Strategy upload response:', response) // Debug log
      
      showToast('Strategy uploaded successfully!', { type: 'success' })
      setShowModal(false)
      setName('')
      setDescription('')
      setFile(null)
      
      // Reload strategies after successful upload
      await loadStrategies()
    } catch (error: any) {
      console.error('Error uploading strategy:', error)
      showToast('Error uploading strategy: ' + (error?.response?.data?.detail || 'Unknown error'), { type: 'error' })
    }
  }

  const toggleStrategy = async (id: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/strategies/${id}/toggle_active/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        await loadStrategies()
        showToast('Strategy status updated', { type: 'success' })
      } else {
        showToast('Error toggling strategy status', { type: 'error' })
      }
    } catch (error) {
      console.error('Error toggling strategy:', error)
      showToast('Error toggling strategy status', { type: 'error' })
    }
  }

  const handleDelete = async (id: number, name: string) => {
    const confirmDelete = window.confirm(`آیا از حذف استراتژی «${name}» مطمئن هستید؟ این عمل قابل بازگشت نیست.`)
    if (!confirmDelete) return
    try {
      await apiDeleteStrategy(id)
      showToast('استراتژی با موفقیت حذف شد', { type: 'success' })
      await loadStrategies()
    } catch (error) {
      console.error('Error deleting strategy:', error)
      showToast('خطا در حذف استراتژی', { type: 'error' })
    }
  }

  const handleProcess = async (id: number, name: string) => {
    try {
      showToast('در حال پردازش استراتژی...', { type: 'info' })
      const response = await processStrategy(id)
      
      console.log('Process response:', response) // Debug log
      
      if (response.data.status === 'success') {
        showToast(`استراتژی «${name}» با موفقیت پردازش شد`, { type: 'success' })
        await loadStrategies()
        await checkGeminiAPI() // Recheck API status after processing
      } else {
        const errorMsg = response.data.message || response.data.error || 'خطای نامشخص'
        showToast(`خطا در پردازش استراتژی: ${errorMsg}`, { type: 'error' })
        await loadStrategies()
        await checkGeminiAPI() // Recheck API status even on error
      }
    } catch (error: any) {
      console.error('Error processing strategy:', error)
      console.error('Error response:', error?.response)
      console.error('Error data:', error?.response?.data)
      
      // Extract error message from different possible locations
      const errorMsg = 
        error?.response?.data?.message || 
        error?.response?.data?.error || 
        error?.response?.data?.detail ||
        error?.message ||
        'خطای نامشخص'
      
      showToast(`خطا در پردازش استراتژی: ${errorMsg}`, { type: 'error' })
      await loadStrategies()
      await checkGeminiAPI() // Recheck API status even on error
    }
  }

  const getProcessingStatusLabel = (status?: string) => {
    switch (status) {
      case 'not_processed':
        return { text: 'پردازش نشده', color: 'bg-gray-600 text-gray-200' }
      case 'processing':
        return { text: 'در حال پردازش...', color: 'bg-yellow-600 text-yellow-200' }
      case 'processed':
        return { text: 'پردازش شده', color: 'bg-green-700 text-green-200' }
      case 'failed':
        return { text: 'خطا در پردازش', color: 'bg-red-700 text-red-200' }
      default:
        return { text: 'پردازش نشده', color: 'bg-gray-600 text-gray-200' }
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 mb-6 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">استراتژی‌های معاملاتی</h2>
        <button
          onClick={() => setShowModal(true)}
          className="btn-success"
        >
          + افزودن استراتژی جدید
        </button>
      </div>

      {strategies.length === 0 ? (
        <p className="text-gray-400">هنوز استراتژی ثبت نشده است. برای افزودن، روی دکمه زیر کلیک کنید.</p>
      ) : (
        <div className="space-y-3">
          {strategies.map((strategy) => (
            <div key={strategy.id} className="bg-gray-700 rounded-lg p-5">
              {/* Action Buttons - Top Row */}
              <div className="flex gap-2 flex-wrap mb-4">
                <button
                  onClick={() => handleProcess(strategy.id, strategy.name)}
                  disabled={strategy.processing_status === 'processing'}
                  className={`px-4 py-2 rounded-lg transition text-sm font-medium ${
                    strategy.processing_status === 'processing'
                      ? 'bg-gray-500 cursor-not-allowed text-gray-300'
                      : 'bg-purple-600 hover:bg-purple-700 text-white'
                  }`}
                >
                  {strategy.processing_status === 'processing' ? 'در حال پردازش...' : 'پردازش'}
                </button>
                <button
                  onClick={() => {
                    setCollapsedQuestionsStrategyIds(prev => {
                      const newSet = new Set(prev)
                      if (newSet.has(strategy.id)) {
                        newSet.delete(strategy.id)
                      } else {
                        newSet.add(strategy.id)
                      }
                      return newSet
                    })
                  }}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition text-sm font-medium"
                >
                  {collapsedQuestionsStrategyIds.has(strategy.id) ? '💬 سوالات تعاملی' : 'بستن سوالات'}
                </button>
                <button
                  onClick={() => toggleStrategy(strategy.id)}
                  className={`px-4 py-2 rounded-lg transition text-sm font-medium ${
                    strategy.is_active
                      ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  {strategy.is_active ? 'غیرفعال کن' : 'فعال کن'}
                </button>
                <a
                  href="/testing"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium inline-block"
                >
                  تست استراتژی
                </a>
                <button
                  onClick={() => handleDelete(strategy.id, strategy.name)}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition text-sm font-medium"
                >
                  حذف
                </button>
              </div>

              {/* Strategy Content - Full Width */}
              <div>
                <div className="flex items-center gap-3 mb-3 flex-wrap">
                  <h3 className="text-white font-medium text-lg">{strategy.name}</h3>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      strategy.is_active
                        ? 'bg-green-700 text-green-200'
                        : 'bg-gray-600 text-gray-300'
                    }`}
                  >
                    {strategy.is_active ? 'فعال' : 'غیرفعال'}
                  </span>
                  {strategy.processing_status && (
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${getProcessingStatusLabel(strategy.processing_status).color}`}
                    >
                      {getProcessingStatusLabel(strategy.processing_status).text}
                    </span>
                  )}
                </div>
                <p className="text-gray-300 text-sm mb-3 leading-relaxed">{strategy.description}</p>
                <div className="text-gray-400 text-xs space-y-1">
                  <div>تاریخ ثبت: {new Date(strategy.uploaded_at).toLocaleDateString('fa-IR')}</div>
                  {strategy.processed_at && (
                    <div>تاریخ پردازش: {new Date(strategy.processed_at).toLocaleDateString('fa-IR')}</div>
                  )}
                </div>
              </div>
              
              {/* Error Display */}
              {strategy.processing_error && (
                <div className="text-red-400 text-xs mb-3">
                  خطا: {strategy.processing_error}
                </div>
              )}
              
              {/* Strategy Data and Analysis Section - Full Width */}
              {strategy.processing_status === 'processed' && strategy.parsed_strategy_data && (
                <>
                  <div className="text-green-400 text-xs mb-3">
                    اعتماد: {(strategy.parsed_strategy_data.confidence_score * 100).toFixed(0)}% | 
                    نماد: {strategy.parsed_strategy_data.symbol || 'تعیین نشده'} | 
                    تایم‌فریم: {strategy.parsed_strategy_data.timeframe || 'تعیین نشده'}
                  </div>
                  
                  {/* تحلیل استراتژی - Full Width */}
                  {strategy.parsed_strategy_data.analysis ? (
                    <div className="w-full mt-3 p-4 bg-gradient-to-br from-gray-700 to-gray-600 rounded-lg border border-gray-500">
                          <h4 className="text-white font-bold text-base mb-3 pb-2 border-b border-gray-400">
                            📊 تحلیل استراتژی
                            {strategy.parsed_strategy_data.analysis.quality_score && (
                              <span className="mr-2 text-xs font-normal text-gray-300">
                                (امتیاز کیفیت: {strategy.parsed_strategy_data.analysis.quality_score}/100)
                              </span>
                            )}
                            {strategy.parsed_strategy_data.analysis.is_basic && (
                              <span className="mr-2 text-xs font-normal text-yellow-400 bg-yellow-900/30 px-2 py-1 rounded">
                                تحلیل پایه
                              </span>
                            )}
                          </h4>
                          <div className="space-y-4 text-sm">
                            {/* خلاصه کلی */}
                            {strategy.parsed_strategy_data.analysis.summary && (
                              <div className="bg-gray-700 p-3 rounded border-r-4 border-blue-500">
                                <h5 className="text-blue-300 font-semibold mb-2">خلاصه کلی:</h5>
                                <p className="text-gray-200 leading-relaxed">{strategy.parsed_strategy_data.analysis.summary}</p>
                              </div>
                            )}
                            
                            {/* نقاط قوت */}
                            {strategy.parsed_strategy_data.analysis.strengths && strategy.parsed_strategy_data.analysis.strengths.length > 0 && (
                              <div>
                                <h5 className="text-green-400 font-semibold mb-2">✅ نقاط قوت:</h5>
                                <ul className="list-disc list-inside mr-4 space-y-1 text-gray-200">
                                  {strategy.parsed_strategy_data.analysis.strengths.map((strength: string, idx: number) => (
                                    <li key={idx}>{strength}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {/* نقاط ضعف */}
                            {strategy.parsed_strategy_data.analysis.weaknesses && strategy.parsed_strategy_data.analysis.weaknesses.length > 0 && (
                              <div>
                                <h5 className="text-orange-400 font-semibold mb-2">⚠️ نقاط ضعف:</h5>
                                <ul className="list-disc list-inside mr-4 space-y-1 text-gray-200">
                                  {strategy.parsed_strategy_data.analysis.weaknesses.map((weakness: string, idx: number) => (
                                    <li key={idx}>{weakness}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {/* ارزیابی ریسک */}
                            {strategy.parsed_strategy_data.analysis.risk_assessment && (
                              <div className="bg-gray-700 p-3 rounded border-r-4 border-yellow-500">
                                <h5 className="text-yellow-300 font-semibold mb-2">⚠️ ارزیابی ریسک:</h5>
                                <p className="text-gray-200 leading-relaxed">{strategy.parsed_strategy_data.analysis.risk_assessment}</p>
                              </div>
                            )}
                            
                            {/* پیشنهادات */}
                            {strategy.parsed_strategy_data.analysis.recommendations && strategy.parsed_strategy_data.analysis.recommendations.length > 0 && (
                              <div>
                                <h5 className="text-purple-400 font-semibold mb-2">💡 پیشنهادات و توصیه‌ها:</h5>
                                <ul className="list-disc list-inside mr-4 space-y-1 text-gray-200">
                                  {strategy.parsed_strategy_data.analysis.recommendations.map((rec: string, idx: number) => (
                                    <li key={idx}>{rec}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {/* پیام راهنمایی برای تحلیل پایه - فقط اگر کلید Gemini موجود نباشد */}
                            {strategy.parsed_strategy_data.analysis.is_basic && !hasGeminiAPI && (
                              <div className="mt-3 p-3 bg-blue-900/30 rounded-lg border border-blue-700">
                                <p className="text-blue-300 text-xs mb-2">
                                  💡 نکته: این تحلیل پایه است که بر اساس داده‌های استخراج شده از استراتژی تولید شده است.
                                </p>
                                <p className="text-blue-200 text-xs">
                                  برای دریافت تحلیل پیشرفته با هوش مصنوعی:
                                  <br />
                                  <br />
                                  1. به Google AI Studio بروید و کلید API دریافت کنید
                                  <br />
                                  <br />
                                  2. در داشبورد، به بخش "تنظیمات API" بروید
                                  <br />
                                  <br />
                                  3. روی دکمه "افزودن کلید API" کلیک کنید
                                  <br />
                                  <br />
                                  4. ارائه‌دهنده را "Gemini AI (Google AI Studio)" انتخاب کنید
                                  <br />
                                  <br />
                                  5. کلید API خود را وارد و ذخیره کنید
                                  <br />
                                  <br />
                                  6. پس از ذخیره، استراتژی را مجدداً پردازش کنید (دکمه "پردازش")
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        /* اگر تحلیل وجود نداشت، خلاصه شرایط را نمایش بده */
                        <div className="mt-3 p-3 bg-gray-600 rounded-lg border border-gray-500">
                          <h4 className="text-white font-semibold text-sm mb-2 pb-1 border-b border-gray-500">
                            خلاصه شرایط استراتژی
                          </h4>
                          <div className="space-y-2 text-xs">
                            {/* شرایط ورود */}
                            {strategy.parsed_strategy_data.entry_conditions && strategy.parsed_strategy_data.entry_conditions.length > 0 && (
                              <div>
                                <span className="text-green-300 font-medium">شرایط ورود:</span>
                                <ul className="list-disc list-inside mr-4 mt-1 text-gray-300">
                                  {strategy.parsed_strategy_data.entry_conditions.map((condition: string, idx: number) => (
                                    <li key={idx} className="mb-1">{condition}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {/* شرایط خروج */}
                            {strategy.parsed_strategy_data.exit_conditions && strategy.parsed_strategy_data.exit_conditions.length > 0 && (
                              <div>
                                <span className="text-red-300 font-medium">شرایط خروج:</span>
                                <ul className="list-disc list-inside mr-4 mt-1 text-gray-300">
                                  {strategy.parsed_strategy_data.exit_conditions.map((condition: string, idx: number) => (
                                    <li key={idx} className="mb-1">{condition}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {/* مدیریت ریسک */}
                            {strategy.parsed_strategy_data.risk_management && Object.keys(strategy.parsed_strategy_data.risk_management).length > 0 && (
                              <div>
                                <span className="text-yellow-300 font-medium">مدیریت ریسک:</span>
                                <div className="mr-4 mt-1 text-gray-300 space-y-1">
                                  {strategy.parsed_strategy_data.risk_management.stop_loss && (
                                    <div>حد ضرر: {strategy.parsed_strategy_data.risk_management.stop_loss}</div>
                                  )}
                                  {strategy.parsed_strategy_data.risk_management.take_profit && (
                                    <div>حد سود: {strategy.parsed_strategy_data.risk_management.take_profit}</div>
                                  )}
                                  {strategy.parsed_strategy_data.risk_management.risk_per_trade && (
                                    <div>ریسک هر معامله: {strategy.parsed_strategy_data.risk_management.risk_per_trade}</div>
                                  )}
                                  {strategy.parsed_strategy_data.risk_management.position_size && (
                                    <div>اندازه موقعیت: {strategy.parsed_strategy_data.risk_management.position_size}</div>
                                  )}
                                </div>
                              </div>
                            )}
                            {/* اندیکاتورها */}
                            {strategy.parsed_strategy_data.indicators && strategy.parsed_strategy_data.indicators.length > 0 && (
                              <div>
                                <span className="text-blue-300 font-medium">اندیکاتورها:</span>
                                <div className="mr-4 mt-1 text-gray-300">
                                  {strategy.parsed_strategy_data.indicators.join('، ')}
                                </div>
                              </div>
                            )}
                          </div>
                          {/* پیام راهنمایی - فقط اگر کلید Gemini موجود نباشد */}
                          {!hasGeminiAPI && (
                            <div className="mt-3 p-3 bg-blue-900/30 rounded-lg border border-blue-700">
                              <p className="text-blue-300 text-xs mb-2">
                                💡 نکته: این تحلیل پایه است که بر اساس داده‌های استخراج شده از استراتژی تولید شده است.
                              </p>
                              <p className="text-blue-200 text-xs">
                                برای دریافت تحلیل پیشرفته با هوش مصنوعی:
                                <br />
                                <br />
                                1. به Google AI Studio بروید و کلید API دریافت کنید
                                <br />
                                <br />
                                2. در داشبورد، به بخش "تنظیمات API" بروید
                                <br />
                                <br />
                                3. روی دکمه "افزودن کلید API" کلیک کنید
                                <br />
                                <br />
                                4. ارائه‌دهنده را "Gemini AI (Google AI Studio)" انتخاب کنید
                                <br />
                                <br />
                                5. کلید API خود را وارد و ذخیره کنید
                                <br />
                                <br />
                                6. پس از ذخیره، استراتژی را مجدداً پردازش کنید (دکمه "پردازش")
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )}
                  
                  {/* Strategy Questions Section - Always visible unless collapsed */}
                  {!collapsedQuestionsStrategyIds.has(strategy.id) && (
                    <div className="mt-4 space-y-4">
                      <div className="p-4 bg-gray-800 rounded-lg border border-gray-600">
                        <StrategyQuestions 
                          strategyId={strategy.id}
                          onComplete={() => {
                            loadStrategies()
                          }}
                        />
                      </div>
                      
                      {/* AI Recommendations Section */}
                      {strategy.processing_status === 'processed' && (
                        <div className="p-4 bg-gray-800 rounded-lg border border-gray-600">
                          <AIRecommendations 
                            strategyId={strategy.id}
                            strategyName={strategy.name}
                          />
                        </div>
                      )}
                      
                      {/* Strategy Optimizer Section */}
                      {strategy.processing_status === 'processed' && (
                        <div className="p-4 bg-gray-800 rounded-lg border border-gray-600">
                          <StrategyOptimizer 
                            strategyId={strategy.id}
                            strategyName={strategy.name}
                          />
                        </div>
                      )}
                    </div>
                  )}
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="text-xl font-semibold text-white mb-4">آپلود استراتژی جدید</h3>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="label-standard">نام استراتژی</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="input-standard"
                  placeholder="نام استراتژی"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="label-standard">توضیحات</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="textarea-standard"
                  rows={4}
                  placeholder="توضیح ..."
                  required
                />
              </div>
              <div className="mb-4">
                <label className="label-standard">فایل استراتژی</label>
                <input
                  type="file"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  accept=".txt,.md,.pdf,.doc,.docx"
                  className="w-full px-4 py-2.5 bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 file:cursor-pointer"
                  required
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="flex-1 btn-success"
                >
                  آپلود
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 btn-secondary"
                >
                  انصراف
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
