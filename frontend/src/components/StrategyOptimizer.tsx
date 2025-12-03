import { useState, useEffect } from 'react'
import {
  getStrategyOptimizations,
  createStrategyOptimization,
  getOptimizationStatus,
  updateStrategyOptimization,
  deleteStrategyOptimization,
  cancelStrategyOptimization,
  StrategyOptimization,
  OptimizationCreateRequest
} from '../api/client'
import { useToast } from './ToastProvider'
// import SymbolSelector from './SymbolSelector' // Not used, replaced with select element

interface StrategyOptimizerProps {
  strategyId: number
  strategyName?: string
}

export default function StrategyOptimizer({ strategyId, strategyName }: StrategyOptimizerProps) {
  const [optimizations, setOptimizations] = useState<StrategyOptimization[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [cancellingId, setCancellingId] = useState<number | null>(null)
  const { showToast } = useToast()

  // Form state
  const [method, setMethod] = useState<'ml' | 'dl' | 'hybrid' | 'auto'>('auto')
  const [optimizerType, setOptimizerType] = useState<'ml' | 'dl'>('ml')
  const [objective, setObjective] = useState<'sharpe_ratio' | 'total_return' | 'win_rate' | 'profit_factor' | 'combined'>('sharpe_ratio')
  const [nTrials, setNTrials] = useState(50)
  const [nEpisodes, setNEpisodes] = useState(50)
  const [mlMethod, setMlMethod] = useState<'bayesian' | 'random_search' | 'grid_search'>('bayesian')
  const [dlMethod, setDlMethod] = useState<'reinforcement_learning' | 'neural_evolution' | 'gan'>('reinforcement_learning')
  const [timeframeDays, setTimeframeDays] = useState(365)
  const [symbol, setSymbol] = useState('EURUSD')

  // Polling state for running optimizations
  const [pollingOptimizations, setPollingOptimizations] = useState<Set<number>>(new Set())
  // Store progress for each optimization
  const [optimizationProgress, setOptimizationProgress] = useState<Record<number, number>>({})

  useEffect(() => {
    loadOptimizations()
  }, [strategyId])

  // Poll for running optimizations
  useEffect(() => {
    if (pollingOptimizations.size === 0) return

    const interval = setInterval(() => {
      pollingOptimizations.forEach(async (id) => {
        try {
          const response = await getOptimizationStatus(id)
          const status = response.data

          // Update progress
          setOptimizationProgress(prev => ({
            ...prev,
            [id]: status.progress
          }))

          // Update optimization status and scores
          setOptimizations(prev => prev.map(opt => 
            opt.id === id
              ? { ...opt, status: status.status as any, best_score: status.best_score, improvement_percent: status.improvement_percent }
              : opt
          ))

          // Stop polling if completed or failed
          if (status.status === 'completed' || status.status === 'failed') {
            setPollingOptimizations(prev => {
              const next = new Set(prev)
              next.delete(id)
              return next
            })
            // Clear progress
            setOptimizationProgress(prev => {
              const next = { ...prev }
              delete next[id]
              return next
            })
            loadOptimizations() // Refresh to get full data
          }
        } catch (error) {
          console.error(`Error polling optimization ${id}:`, error)
        }
      })
    }, 3000) // Poll every 3 seconds

    return () => clearInterval(interval)
  }, [pollingOptimizations])

  const loadOptimizations = async () => {
    try {
      setLoading(true)
      const response = await getStrategyOptimizations(strategyId)
      let optimizationsData: StrategyOptimization[] = []
      
      if (Array.isArray(response.data)) {
        optimizationsData = response.data
      } else if (response.data && 'results' in response.data && Array.isArray((response.data as any).results)) {
        optimizationsData = (response.data as any).results
      } else if (response.data && 'data' in response.data && Array.isArray((response.data as any).data)) {
        optimizationsData = (response.data as any).data
      }

      setOptimizations(optimizationsData)

      // Start polling for running optimizations
      const runningIds = optimizationsData
        .filter(opt => opt.status === 'running')
        .map(opt => opt.id)
      if (runningIds.length > 0) {
        setPollingOptimizations(new Set(runningIds))
        // Initialize progress for running optimizations
        const progressMap: Record<number, number> = {}
        optimizationsData.forEach(opt => {
          if (opt.status === 'running') {
            const settings = opt.optimization_settings || {}
            const nTrials = settings.n_trials || settings.n_episodes || 50
            const historyLen = opt.optimization_history?.length || 0
            if (nTrials > 0) {
              progressMap[opt.id] = Math.min(100, Math.round((historyLen / nTrials) * 100))
            } else {
              progressMap[opt.id] = 0
            }
          }
        })
        setOptimizationProgress(prev => ({ ...prev, ...progressMap }))
      }
    } catch (error: any) {
      console.error('Error loading optimizations:', error)
      showToast('خطا در بارگذاری بهینه‌سازی‌ها', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleCreateOptimization = async () => {
    try {
      setCreating(true)

      const request: OptimizationCreateRequest = {
        strategy: strategyId,
        method,
        optimizer_type: optimizerType,
        objective,
        n_trials: method === 'ml' || method === 'hybrid' || method === 'auto' ? nTrials : undefined,
        n_episodes: method === 'dl' || method === 'hybrid' || method === 'auto' ? nEpisodes : undefined,
        ml_method: mlMethod,
        dl_method: dlMethod,
        timeframe_days: timeframeDays,
        symbol: symbol || undefined
      }

      if (editingId) {
        // Update existing optimization
        await updateStrategyOptimization(editingId, request)
        showToast('بهینه‌سازی با موفقیت ویرایش شد!', { type: 'success' })
        setEditingId(null)
      } else {
        // Create new optimization
        const response = await createStrategyOptimization(request)
        showToast('بهینه‌سازی با موفقیت شروع شد!', { type: 'success' })
        
        // Add to list and start polling
        setOptimizations(prev => [response.data, ...prev])
        setPollingOptimizations(prev => new Set([...prev, response.data.id]))
        // Initialize progress to 0
        setOptimizationProgress(prev => ({
          ...prev,
          [response.data.id]: 0
        }))
      }
      
      setShowForm(false)
      await loadOptimizations()
      
      // Reset form
      resetForm()
    } catch (error: any) {
      console.error('Error creating/updating optimization:', error)
      showToast(
        error.response?.data?.error || (editingId ? 'خطا در ویرایش بهینه‌سازی' : 'خطا در ایجاد بهینه‌سازی'),
        { type: 'error' }
      )
    } finally {
      setCreating(false)
    }
  }

  const handleEdit = (optimization: StrategyOptimization) => {
    if (optimization.status !== 'pending' && optimization.status !== 'failed') {
      showToast('فقط بهینه‌سازی‌های در انتظار یا خطا خورده قابل ویرایش هستند', { type: 'error' })
      return
    }
    
    setEditingId(optimization.id)
    setMethod(optimization.method)
    setOptimizerType(optimization.optimizer_type)
    setObjective(optimization.objective)
    setNTrials(optimization.optimization_settings?.n_trials || 50)
    setNEpisodes(optimization.optimization_settings?.n_episodes || 50)
    setMlMethod(optimization.optimization_settings?.ml_method || 'bayesian')
    setDlMethod(optimization.optimization_settings?.dl_method || 'reinforcement_learning')
    setTimeframeDays(optimization.optimization_settings?.timeframe_days || 365)
    setSymbol(optimization.optimization_settings?.symbol || 'EURUSD')
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('آیا از حذف این بهینه‌سازی اطمینان دارید؟')) {
      return
    }
    
    try {
      setDeletingId(id)
      await deleteStrategyOptimization(id)
      showToast('بهینه‌سازی با موفقیت حذف شد', { type: 'success' })
      await loadOptimizations()
    } catch (error: any) {
      showToast(error.response?.data?.error || 'خطا در حذف بهینه‌سازی', { type: 'error' })
    } finally {
      setDeletingId(null)
    }
  }

  const handleCancel = async (id: number) => {
    if (!confirm('آیا از لغو این بهینه‌سازی اطمینان دارید؟')) {
      return
    }
    
    try {
      setCancellingId(id)
      await cancelStrategyOptimization(id)
      showToast('بهینه‌سازی با موفقیت لغو شد', { type: 'success' })
      // Stop polling for this optimization
      setPollingOptimizations(prev => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
      await loadOptimizations()
    } catch (error: any) {
      showToast(error.response?.data?.error || 'خطا در لغو بهینه‌سازی', { type: 'error' })
    } finally {
      setCancellingId(null)
    }
  }

  const resetForm = () => {
    setEditingId(null)
    setMethod('auto')
    setOptimizerType('ml')
    setObjective('sharpe_ratio')
    setNTrials(50)
    setNEpisodes(50)
    setMlMethod('bayesian')
    setDlMethod('reinforcement_learning')
    setTimeframeDays(365)
    setSymbol('EURUSD')
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200', text: 'در انتظار' },
      running: { color: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200', text: 'در حال اجرا' },
      completed: { color: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200', text: 'تکمیل شده' },
      failed: { color: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200', text: 'خطا' },
      cancelled: { color: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200', text: 'لغو شده' }
    }
    const statusInfo = statusMap[status] || statusMap.pending
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${statusInfo.color}`}>
        {statusInfo.text}
      </span>
    )
  }

  const getMethodText = (method: string) => {
    const methodMap: Record<string, string> = {
      ml: 'Machine Learning',
      dl: 'Deep Learning',
      hybrid: 'Hybrid (ML + DL)',
      auto: 'Auto'
    }
    return methodMap[method] || method
  }

  const getObjectiveText = (objective: string) => {
    const objectiveMap: Record<string, string> = {
      sharpe_ratio: 'Sharpe Ratio',
      total_return: 'Total Return',
      win_rate: 'Win Rate',
      profit_factor: 'Profit Factor',
      combined: 'Combined'
    }
    return objectiveMap[objective] || objective
  }

  const calculateProgress = (optimization: StrategyOptimization): number => {
    // If we have progress from polling, use it
    if (optimization.status === 'running' && optimizationProgress[optimization.id] !== undefined) {
      return optimizationProgress[optimization.id]
    }
    
    if (optimization.status === 'completed') return 100
    if (optimization.status === 'failed') return 0
    if (optimization.status === 'running') {
      // Fallback to calculating from history
      const settings = optimization.optimization_settings || {}
      const nTrials = settings.n_trials || settings.n_episodes || 50
      const historyLen = optimization.optimization_history?.length || 0
      if (nTrials > 0) {
        return Math.min(100, Math.round((historyLen / nTrials) * 100))
      }
    }
    return 0
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">بهینه‌سازی استراتژی با ML/DL</h2>
          {strategyName && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">استراتژی: {strategyName}</p>
          )}
        </div>
        <button
          onClick={() => {
            setShowForm(!showForm)
            if (showForm) {
              setEditingId(null)
              resetForm()
            }
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showForm ? '✕ بستن' : '+ ایجاد بهینه‌سازی جدید'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {editingId ? 'ویرایش بهینه‌سازی' : 'تنظیمات بهینه‌سازی'}
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                روش بهینه‌سازی
              </label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="auto">Auto (توصیه می‌شود)</option>
                <option value="ml">Machine Learning</option>
                <option value="dl">Deep Learning</option>
                <option value="hybrid">Hybrid (ML + DL)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                نوع بهینه‌ساز
              </label>
              <select
                value={optimizerType}
                onChange={(e) => setOptimizerType(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-50"
                disabled={method === 'auto'}
              >
                <option value="ml">Machine Learning</option>
                <option value="dl">Deep Learning</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                هدف بهینه‌سازی
              </label>
              <select
                value={objective}
                onChange={(e) => setObjective(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="sharpe_ratio">Sharpe Ratio</option>
                <option value="total_return">Total Return</option>
                <option value="win_rate">Win Rate</option>
                <option value="profit_factor">Profit Factor</option>
                <option value="combined">Combined</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                نماد معاملاتی
              </label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full px-4 py-2 text-sm bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="EURUSD">EURUSD</option>
                <option value="GBPUSD">GBPUSD</option>
                <option value="USDJPY">USDJPY</option>
                <option value="XAUUSD">XAUUSD</option>
                <option value="BTCUSD">BTCUSD</option>
              </select>
            </div>

            {(method === 'ml' || method === 'hybrid' || method === 'auto') && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    تعداد تست‌ها (ML)
                  </label>
                  <input
                    type="number"
                    value={nTrials}
                    onChange={(e) => setNTrials(parseInt(e.target.value) || 50)}
                    min={10}
                    max={500}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    روش ML
                  </label>
                  <select
                    value={mlMethod}
                    onChange={(e) => setMlMethod(e.target.value as any)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="bayesian">Bayesian Optimization</option>
                    <option value="random_search">Random Search</option>
                    <option value="grid_search">Grid Search</option>
                  </select>
                </div>
              </>
            )}

            {(method === 'dl' || method === 'hybrid' || method === 'auto') && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    تعداد Episode (DL)
                  </label>
                  <input
                    type="number"
                    value={nEpisodes}
                    onChange={(e) => setNEpisodes(parseInt(e.target.value) || 50)}
                    min={10}
                    max={500}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    روش DL
                  </label>
                  <select
                    value={dlMethod}
                    onChange={(e) => setDlMethod(e.target.value as any)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="reinforcement_learning">Reinforcement Learning</option>
                    <option value="neural_evolution">Neural Evolution</option>
                    <option value="gan">GAN</option>
                  </select>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                بازه زمانی (روز)
              </label>
              <input
                type="number"
                value={timeframeDays}
                onChange={(e) => setTimeframeDays(parseInt(e.target.value) || 365)}
                min={30}
                max={3650}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          </div>

          <div className="mt-6 flex gap-3">
            <button
              onClick={handleCreateOptimization}
              disabled={creating}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {creating ? (editingId ? 'در حال ویرایش...' : 'در حال ایجاد...') : (editingId ? 'ذخیره تغییرات' : 'شروع بهینه‌سازی')}
            </button>
            <button
              onClick={() => {
                setShowForm(false)
                resetForm()
              }}
              className="px-6 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              انصراف
            </button>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {optimizations.length === 0 ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            هنوز بهینه‌سازی‌ای ایجاد نشده است
          </div>
        ) : (
          optimizations.map((optimization) => {
            const progress = calculateProgress(optimization)
            return (
              <div
                key={optimization.id}
                className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        بهینه‌سازی #{optimization.id}
                      </h3>
                      {getStatusBadge(optimization.status)}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                      <p>روش: {getMethodText(optimization.method)}</p>
                      <p>هدف: {getObjectiveText(optimization.objective)}</p>
                      {optimization.strategy_name && (
                        <p>استراتژی: {optimization.strategy_name}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      {optimization.status === 'running' && (
                        <button
                          onClick={() => handleCancel(optimization.id)}
                          disabled={cancellingId === optimization.id}
                          className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {cancellingId === optimization.id ? 'در حال لغو...' : '⏹️ توقف'}
                        </button>
                      )}
                      
                      {(optimization.status === 'pending' || optimization.status === 'failed') && (
                        <>
                          <button
                            onClick={() => handleEdit(optimization)}
                            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors"
                          >
                            ✏️ ویرایش
                          </button>
                          <button
                            onClick={() => handleDelete(optimization.id)}
                            disabled={deletingId === optimization.id}
                            className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {deletingId === optimization.id ? 'در حال حذف...' : '🗑️ حذف'}
                          </button>
                        </>
                      )}
                      
                      {optimization.status !== 'running' && optimization.status !== 'pending' && 
                       optimization.status !== 'failed' && (
                        <button
                          onClick={() => handleDelete(optimization.id)}
                          disabled={deletingId === optimization.id}
                          className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {deletingId === optimization.id ? 'در حال حذف...' : '🗑️ حذف'}
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {optimization.created_at && (
                        <p>{new Date(optimization.created_at).toLocaleDateString('fa-IR')}</p>
                      )}
                    </div>
                  </div>
                </div>

                {optimization.status === 'running' && (
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-1 text-gray-700 dark:text-gray-300">
                      <span>پیشرفت: {progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {optimization.status === 'completed' && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">امتیاز اولیه</p>
                      <p className="text-lg font-semibold text-gray-900 dark:text-white">
                        {optimization.original_score?.toFixed(2) || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">بهترین امتیاز</p>
                      <p className="text-lg font-semibold text-green-600 dark:text-green-400">
                        {optimization.best_score?.toFixed(2) || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">بهبود</p>
                      <p className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                        {optimization.improvement_percent
                          ? `${optimization.improvement_percent > 0 ? '+' : ''}${optimization.improvement_percent.toFixed(1)}%`
                          : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">تعداد تست‌ها</p>
                      <p className="text-lg font-semibold text-gray-900 dark:text-white">
                        {optimization.optimization_history?.length || 0}
                      </p>
                    </div>
                  </div>
                )}

                {optimization.optimized_params && (
                  <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600">
                    <p className="text-sm font-medium mb-2 text-gray-900 dark:text-white">پارامترهای بهینه شده:</p>
                    <pre className="text-xs overflow-x-auto text-gray-700 dark:text-gray-300">
                      {JSON.stringify(optimization.optimized_params, null, 2)}
                    </pre>
                  </div>
                )}

                {optimization.error_message && (
                  <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/30 rounded border border-red-200 dark:border-red-800">
                    <p className="text-sm text-red-800 dark:text-red-300 font-medium">خطا:</p>
                    <p className="text-xs text-red-600 dark:text-red-400">{optimization.error_message}</p>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

