import { useState, useRef, useEffect, useCallback } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import Strategies from '../components/Strategies'
import Jobs from '../components/Jobs'
import { useToast } from '../components/ToastProvider'
import { useAuth } from '../context/AuthContext'
import { getStrategies, getJobs, getWalletBalance, getResults } from '../api/client'
import { useFeatureFlags } from '../context/FeatureFlagsContext'

function normalizeArrayResponse<T = any>(data: any): T[] {
  if (!data) return []
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.data)) return data.data
  if (Array.isArray(data?.data?.results)) return data.data.results
  if (Array.isArray(data?.results?.data)) return data.results.data
  return []
}

export default function Dashboard() {
  const [showStrategyModal, setShowStrategyModal] = useState(false)
  const [strategyOpen, setStrategyOpen] = useState(true)
  const [jobsOpen, setJobsOpen] = useState(false)
  const [strategyName, setStrategyName] = useState('')
  const [strategyDesc, setStrategyDesc] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [strategyRefreshKey, setStrategyRefreshKey] = useState(0)
  const { showToast } = useToast()
  const { user } = useAuth()
  const { liveTradingEnabled } = useFeatureFlags()
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  
  // Stats state
  const [stats, setStats] = useState({
    walletBalance: 0,
    strategiesCount: 0,
    recentJobsCount: 0,
    activeJobsCount: 0
  })
  const [statsLoading, setStatsLoading] = useState(true)

  const loadStats = useCallback(async () => {
    try {
      setStatsLoading(true)
      const [walletRes, strategiesRes, jobsRes, resultsRes] = await Promise.allSettled([
        getWalletBalance(),
        getStrategies(),
        getJobs(),
        getResults(),
      ])

      const newStats = {
        walletBalance: 0,
        strategiesCount: 0,
        recentJobsCount: 0,
        activeJobsCount: 0
      }

      // Wallet balance
      if (walletRes.status === 'fulfilled') {
        newStats.walletBalance = walletRes.value.data.balance || 0
      }

      // Strategies count
      if (strategiesRes.status === 'fulfilled') {
        const strategiesData = Array.isArray(strategiesRes.value.data) 
          ? strategiesRes.value.data 
          : strategiesRes.value.data?.results || []
        newStats.strategiesCount = strategiesData.length
      }

      // Results count (completed tests)
      if (resultsRes.status === 'fulfilled') {
        const resultsData = normalizeArrayResponse(resultsRes.value.data)
        newStats.recentJobsCount = resultsData.length
      }

      // Jobs count
      if (jobsRes.status === 'fulfilled') {
        const jobsData = Array.isArray(jobsRes.value.data)
          ? jobsRes.value.data
          : jobsRes.value.data?.results || []

        if (newStats.recentJobsCount === 0) {
          const seenResults = new Set<number>()
          for (const job of jobsData) {
            const resultId = job?.result?.id
            if (typeof resultId === 'number' && !seenResults.has(resultId)) {
              seenResults.add(resultId)
            }
          }
          newStats.recentJobsCount = seenResults.size
        }

        newStats.activeJobsCount = jobsData.filter((job: any) => 
          job.status === 'running' || job.status === 'pending'
        ).length
      }

      setStats(newStats)
    } catch (error) {
      console.error('Error loading stats:', error)
    } finally {
      setStatsLoading(false)
    }
  }, [])

  // Load dashboard stats
  useEffect(() => {
    loadStats()
  }, [loadStats])

  // Handle payment callback from Zarinpal
  useEffect(() => {
    const paymentSuccess = searchParams.get('payment_success')
    const paymentError = searchParams.get('payment_error')
    const transactionId = searchParams.get('transaction_id')

    if (paymentSuccess === '1') {
      showToast('پرداخت با موفقیت انجام شد! حساب شما شارژ شد.', { type: 'success', duration: 5000 })
      // Remove query params from URL
      searchParams.delete('payment_success')
      searchParams.delete('transaction_id')
      setSearchParams(searchParams, { replace: true })
      // Refresh strategies to update wallet balance
      setStrategyRefreshKey(prev => prev + 1)
      loadStats() // Refresh stats after payment
    } else if (paymentError) {
      const errorMessages: Record<string, string> = {
        'missing_params': 'پارامترهای پرداخت نامعتبر است',
        'transaction_not_found': 'تراکنش یافت نشد',
        'already_processed': 'این تراکنش قبلاً پردازش شده است',
        'verify_failed': 'تایید پرداخت ناموفق بود',
        'cancelled': 'پرداخت لغو شد'
      }
      const errorMessage = errorMessages[paymentError] || 'خطا در پرداخت'
      const errorDetail = searchParams.get('error')
      showToast(
        errorDetail ? `${errorMessage}: ${errorDetail}` : errorMessage,
        { type: 'error', duration: 5000 }
      )
      // Remove query params from URL
      searchParams.delete('payment_error')
      searchParams.delete('error')
      setSearchParams(searchParams, { replace: true })
    }
  }, [searchParams, setSearchParams, showToast, loadStats])

  const handleStrategySubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!file) {
      showToast('لطفاً فایلی را انتخاب کنید', { type: 'warning' })
      return
    }

    try {
      const formData = new FormData()
      formData.append('name', strategyName)
      formData.append('description', strategyDesc)
      formData.append('strategy_file', file)

      const response = await fetch('http://localhost:8000/api/strategies/', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        showToast('استراتژی با موفقیت آپلود شد!', { type: 'success' })
        setShowStrategyModal(false)
        setStrategyName('')
        setStrategyDesc('')
        setFile(null)
        // Trigger a refresh of the Strategies component
        setStrategyRefreshKey(prev => prev + 1)
      } else {
        const error = await response.text()
        showToast('خطا در آپلود استراتژی: ' + error, { type: 'error' })
      }
    } catch (error: any) {
      console.error('Error uploading strategy:', error)
      showToast('خطا در آپلود استراتژی: ' + error, { type: 'error' })
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
          داشبورد
        </h1>
        <p className="text-gray-400 text-lg">مدیریت استراتژی‌های معاملاتی و نظارت بر عملکرد</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Wallet Balance Card */}
        <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-gray-200 text-sm font-medium">موجودی کیف پول</h3>
            <svg className="w-6 h-6 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          {statsLoading ? (
            <div className="text-white text-xl">...</div>
          ) : (
            <p className="text-white text-2xl font-bold">
              {stats.walletBalance.toLocaleString('fa-IR')} تومان
            </p>
          )}
          <Link 
            to="/profile" 
            className="text-blue-100 text-sm hover:text-white mt-2 inline-block"
          >
            شارژ کیف پول →
          </Link>
        </div>

        {/* Strategies Count Card */}
        <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-gray-200 text-sm font-medium">استراتژی‌ها</h3>
            <svg className="w-6 h-6 text-green-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          {statsLoading ? (
            <div className="text-white text-xl">...</div>
          ) : (
            <p className="text-white text-2xl font-bold">{stats.strategiesCount}</p>
          )}
          <p className="text-green-100 text-sm mt-2">استراتژی فعال</p>
        </div>

        {/* Recent Jobs Card */}
        <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-gray-200 text-sm font-medium">تست‌های انجام شده</h3>
            <svg className="w-6 h-6 text-purple-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          {statsLoading ? (
            <div className="text-white text-xl">...</div>
          ) : (
            <p className="text-white text-2xl font-bold">{stats.recentJobsCount}</p>
          )}
          <Link 
            to="/results" 
            className="text-purple-100 text-sm hover:text-white mt-2 inline-block"
          >
            مشاهده نتایج →
          </Link>
        </div>

        {/* Active Jobs Card */}
        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-gray-200 text-sm font-medium">تست‌های در حال اجرا</h3>
            <svg className="w-6 h-6 text-yellow-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          {statsLoading ? (
            <div className="text-white text-xl">...</div>
          ) : (
            <p className="text-white text-2xl font-bold">{stats.activeJobsCount}</p>
          )}
          <p className="text-yellow-100 text-sm mt-2">در حال پردازش</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">دسترسی سریع</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link
              to="/testing"
              className="flex flex-col items-center justify-center p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              <svg className="w-8 h-8 text-blue-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              <span className="text-white text-sm font-medium">تست استراتژی</span>
            </Link>
            <Link
              to="/results"
              className="flex flex-col items-center justify-center p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              <svg className="w-8 h-8 text-green-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span className="text-white text-sm font-medium">نتایج تست</span>
            </Link>
            <Link
              to="/tickets"
              className="flex flex-col items-center justify-center p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              <svg className="w-8 h-8 text-indigo-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" strokeWidth={2} />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01" />
              </svg>
              <span className="text-white text-sm font-medium">تیکت پشتیبانی</span>
            </Link>
            <Link
              to="/profile"
              className="flex flex-col items-center justify-center p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              <svg className="w-8 h-8 text-purple-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span className="text-white text-sm font-medium">پروفایل</span>
            </Link>
            {liveTradingEnabled && (
              <Link
                to="/trading"
                className="flex flex-col items-center justify-center p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                <svg className="w-8 h-8 text-yellow-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span className="text-white text-sm font-medium">معاملات زنده</span>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/** استراتژی‌های معاملاتی */}
      <div className="mb-6">
        <div className="bg-gray-800 rounded-lg p-0">
          <button onClick={()=>setStrategyOpen(s=>!s)} className="w-full px-4 py-3 flex justify-between items-center text-white text-xl font-semibold focus:outline-none border-b border-gray-700">
            <span>استراتژی‌های معاملاتی</span>
            <svg className={`w-5 h-5 transition-transform duration-300 ${strategyOpen ? '' : 'rotate-180'}`} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7"/></svg>
          </button>
          {strategyOpen && <div className="p-4 pt-2"><Strategies key={strategyRefreshKey} /></div>}
        </div>
      </div>

      {/** تست‌های اخیر - زیر استراتژی‌ها */}
      <div>
        <div className="bg-gray-800 rounded-lg p-0">
          <button onClick={()=>setJobsOpen(s=>!s)} className="w-full px-4 py-3 flex justify-between items-center text-white text-xl font-semibold focus:outline-none border-b border-gray-700">
            <span>تست‌های اخیر</span>
            <svg className={`w-5 h-5 transition-transform duration-300 ${jobsOpen ? '' : 'rotate-180'}`} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7"/></svg>
          </button>
          {jobsOpen && <div className="p-4 pt-2"><Jobs /></div>}
        </div>
      </div>
      {showStrategyModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="text-xl font-semibold text-white mb-4">آپلود استراتژی جدید</h3>
            <form onSubmit={handleStrategySubmit}>
              <div className="mb-4">
                <label className="label-standard">نام استراتژی</label>
                <input
                  type="text"
                  value={strategyName}
                  onChange={(e) => setStrategyName(e.target.value)}
                  className="input-standard"
                  placeholder="نام استراتژی شما"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="label-standard">توضیحات</label>
                <textarea
                  value={strategyDesc}
                  onChange={(e) => setStrategyDesc(e.target.value)}
                  className="textarea-standard"
                  rows={4}
                  placeholder="توضیحی درباره استراتژی..."
                  required
                />
              </div>
              <div className="mb-4">
                <label className="label-standard">فایل استراتژی</label>
                <input
                  type="file"
                  accept=".txt,.md,.pdf,.doc,.docx"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
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
                  onClick={() => setShowStrategyModal(false)}
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
