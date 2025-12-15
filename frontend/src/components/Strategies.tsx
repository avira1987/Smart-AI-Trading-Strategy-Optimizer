import { useState, useEffect, useRef } from 'react'
import { getStrategies, addStrategy, deleteStrategy as apiDeleteStrategy, processStrategy, getStrategyProgress, getAPIConfigurations, setPrimaryStrategy, downloadStrategy, getStrategyFileContent, toggleStrategyActive, ensureCsrfToken, getJobs } from '../api/client'
import { useToast } from './ToastProvider'
import StrategyQuestions from './StrategyQuestions'
import StrategyOptimizer from './StrategyOptimizer'
import AIRecommendations from './AIRecommendations'
import GapGPTConverter from './GapGPTConverter'
import { useRateLimit } from '../hooks/useRateLimit'

const AI_PROVIDER_REFRESH_MS = 120000

interface TradingStrategy {
  id: number
  name: string
  description: string
  strategy_file: string
  is_active: boolean
  is_primary: boolean
  uploaded_at: string
  parsed_strategy_data?: any
  processing_status?: 'not_processed' | 'processing' | 'processed' | 'failed'
  processed_at?: string
  processing_error?: string
  analysis_sources?: any
  analysis_sources_display?: any
  has_backtest_capability?: boolean
}

export default function Strategies() {
  const [strategies, setStrategies] = useState<TradingStrategy[]>([])
  const [showModal, setShowModal] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [inputMode, setInputMode] = useState<'file' | 'text'>('file')
  const [strategyText, setStrategyText] = useState('')
  const [expandedStrategyId, setExpandedStrategyId] = useState<number | null>(null)
  const [collapsedQuestionsStrategyIds, setCollapsedQuestionsStrategyIds] = useState<Set<number>>(new Set())
  const [expandedDetailsStrategyIds, setExpandedDetailsStrategyIds] = useState<Set<number>>(new Set())
  const [hasAIProvider, setHasAIProvider] = useState(false)
  const [processingStrategies, setProcessingStrategies] = useState<Map<number, { progress: number; stage: string; message: string }>>(new Map())
  const [showGapGPTModal, setShowGapGPTModal] = useState(false)
  const [selectedStrategyForGapGPT, setSelectedStrategyForGapGPT] = useState<TradingStrategy | null>(null)
  const [gapGPTFileContent, setGapGPTFileContent] = useState<string>('')
  const [loadingFileContent, setLoadingFileContent] = useState(false)
  const [strategiesWithRecommendations, setStrategiesWithRecommendations] = useState<Set<number>>(new Set())
  const { showToast } = useToast()
  const expandedStrategyIdRef = useRef<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const rateLimitClickSubmit = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'strategies-submit' })
  const rateLimitClickToggle = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'strategies-toggle' })
  const rateLimitClickDelete = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'strategies-delete' })
  const rateLimitClickProcess = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'strategies-process' })
  const rateLimitClickSetPrimary = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'strategies-setPrimary' })
  
  // Sync ref with state
  useEffect(() => {
    expandedStrategyIdRef.current = expandedStrategyId
  }, [expandedStrategyId])

  useEffect(() => {
    loadStrategies()
    checkAIProvider()
    checkImprovementRecommendations()
    
    // Check AI provider status periodically with throttling
    const interval = setInterval(() => {
      if (typeof document !== 'undefined' && document.hidden) {
        return
      }
      checkAIProvider()
    }, AI_PROVIDER_REFRESH_MS)
    
    return () => clearInterval(interval)
  }, [])



  const checkAIProvider = async () => {
    try {
      const response = await getAPIConfigurations()
      let apisData = []
      if (response.data && response.data.results) {
        apisData = response.data.results
      } else if (Array.isArray(response.data)) {
        apisData = response.data
      }
      
      // Check if there's an active AI provider configuration (GapGPT or other supported LLMs)
      const aiProviders = ['gapgpt', 'cohere', 'openrouter', 'together_ai', 'deepinfra', 'groq']
      const activeAIProvider = apisData.find((api: any) => 
        aiProviders.includes(api.provider) && api.is_active === true
      )
      const hasApi = !!activeAIProvider
      
      // Only update state if the value actually changed to avoid unnecessary re-renders
      setHasAIProvider(prev => prev !== hasApi ? hasApi : prev)
    } catch (error) {
      console.error('Error checking AI provider API:', error)
      // Only update if it was previously true
      setHasAIProvider(prev => prev ? false : prev)
    }
  }

  const checkImprovementRecommendations = async () => {
    try {
      const jobsResponse = await getJobs()
      const normalizeArrayResponse = <T = any>(data: any): T[] => {
        if (!data) return []
        if (Array.isArray(data)) return data
        if (Array.isArray(data?.results)) return data.results
        if (Array.isArray(data?.data)) return data.data
        return []
      }
      
      const jobsData = normalizeArrayResponse(jobsResponse.data)
      const strategiesWithRecs = new Set<number>()
      
      // Check each job's result for improvement recommendations
      for (const job of jobsData) {
        if (job.result && job.result.improvement_recommendations && 
            Array.isArray(job.result.improvement_recommendations) && 
            job.result.improvement_recommendations.length > 0) {
          // Get strategy ID from job
          if (job.strategy && typeof job.strategy === 'object' && job.strategy.id) {
            strategiesWithRecs.add(job.strategy.id)
          } else if (typeof job.strategy === 'number') {
            strategiesWithRecs.add(job.strategy)
          }
        }
      }
      
      setStrategiesWithRecommendations(strategiesWithRecs)
    } catch (error) {
      console.error('Error checking improvement recommendations:', error)
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate based on input mode
    if (inputMode === 'file') {
      if (!file) {
        showToast('لطفاً یک فایل انتخاب کنید', { type: 'warning' })
        return
      }
    } else if (inputMode === 'text') {
      if (!strategyText.trim()) {
        showToast('لطفاً متن استراتژی را وارد کنید', { type: 'warning' })
        return
      }
    } else {
      showToast('لطفاً یک روش ورود استراتژی را انتخاب کنید', { type: 'warning' })
      return
    }

    const submitAction = rateLimitClickSubmit(async () => {
      try {
        const formData = new FormData()
        formData.append('name', name)
        formData.append('description', description)
        
        if (inputMode === 'file' && file) {
          formData.append('strategy_file', file)
        } else if (inputMode === 'text' && strategyText.trim()) {
          formData.append('strategy_text', strategyText.trim())
        }

        console.log('Submitting strategy:', { name, description, inputMode, file: file?.name, textLength: strategyText.length }) // Debug log
        
        const response = await addStrategy(formData)
        console.log('Strategy upload response:', response) // Debug log
        
        showToast('استراتژی با موفقیت ثبت شد!', { type: 'success' })
        setShowModal(false)
        setName('')
        setDescription('')
        setFile(null)
        setStrategyText('')
        setInputMode('file')
        
        // Reload strategies after successful upload
        await loadStrategies()
      } catch (error: any) {
        console.error('Error uploading strategy:', error)
        
        // Extract error message from different possible locations
        let errorMessage = 'خطای نامشخص'
        
        if (error?.response?.data) {
          // Try different error message fields
          errorMessage = 
            error.response.data.detail ||
            error.response.data.message ||
            error.response.data.error ||
            (typeof error.response.data === 'string' ? error.response.data : 'خطای نامشخص')
          
          // If it's an object with multiple errors, try to format it
          if (typeof error.response.data === 'object' && !error.response.data.detail && !error.response.data.message) {
            const errorKeys = Object.keys(error.response.data)
            if (errorKeys.length > 0) {
              const firstError = error.response.data[errorKeys[0]]
              if (Array.isArray(firstError)) {
                errorMessage = firstError[0]
              } else if (typeof firstError === 'string') {
                errorMessage = firstError
              }
            }
          }
        } else if (error?.message) {
          errorMessage = error.message
        }
        
        // Show more detailed error message
        showToast(`خطا در ثبت استراتژی: ${errorMessage}`, { type: 'error', duration: 8000 })
      }
    })
    
    submitAction()
  }

  const toggleStrategy = async (id: number) => {
    const toggleAction = rateLimitClickToggle(async () => {
      try {
        const response = await toggleStrategyActive(id)
        
        if (response.data) {
          await loadStrategies()
          const message = response.data.is_active ? 'استراتژی فعال شد' : 'استراتژی غیرفعال شد'
          showToast(message, { type: 'success' })
        } else {
          showToast('خطا در تغییر وضعیت استراتژی', { type: 'error' })
        }
      } catch (error: any) {
        console.error('Error toggling strategy:', error)
        const errorMsg = error.response?.data?.message || error.message || 'خطا در تغییر وضعیت استراتژی'
        showToast(errorMsg, { type: 'error' })
      }
    })
    
    toggleAction()
  }

  const handleOpenGapGPTModal = async (strategy: TradingStrategy) => {
    try {
      setSelectedStrategyForGapGPT(strategy)
      setLoadingFileContent(true)
      setGapGPTFileContent('')
      
      // دریافت محتوای فایل استراتژی
      try {
        const response = await getStrategyFileContent(strategy.id)
        if (response.data.status === 'success' && response.data.content) {
          setGapGPTFileContent(response.data.content)
        } else {
          // اگر فایل موجود نبود، از parsed_strategy_data یا description استفاده کن
          const fallbackText = strategy.parsed_strategy_data
            ? JSON.stringify(strategy.parsed_strategy_data, null, 2)
            : strategy.description || ''
          setGapGPTFileContent(fallbackText)
          if (!fallbackText) {
            showToast('هشدار: فایل استراتژی یافت نشد. لطفاً متن استراتژی را وارد کنید.', { type: 'warning' })
          }
        }
      } catch (fileError: any) {
        console.error('Error loading file content:', fileError)
        // در صورت خطا، از parsed_strategy_data یا description استفاده کن
        const fallbackText = strategy.parsed_strategy_data
          ? JSON.stringify(strategy.parsed_strategy_data, null, 2)
          : strategy.description || ''
        setGapGPTFileContent(fallbackText)
        if (!fallbackText) {
          showToast('خطا در خواندن فایل. لطفاً متن استراتژی را وارد کنید.', { type: 'warning' })
        }
      } finally {
        setLoadingFileContent(false)
        setShowGapGPTModal(true)
      }
    } catch (error) {
      console.error('Error opening GapGPT modal:', error)
      setLoadingFileContent(false)
      showToast('خطا در باز کردن مودال GPT', { type: 'error' })
    }
  }

  const handleDelete = (id: number, name: string) => {
    const confirmDelete = window.confirm(`آیا از حذف استراتژی «${name}» مطمئن هستید؟ این عمل قابل بازگشت نیست.`)
    if (!confirmDelete) return
    
    const deleteAction = rateLimitClickDelete(async () => {
      try {
        await apiDeleteStrategy(id)
        showToast('استراتژی با موفقیت حذف شد', { type: 'success' })
        await loadStrategies()
      } catch (error: any) {
        console.error('Error deleting strategy:', error)
        console.error('Error response:', error?.response)
        console.error('Error data:', error?.response?.data)
        
        // Extract error message from different possible locations
        const errorMsg = 
          error?.response?.data?.error || 
          error?.response?.data?.message || 
          error?.response?.data?.detail ||
          error?.message ||
          'خطا در حذف استراتژی'
        
        showToast(errorMsg, { type: 'error' })
      }
    })
    
    deleteAction()
  }

  // @ts-ignore - Reserved for future use
  const handleProcess = (id: number, name: string) => {
    const processAction = rateLimitClickProcess(async () => {
      try {
        const processStartedAt = performance.now()
        showToast('در حال پردازش استراتژی...', { type: 'info' })
        
        // Ensure CSRF token is available before processing
        try {
          await ensureCsrfToken()
        } catch (csrfError) {
          console.warn('CSRF token check failed, proceeding anyway:', csrfError)
        }
        
        // Initialize progress tracking
        setProcessingStrategies(prev => new Map(prev).set(id, { progress: 0, stage: 'شروع', message: 'در حال آماده‌سازی...' }))
        
        // Start polling for progress
        const progressInterval = setInterval(async () => {
          try {
            const progressResponse = await getStrategyProgress(id)
            if (progressResponse.data) {
              const progressData = progressResponse.data
              setProcessingStrategies(prev => new Map(prev).set(id, {
                progress: progressData.progress || 0,
                stage: progressData.stage || '',
                message: progressData.message || ''
              }))
              
              // Stop polling if processing is complete or failed
              if (progressData.processing_status === 'processed' || progressData.processing_status === 'failed') {
                clearInterval(progressInterval)
                setProcessingStrategies(prev => {
                  const newMap = new Map(prev)
                  newMap.delete(id)
                  return newMap
                })
              }
            }
          } catch (error) {
            console.error('Error fetching progress:', error)
          }
        }, 1000) // Poll every second
        
        const response = await processStrategy(id)
        
        // Clear interval when request completes
        clearInterval(progressInterval)
        setProcessingStrategies(prev => {
          const newMap = new Map(prev)
          newMap.delete(id)
          return newMap
        })
        
        console.log('Process response:', response) // Debug log
        
        if (response.data.status === 'success') {
          const elapsedSeconds = (performance.now() - processStartedAt) / 1000
          const analysisSourceDisplay = response?.data?.analysis_sources_display || {}
          const analysisSources = response?.data?.analysis_sources || {}
          const tokenInfo = response?.data?.token_info || {}
          const aiModelDisplay =
            analysisSourceDisplay?.ai_model_display ||
            analysisSourceDisplay?.analysis_method_display ||
            analysisSources?.ai_model ||
            analysisSources?.analysis_method ||
            'تحلیل پایه'
          const aiStatusDisplay =
            analysisSourceDisplay?.ai_status_display || analysisSources?.ai_status || ''
          const durationDisplay =
            analysisSourceDisplay?.processing_duration_display ||
            `${elapsedSeconds.toFixed(2)} ثانیه`
          const aiFallbackReason =
            analysisSourceDisplay?.ai_fallback_reason_display ||
            analysisSourceDisplay?.ai_message_display ||
            analysisSources?.ai_fallback_reason ||
            analysisSources?.ai_message ||
            analysisSources?.ai_error ||
            ''

          const isBasicAnalysis = aiModelDisplay === 'هیچکدام' || aiModelDisplay === 'تحلیل پایه'
          const toastMessageParts = [
            `استراتژی «${name}» با ${isBasicAnalysis ? 'تحلیل پایه' : aiModelDisplay}`
          ]
          if (aiStatusDisplay && !isBasicAnalysis) {
            toastMessageParts.push(`(وضعیت: ${aiStatusDisplay})`)
          }
          toastMessageParts.push(`در ${durationDisplay} پردازش شد (آنلاین).`)
          
          // نمایش اطلاعات توکن‌های مصرفی
          if (tokenInfo && tokenInfo.total_tokens) {
            const tokenCount = tokenInfo.total_tokens
            const inputTokens = tokenInfo.input_tokens || ''
            const outputTokens = tokenInfo.output_tokens || ''
            if (inputTokens && outputTokens) {
              toastMessageParts.push(`توکن‌های مصرفی: ${tokenCount.toLocaleString('fa-IR')} (ورودی: ${inputTokens.toLocaleString('fa-IR')}، خروجی: ${outputTokens.toLocaleString('fa-IR')})`)
            } else {
              toastMessageParts.push(`توکن‌های مصرفی: ${tokenCount.toLocaleString('fa-IR')}`)
            }
          }
          
          if (isBasicAnalysis && aiFallbackReason) {
            toastMessageParts.push(`دلیل عدم استفاده از هوش مصنوعی: ${aiFallbackReason}`)
          }

          showToast(toastMessageParts.join(' '), { type: 'success', duration: 10000 })
          await loadStrategies()
          await checkAIProvider() // Recheck AI status after processing
        } else {
          const errorMsg = response.data.message || response.data.error || 'خطای نامشخص'
          showToast(`خطا در پردازش استراتژی: ${errorMsg}`, { type: 'error' })
          await loadStrategies()
          await checkAIProvider() // Recheck AI status even on error
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
        
        // Reload strategies immediately to get latest status
        await loadStrategies()
        await checkAIProvider() // Recheck AI status even on error
        
        // If error was timeout or network error, retry loading strategies after delay
        // to ensure we get the updated status from server (backend may have set status to 'failed')
        if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout') || !error?.response) {
          // Retry loading strategies after 2 seconds to get updated status
          setTimeout(async () => {
            await loadStrategies()
          }, 2000)
          
          // Retry one more time after 5 seconds to ensure status is updated
          setTimeout(async () => {
            await loadStrategies()
          }, 5000)
        }
      }
    })
    
    processAction()
  }

  const handleSetPrimary = (id: number, name: string) => {
    const setPrimaryAction = rateLimitClickSetPrimary(async () => {
      try {
        await setPrimaryStrategy(id)
        showToast(`استراتژی «${name}» به‌عنوان استراتژی اصلی انتخاب شد`, { type: 'success' })
        await loadStrategies()
      } catch (error: any) {
        console.error('Error setting primary strategy:', error)
        const message =
          error?.response?.data?.message ||
          error?.response?.data?.detail ||
          error?.message ||
          'خطای نامشخص'
        showToast(`خطا در تعیین استراتژی اصلی: ${message}`, { type: 'error' })
      }
    })
    
    setPrimaryAction()
  }

  const handleDownload = async (id: number, _name: string) => {
    try {
      const response = await downloadStrategy(id)
      
      // ایجاد لینک دانلود
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // استخراج نام فایل اصلی از header (همان نام فایل آپلود شده با پسوند کامل)
      const contentDisposition = response.headers['content-disposition'] || response.headers['Content-Disposition']
      let filename = null
      
      if (contentDisposition) {
        // اول تلاش برای استخراج از فرمت RFC 2231 (filename*=UTF-8''encoded)
        const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
        if (utf8Match) {
          try {
            filename = decodeURIComponent(utf8Match[1].trim())
          } catch (e) {
            console.warn('Error decoding UTF-8 filename:', e)
          }
        }
        
        // اگر از RFC 2231 استخراج نشد، از فرمت ساده استفاده کن
        if (!filename) {
          // الگوهای مختلف برای استخراج نام فایل
          const patterns = [
            /filename="([^"]+)"/i,  // filename="file.docx"
            /filename=([^;]+)/i,    // filename=file.docx
            /filename\*="?([^";]+)"?/i,  // filename*="encoded"
          ]
          
          for (const pattern of patterns) {
            const match = contentDisposition.match(pattern)
            if (match && match[1]) {
              filename = match[1].trim()
              // حذف quotes اگر وجود دارد
              filename = filename.replace(/^["']|["']$/g, '')
              break
            }
          }
        }
      }
      
      // اگر نام فایل از header استخراج نشد، لاگ کن و از نام پیش‌فرض استفاده کن
      if (!filename) {
        console.warn('Could not extract filename from Content-Disposition header:', contentDisposition)
        // استفاده از نام پیش‌فرض با پسوند .docx (چون کاربر گفت فایل Word است)
        // اما بهتر است از backend درخواست کنیم که header را ارسال کند
        filename = `strategy_${id}.docx`
      }
      
      // اطمینان از اینکه نام فایل پسوند دارد
      if (filename && !filename.includes('.')) {
        // اگر پسوند ندارد، .docx اضافه کن (برای فایل‌های Word)
        filename = `${filename}.docx`
      }
      
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
      showToast('فایل با موفقیت دانلود شد', { type: 'success' })
    } catch (error: any) {
      console.error('Error downloading strategy:', error)
      const message =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        error?.message ||
        'خطای نامشخص'
      showToast(`خطا در دانلود فایل: ${message}`, { type: 'error' })
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

      {/* راهنمای آپلود استراتژی برای بهترین نتایج بک‌تست */}
      <div className="bg-gradient-to-r from-blue-900/50 to-purple-900/50 border border-blue-700 rounded-lg p-4 mb-4">
        <div className="flex items-start gap-3">
          <div className="text-2xl">📚</div>
          <div className="flex-1">
            <h3 className="text-white font-semibold mb-3">راهنمای آپلود استراتژی برای بهترین نتایج بک‌تست</h3>
            <p className="text-gray-300 text-sm mb-3">
              برای دریافت بیشترین بازدهی در بک‌تست‌های خود، لطفاً نکات زیر را قبل از آپلود استراتژی مطالعه کنید:
            </p>
            <ul className="text-gray-300 text-sm space-y-2 list-disc list-inside mr-4">
              <li><strong className="text-white">استراتژی کامل و واضح:</strong> استراتژی شما باید شامل تمام قوانین معاملاتی، شرایط ورود و خروج، مدیریت ریسک و پارامترهای قابل تنظیم باشد.</li>
              <li><strong className="text-white">کد تمیز و ساختاریافته:</strong> از کدهای تمیز و خوش‌خوان استفاده کنید. کامنت‌های واضح و نام‌گذاری مناسب متغیرها به هوش مصنوعی کمک می‌کند تا استراتژی را بهتر درک کند.</li>
              <li><strong className="text-white">توضیحات کامل:</strong> در ابتدای فایل استراتژی، توضیح دهید که استراتژی چه کاری انجام می‌دهد، برای چه بازه زمانی مناسب است و چه نوع بازارهایی را هدف قرار می‌دهد.</li>
              <li><strong className="text-white">پارامترهای قابل تنظیم:</strong> تمام پارامترهای مهم (مثل stop loss، take profit، دوره‌های اندیکاتورها) را به صورت متغیر تعریف کنید تا در بک‌تست قابل تنظیم باشند.</li>
              <li><strong className="text-white">منطق معاملاتی واضح:</strong> شرایط ورود و خروج باید به صورت واضح و منطقی تعریف شده باشند. از شرط‌های پیچیده و مبهم خودداری کنید.</li>
            </ul>
            <p className="text-yellow-300 text-xs mt-3 p-2 bg-yellow-900/30 rounded border border-yellow-700/50">
              💡 <strong>نکته مهم:</strong> هرچه استراتژی شما کامل‌تر و واضح‌تر باشد، هوش مصنوعی می‌تواند آن را بهتر پردازش کند و در نتیجه بک‌تست‌های دقیق‌تر و بازدهی بالاتری دریافت خواهید کرد.
            </p>
          </div>
        </div>
      </div>

      {strategies.length === 0 ? (
        <p className="text-gray-400">هنوز استراتژی ثبت نشده است. برای افزودن، روی دکمه زیر کلیک کنید.</p>
      ) : (
        <div className="space-y-3">
          {strategies.map((strategy) => {
            const isDetailsExpanded = expandedDetailsStrategyIds.has(strategy.id)
            
            return (
              <div key={strategy.id} className="bg-gray-700 rounded-lg overflow-hidden">
                {/* Header Section - Always Visible */}
                <div className="p-4">
                  {/* Improvement Recommendations Alert */}
                  {strategiesWithRecommendations.has(strategy.id) && (
                    <div className="mb-4 p-4 bg-yellow-900/30 border border-yellow-700 rounded-lg">
                      <div className="flex items-start gap-3">
                        <span className="text-yellow-400 text-2xl">⚠️</span>
                        <div className="flex-1">
                          <h4 className="text-yellow-200 font-semibold mb-1">هشدار: توصیه‌های بهبود موجود است</h4>
                          <p className="text-yellow-100 text-sm mb-3">
                            نتایج بک‌تست اخیر شما شامل توصیه‌هایی برای بهبود استراتژی است. برای مشاهده جزئیات به بخش نتایج بروید و برای اعمال تغییرات، استراتژی خود را دوباره پردازش کنید.
                          </p>
                          <button
                            onClick={() => {
                              window.location.href = '/results'
                            }}
                            className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm font-medium transition"
                          >
                            مشاهده نتایج و توصیه‌ها
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Backtest Capability Warning */}
                  {strategy.processing_status === 'processed' && strategy.has_backtest_capability === false && (
                    <div className="mb-4 p-4 bg-red-900/30 border border-red-700 rounded-lg">
                      <div className="flex items-start gap-3">
                        <span className="text-red-400 text-2xl">⚠️</span>
                        <div className="flex-1">
                          <h4 className="text-red-200 font-semibold mb-1">قابلیت بک تست ندارد</h4>
                          <p className="text-red-100 text-sm">
                            خروجی بک تست این استراتژی صفر است. استراتژی خود را کامل یا حذف کنید.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between gap-3 flex-wrap mb-3">
                    {/* Strategy Name and Status */}
                    <div className="flex items-center gap-3 flex-wrap flex-1">
                      <button
                        onClick={() => {
                          setExpandedDetailsStrategyIds(prev => {
                            const newSet = new Set(prev)
                            if (newSet.has(strategy.id)) {
                              newSet.delete(strategy.id)
                            } else {
                              newSet.add(strategy.id)
                            }
                            return newSet
                          })
                        }}
                        className="flex items-center gap-2 text-white hover:text-blue-300 transition-colors"
                      >
                        <svg 
                          className={`w-5 h-5 transition-transform duration-200 ${isDetailsExpanded ? 'rotate-90' : ''}`} 
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        <h3 className="text-white font-medium text-lg flex items-center gap-2">
                          {strategy.name}
                          {strategy.is_primary && (
                            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-600 text-white text-xs font-semibold">
                              <svg
                                className="w-4 h-4"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                              >
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.069-3.292z" />
                              </svg>
                              استراتژی اصلی
                            </span>
                          )}
                        </h3>
                      </button>
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
                    
                    {/* Action Buttons */}
                    <div className="flex gap-2 flex-wrap">
                      <button
                        onClick={() => handleSetPrimary(strategy.id, strategy.name)}
                        disabled={strategy.is_primary}
                        className={`px-3 py-1.5 rounded-lg transition text-xs font-medium ${
                          strategy.is_primary
                            ? 'bg-blue-800 text-blue-200 cursor-default'
                            : 'bg-blue-600 hover:bg-blue-700 text-white'
                        }`}
                      >
                        {strategy.is_primary ? 'استراتژی اصلی' : 'انتخاب به‌عنوان اصلی'}
                      </button>
                      {/* دکمه پردازش استراتژی با هوش مصنوعی */}
                      <button
                        onClick={() => handleOpenGapGPTModal(strategy)}
                        className="px-3 py-1.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg transition text-xs font-medium flex items-center gap-1"
                        title="پردازش استراتژی با هوش مصنوعی - محتوای فایل به طور خودکار بارگذاری می‌شود"
                      >
                        <span>🔮</span>
                        <span>پردازش استراتژی با هوش مصنوعی</span>
                      </button>
                      {strategy.processing_status === 'processing' && processingStrategies.has(strategy.id) && (
                        <div className="w-full mt-2">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-gray-400">
                              {processingStrategies.get(strategy.id)?.stage || 'در حال پردازش...'}
                            </span>
                            <span className="text-xs text-gray-400">
                              {processingStrategies.get(strategy.id)?.progress || 0}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${processingStrategies.get(strategy.id)?.progress || 0}%` }}
                            ></div>
                          </div>
                          {processingStrategies.get(strategy.id)?.message && (
                            <p className="text-xs text-gray-500 mt-1">
                              {processingStrategies.get(strategy.id)?.message}
                            </p>
                          )}
                        </div>
                      )}
                      <button
                        onClick={() => toggleStrategy(strategy.id)}
                        className={`px-3 py-1.5 rounded-lg transition text-xs font-medium ${
                          strategy.is_active
                            ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
                            : 'bg-green-600 hover:bg-green-700 text-white'
                        }`}
                      >
                        {strategy.is_active ? 'غیرفعال' : 'فعال'}
                      </button>
                      <a
                        href="/testing"
                        className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-xs font-medium inline-block"
                      >
                        تست
                      </a>
                      {strategy.strategy_file && (
                        <button
                          onClick={() => handleDownload(strategy.id, strategy.name)}
                          className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg transition text-xs font-medium flex items-center gap-1"
                          title="دانلود فایل استراتژی"
                        >
                          <span>⬇️</span>
                          <span>دانلود</span>
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(strategy.id, strategy.name)}
                        className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg transition text-xs font-medium"
                      >
                        حذف
                      </button>
                    </div>
                  </div>
                  
                  {/* Brief Info - Always Visible */}
                  <div className="text-gray-400 text-xs space-y-1">
                    <div>تاریخ ثبت: {new Date(strategy.uploaded_at).toLocaleDateString('fa-IR')}</div>
                    {strategy.processed_at && (
                      <div>تاریخ پردازش: {new Date(strategy.processed_at).toLocaleDateString('fa-IR')}</div>
                    )}
                  </div>
                </div>

                {/* Collapsible Details Section */}
                {isDetailsExpanded && (
                  <div className="border-t border-gray-600 p-4 space-y-4">
                    {/* Description */}
                    {strategy.description && (
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <h4 className="text-white font-semibold text-sm mb-2">توضیحات استراتژی</h4>
                        <p className="text-gray-300 text-sm leading-relaxed">{strategy.description}</p>
                      </div>
                    )}
                    
                    {/* Error Display */}
                    {strategy.processing_error && (
                      <div className="bg-red-900/30 border border-red-700 rounded-lg p-3">
                        <div className="text-red-400 text-sm font-semibold mb-1">خطا در پردازش:</div>
                        <div className="text-red-300 text-xs">{strategy.processing_error}</div>
                      </div>
                    )}
                    
                    {/* Strategy Data and Analysis Section */}
                    {strategy.processing_status === 'processed' && strategy.parsed_strategy_data && (
                <>
                  <div className="bg-green-900/20 border border-green-700 rounded-lg p-3 mb-3">
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-green-400 text-lg">✓</span>
                        <span className="text-green-400 font-semibold">نتیجه پردازش:</span>
                      </div>
                      {/* دکمه پردازش با هوش مصنوعی در بخش Details */}
                      <button
                        onClick={() => handleOpenGapGPTModal(strategy)}
                        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg transition text-sm font-semibold flex items-center gap-2"
                        title="تبدیل استراتژی با مدل‌های مختلف GPT - محتوای فایل به طور خودکار بارگذاری می‌شود"
                      >
                        <span>🔮</span>
                        <span>تبدیل با GPT</span>
                      </button>
                    </div>
                    <div className="text-gray-300 text-xs space-y-1">
                      <div>اعتماد: <span className="text-yellow-400 font-medium">{(strategy.parsed_strategy_data.confidence_score * 100).toFixed(0)}%</span></div>
                      <div>نماد: <span className="text-blue-400">{strategy.parsed_strategy_data.symbol || 'تعیین نشده'}</span></div>
                      <div>تایم‌فریم: <span className="text-blue-400">{strategy.parsed_strategy_data.timeframe || 'تعیین نشده'}</span></div>
                      {strategy.processed_at && (
                        <div className="text-gray-500 text-xs mt-2 pt-2 border-t border-gray-700">
                          تاریخ پردازش: {new Date(strategy.processed_at).toLocaleDateString('fa-IR', { 
                            year: 'numeric', 
                            month: 'long', 
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      )}
                    </div>
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
                          
                          {/* نمایش منبع پردازش */}
                          {strategy.analysis_sources_display && Object.keys(strategy.analysis_sources_display).length > 0 && (
                            <div className="mb-4 p-3 bg-gray-800/50 rounded-lg border-r-4 border-blue-500">
                              <h5 className="text-blue-300 font-semibold mb-2 text-sm flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                منبع پردازش
                              </h5>
                              <div className="space-y-2 text-xs text-gray-300">
                                {strategy.analysis_sources_display.analysis_method_display && (
                                  <div className="flex items-center gap-2">
                                    <span className="text-gray-400">روش تحلیل:</span>
                                    <span className="text-white font-medium">{strategy.analysis_sources_display.analysis_method_display}</span>
                                  </div>
                                )}
                                {strategy.analysis_sources_display.ai_model_display && (
                                  <div className="flex items-center gap-2">
                                    <span className="text-gray-400">مدل هوش مصنوعی:</span>
                                    <span className="text-white font-medium">{strategy.analysis_sources_display.ai_model_display}</span>
                                  </div>
                                )}
                                {strategy.analysis_sources_display.ai_status_display && (
                                  <div className="flex items-center gap-2">
                                    <span className="text-gray-400">وضعیت هوش مصنوعی:</span>
                                    <span className="text-white font-medium">
                                      {strategy.analysis_sources_display.ai_status_display}
                                    </span>
                                  </div>
                                )}
                                {strategy.analysis_sources_display.processing_duration_display && (
                                  <div className="flex items-center gap-2">
                                    <span className="text-gray-400">مدت زمان پردازش:</span>
                                    <span className="text-white font-medium">
                                      {strategy.analysis_sources_display.processing_duration_display}
                                    </span>
                                  </div>
                                )}
                                {(strategy.analysis_sources_display.processing_completed_at_display ||
                                  strategy.analysis_sources_display.processing_completed_at) && (
                                  <div className="flex items-center gap-2">
                                    <span className="text-gray-400">زمان اتمام:</span>
                                    <span className="text-white font-medium">
                                      {strategy.analysis_sources_display.processing_completed_at_display ||
                                        (strategy.analysis_sources_display.processing_completed_at
                                          ? new Date(
                                              strategy.analysis_sources_display.processing_completed_at
                                            ).toLocaleString('fa-IR')
                                          : '')}
                                    </span>
                                  </div>
                                )}
                                {strategy.analysis_sources_display.ai_fallback_reason_display && (
                                  <div className="flex items-start gap-2">
                                    <span className="text-gray-400">دلیل تحلیل پایه:</span>
                                    <span className="text-white text-sm leading-relaxed">
                                      {strategy.analysis_sources_display.ai_fallback_reason_display}
                                    </span>
                                  </div>
                                )}
                                {strategy.analysis_sources_display.ai_message_display &&
                                  !strategy.analysis_sources_display.ai_fallback_reason_display && (
                                    <div className="flex items-start gap-2">
                                      <span className="text-gray-400">پیام سیستم:</span>
                                      <span className="text-white text-sm leading-relaxed">
                                        {strategy.analysis_sources_display.ai_message_display}
                                      </span>
                                    </div>
                                  )}
                                {strategy.analysis_sources_display.ai_attempts_display &&
                                  strategy.analysis_sources_display.ai_attempts_display.length > 0 && (
                                    <div className="mt-2 p-2 bg-gray-900/40 rounded border border-gray-600">
                                      <div className="text-gray-300 text-xs font-semibold mb-2">
                                        تلاش‌های ارائه‌دهندگان هوش مصنوعی:
                                      </div>
                                      <ul className="space-y-1 text-xs text-gray-400">
                                        {strategy.analysis_sources_display.ai_attempts_display.map(
                                          (attempt: any, idx: number) => (
                                            <li key={idx} className="flex flex-col sm:flex-row sm:items-center sm:gap-2">
                                              <span className="text-gray-200">{attempt.provider || 'نامشخص'}</span>
                                              <span>
                                                {attempt.success ? '✅ موفق' : '❌ ناموفق'}
                                                {attempt.error ? ` - ${attempt.error}` : ''}
                                                {attempt.status_code ? ` (کد: ${attempt.status_code})` : ''}
                                              </span>
                                              {attempt.latency_ms ? (
                                                <span className="text-gray-500">
                                                  زمان پاسخ: {attempt.latency_ms.toFixed(0)}ms
                                                </span>
                                              ) : null}
                                            </li>
                                          )
                                        )}
                                      </ul>
                                    </div>
                                  )}
                                {strategy.analysis_sources_display.nlp_parser_display && (
                                  <div className="flex items-center gap-2">
                                    <span className="text-gray-400">Parser:</span>
                                    <span className="text-white font-medium">{strategy.analysis_sources_display.nlp_parser_display}</span>
                                  </div>
                                )}
                                {strategy.analysis_sources_display.data_sources && (
                                  <div className="mt-2 pt-2 border-t border-gray-600">
                                    <div className="text-gray-400 mb-1">اطلاعات استراتژی:</div>
                                    {strategy.analysis_sources_display.data_sources.strategy_symbol && (
                                      <div className="flex items-center gap-2 mr-2">
                                        <span className="text-gray-400">نماد:</span>
                                        <span className="text-white">{strategy.analysis_sources_display.data_sources.strategy_symbol}</span>
                                      </div>
                                    )}
                                    {strategy.analysis_sources_display.data_sources.strategy_timeframe && (
                                      <div className="flex items-center gap-2 mr-2">
                                        <span className="text-gray-400">تایم‌فریم:</span>
                                        <span className="text-white">{strategy.analysis_sources_display.data_sources.strategy_timeframe}</span>
                                      </div>
                                    )}
                                    {strategy.analysis_sources_display.data_sources.available_providers_display && 
                                     strategy.analysis_sources_display.data_sources.available_providers_display.length > 0 && (
                                      <div className="flex items-center gap-2 mr-2">
                                        <span className="text-gray-400">ارائه‌دهندگان در دسترس:</span>
                                        <span className="text-white">
                                          {strategy.analysis_sources_display.data_sources.available_providers_display.join('، ')}
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
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
                            
                            {/* پیام راهنمایی برای تحلیل پایه - فقط اگر کلید AI موجود نباشد */}
                            {strategy.parsed_strategy_data.analysis.is_basic && !hasAIProvider && (
                              <div className="mt-3 p-3 bg-blue-900/30 rounded-lg border border-blue-700">
                                <p className="text-blue-300 text-xs mb-2">
                                  💡 نکته: این تحلیل پایه است که بر اساس داده‌های استخراج شده از استراتژی تولید شده است.
                                </p>
                                <p className="text-blue-200 text-xs">
                                برای دریافت تحلیل پیشرفته با هوش مصنوعی:
                                  <br />
                                  <br />
                                1. یک کلید API فعال دریافت کنید
                                  <br />
                                  <br />
                                  2. در داشبورد، به بخش "تنظیمات API" بروید
                                  <br />
                                  <br />
                                  3. روی دکمه "افزودن کلید API" کلیک کنید
                                  <br />
                                  <br />
                                4. ارائه‌دهنده مورد نظر را انتخاب کنید
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
                          {/* پیام راهنمایی - فقط اگر کلید AI موجود نباشد */}
                          {!hasAIProvider && (
                            <div className="mt-3 p-3 bg-blue-900/30 rounded-lg border border-blue-700">
                              <p className="text-blue-300 text-xs mb-2">
                                💡 نکته: این تحلیل پایه است که بر اساس داده‌های استخراج شده از استراتژی تولید شده است.
                              </p>
                              <p className="text-blue-200 text-xs">
                                برای دریافت تحلیل پیشرفته با هوش مصنوعی:
                                <br />
                                <br />
                                1. از GapGPT (حساب کاربری در <code>gapgpt.app</code>) یک کلید API فعال دریافت کنید
                                <br />
                                <br />
                                2. در داشبورد، به بخش "تنظیمات API" بروید
                                <br />
                                <br />
                                3. روی دکمه "افزودن کلید API" کلیک کنید
                                <br />
                                <br />
                                4. ارائه‌دهنده را "GapGPT" انتخاب کنید
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
                    
                    {/* Strategy Questions Section */}
                    {strategy.processing_status === 'processed' && (
                      <div className="mt-4">
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
                          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition text-sm font-medium mb-4"
                        >
                          {collapsedQuestionsStrategyIds.has(strategy.id) ? '💬 نمایش سوالات تعاملی' : '🔽 بستن سوالات تعاملی'}
                        </button>
                        
                        {!collapsedQuestionsStrategyIds.has(strategy.id) && (
                          <div className="space-y-4">
                            <div className="p-4 bg-gray-800 rounded-lg border border-gray-600">
                              <StrategyQuestions 
                                strategyId={strategy.id}
                                onComplete={() => {
                                  loadStrategies()
                                }}
                              />
                            </div>
                            
                            {/* AI Recommendations Section */}
                            <div className="p-4 bg-gray-800 rounded-lg border border-gray-600">
                              <AIRecommendations 
                                strategyId={strategy.id}
                                strategyName={strategy.name}
                              />
                            </div>
                            
                            {/* Strategy Optimizer Section */}
                            <div className="p-4 bg-gray-800 rounded-lg border border-gray-600">
                              <StrategyOptimizer 
                                strategyId={strategy.id}
                                strategyName={strategy.name}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="text-xl font-semibold text-white mb-4">افزودن استراتژی جدید</h3>
            <form onSubmit={handleSubmit} noValidate>
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
              
              {/* انتخاب روش ورود استراتژی */}
              <div className="mb-4">
                <label className="label-standard mb-2 block">روش ورود استراتژی</label>
                <div className="flex gap-4 mb-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="inputMode"
                      value="file"
                      checked={inputMode === 'file'}
                      onChange={() => {
                        setInputMode('file')
                        setStrategyText('')
                      }}
                      className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500"
                    />
                    <span className="text-white">آپلود فایل</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="inputMode"
                      value="text"
                      checked={inputMode === 'text'}
                      onChange={() => {
                        setInputMode('text')
                        setFile(null)
                        // Clear file input value when switching to text mode
                        if (fileInputRef.current) {
                          fileInputRef.current.value = ''
                        }
                      }}
                      className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 focus:ring-blue-500"
                    />
                    <span className="text-white">تایپ یا پیست متن</span>
                  </label>
                </div>
                
                <div>
                  <label className="label-standard">فایل استراتژی</label>
                  <input
                    ref={fileInputRef}
                    type="file"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    accept=".txt,.md,.pdf,.doc,.docx"
                    disabled={inputMode === 'text'}
                    className={`w-full px-4 py-2.5 bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 file:cursor-pointer ${
                      inputMode === 'text' 
                        ? 'opacity-50 cursor-not-allowed file:cursor-not-allowed file:bg-gray-600 file:hover:bg-gray-600' 
                        : ''
                    }`}
                    required={inputMode === 'file'}
                    key="file-input"
                  />
                  <p className="text-gray-400 text-xs mt-2">فایل‌های مجاز: .txt, .md, .pdf, .doc, .docx</p>
                </div>
                
                {inputMode === 'text' && (
                  <div>
                    <label className="label-standard">متن استراتژی</label>
                    <textarea
                      value={strategyText}
                      onChange={(e) => setStrategyText(e.target.value)}
                      className="textarea-standard"
                      rows={12}
                      placeholder="متن استراتژی خود را اینجا تایپ کنید یا پیست کنید..."
                      required={inputMode === 'text'}
                      key="text-input"
                    />
                    <p className="text-gray-400 text-xs mt-2">متن استراتژی خود را مستقیماً اینجا وارد کنید</p>
                  </div>
                )}
              </div>
              
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="flex-1 btn-success"
                >
                  {inputMode === 'file' ? 'آپلود' : 'ثبت'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false)
                    setName('')
                    setDescription('')
                    setFile(null)
                    setStrategyText('')
                    setInputMode('file')
                  }}
                  className="flex-1 btn-secondary"
                >
                  انصراف
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* AI Processing Modal */}
      {showGapGPTModal && selectedStrategyForGapGPT && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" style={{ direction: 'rtl' }}>
          <div className="bg-gray-800 rounded-lg max-w-5xl w-full max-h-[90vh] overflow-y-auto">
            {loadingFileContent ? (
              <div className="p-6 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
                <p className="text-white">در حال بارگذاری محتوای فایل استراتژی...</p>
              </div>
            ) : (
              <GapGPTConverter
                strategyText={gapGPTFileContent}
                strategyId={selectedStrategyForGapGPT.id}
                onConverted={(converted) => {
                  console.log('Converted strategy from GapGPT:', converted)
                  showToast('استراتژی با موفقیت تبدیل شد! می‌توانید آن را ذخیره کنید.', { type: 'success' })
                }}
                onSave={() => {
                  // Reload strategies after save
                  loadStrategies()
                  showToast('استراتژی تبدیل شده با موفقیت ذخیره شد! اکنون می‌توانید از آن در بک تست‌ها استفاده کنید.', { type: 'success' })
                  setShowGapGPTModal(false)
                  setSelectedStrategyForGapGPT(null)
                  setGapGPTFileContent('')
                }}
                onClose={() => {
                  setShowGapGPTModal(false)
                  setSelectedStrategyForGapGPT(null)
                  setGapGPTFileContent('')
                }}
              />
            )}
          </div>
        </div>
      )}
    </div>
  )
}
