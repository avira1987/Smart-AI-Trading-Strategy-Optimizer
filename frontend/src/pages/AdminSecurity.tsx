import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/ToastProvider'
import {
  getSecurityManagement,
  unblockIP,
  clearRateLimitHistory,
  unblockAllIPs,
  getSecurityLogs,
  checkGapGPTBalance,
  type SecurityManagementData,
  type BlockedIP,
  type RateLimitStat,
  type SecurityLog,
  type GapGPTBalanceResponse,
} from '../api/client'
import Breadcrumbs from '../components/Breadcrumbs'

const AUTO_REFRESH_INTERVAL_MS = 60000

export default function AdminSecurity() {
  const { isAdmin } = useAuth()
  const { showToast } = useToast()
  const [data, setData] = useState<SecurityManagementData | null>(null)
  const [logs, setLogs] = useState<SecurityLog[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'blocked' | 'stats' | 'logs'>('overview')
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [gapgptBalance, setGapgptBalance] = useState<GapGPTBalanceResponse['data'] | null>(null)
  const [loadingBalance, setLoadingBalance] = useState(false)

  const loadData = async () => {
    try {
      setLoading(true)
      const response = await getSecurityManagement()
      setData(response.data)
    } catch (error: any) {
      console.error('Error loading security data:', error)
      showToast('خطا در بارگذاری اطلاعات امنیتی', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const loadLogs = async () => {
    try {
      const response = await getSecurityLogs()
      setLogs(response.data.logs || [])
    } catch (error: any) {
      console.error('Error loading security logs:', error)
    }
  }

  const loadGapGPTBalance = async () => {
    try {
      setLoadingBalance(true)
      const response = await checkGapGPTBalance()
      if (response.data.status === 'success' && response.data.data) {
        setGapgptBalance(response.data.data)
      } else if (response.data.data) {
        setGapgptBalance(response.data.data)
      }
    } catch (error: any) {
      console.error('Error loading GapGPT balance:', error)
      if (error.response?.data?.data) {
        setGapgptBalance(error.response.data.data)
      }
    } finally {
      setLoadingBalance(false)
    }
  }

  useEffect(() => {
    if (!isAdmin) {
      return
    }
    loadData()
    loadGapGPTBalance()
    const interval = setInterval(() => {
      if (typeof document !== 'undefined' && document.hidden) {
        return
      }
      loadData()
      loadGapGPTBalance()
      if (activeTab === 'logs') {
        loadLogs()
      }
    }, AUTO_REFRESH_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [isAdmin, activeTab])

  useEffect(() => {
    if (isAdmin && activeTab === 'logs') {
      loadLogs()
    }
  }, [isAdmin, activeTab])

  if (!isAdmin) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Breadcrumbs />
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-red-400 text-center">
            ⚠️ فقط ادمین می‌تواند به این بخش دسترسی داشته باشد
          </div>
        </div>
      </div>
    )
  }

  const handleUnblockIP = async (ip: string) => {
    try {
      setActionLoading(`unblock-${ip}`)
      const response = await unblockIP(ip)
      if (response.data.success) {
        showToast(response.data.message, { type: 'success' })
        await loadData()
      } else {
        showToast(response.data.message || 'خطا در آزاد کردن IP', { type: 'error' })
      }
    } catch (error: any) {
      showToast(error.response?.data?.message || 'خطا در آزاد کردن IP', { type: 'error' })
    } finally {
      setActionLoading(null)
    }
  }

  const handleUnblockAll = async () => {
    if (!confirm('آیا مطمئن هستید که می‌خواهید همه IP های مسدود شده را آزاد کنید؟')) {
      return
    }
    try {
      setActionLoading('unblock-all')
      const response = await unblockAllIPs()
      if (response.data.success) {
        showToast(response.data.message, { type: 'success' })
        await loadData()
      } else {
        showToast(response.data.message || 'خطا در آزاد کردن IP ها', { type: 'error' })
      }
    } catch (error: any) {
      showToast(error.response?.data?.message || 'خطا در آزاد کردن IP ها', { type: 'error' })
    } finally {
      setActionLoading(null)
    }
  }

  const handleClearHistory = async (ip?: string) => {
    const message = ip
      ? `آیا مطمئن هستید که می‌خواهید تاریخچه Rate Limit برای IP ${ip} را پاک کنید؟`
      : 'آیا مطمئن هستید که می‌خواهید همه تاریخچه‌های Rate Limit را پاک کنید؟'
    
    if (!confirm(message)) {
      return
    }
    
    try {
      setActionLoading(ip ? `clear-${ip}` : 'clear-all')
      const response = await clearRateLimitHistory(ip)
      if (response.data.success) {
        showToast(response.data.message, { type: 'success' })
        await loadData()
      } else {
        showToast(response.data.message || 'خطا در پاک کردن تاریخچه', { type: 'error' })
      }
    } catch (error: any) {
      showToast(error.response?.data?.message || 'خطا در پاک کردن تاریخچه', { type: 'error' })
    } finally {
      setActionLoading(null)
    }
  }

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds} ثانیه`
    if (seconds < 3600) return `${Math.floor(seconds / 60)} دقیقه`
    return `${Math.floor(seconds / 3600)} ساعت`
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return new Intl.DateTimeFormat('fa-IR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date)
    } catch {
      return dateString
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <Breadcrumbs />
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
          مدیریت امنیت و مسائل حساس
        </h1>
        <p className="text-gray-400 text-lg">مدیریت IP های مسدود شده، Rate Limiting و لاگ‌های امنیتی</p>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-700">
          <nav className="-mb-px flex space-x-8 space-x-reverse">
            {[
              { id: 'overview', label: 'نمای کلی', icon: '📊' },
              { id: 'blocked', label: 'IP های مسدود شده', icon: '🚫' },
              { id: 'stats', label: 'آمار Rate Limit', icon: '📈' },
              { id: 'logs', label: 'لاگ‌های امنیتی', icon: '📝' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                  }
                `}
              >
                <span className="ml-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      {loading && !data ? (
        <div className="bg-gray-800 rounded-lg p-12 text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
          <div className="text-white text-xl">در حال بارگذاری...</div>
        </div>
      ) : (
        <>
          {/* Overview Tab */}
          {activeTab === 'overview' && data && (
            <div className="space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-red-600 to-red-700 rounded-xl p-6 shadow-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-gray-200 text-sm font-medium">IP های مسدود شده</h3>
                    <svg className="w-6 h-6 text-red-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                    </svg>
                  </div>
                  <p className="text-white text-3xl font-bold">{data.total_blocked}</p>
                </div>

                <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 shadow-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-gray-200 text-sm font-medium">IP های ردیابی شده</h3>
                    <svg className="w-6 h-6 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <p className="text-white text-3xl font-bold">{data.total_tracked_ips}</p>
                </div>

                <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl p-6 shadow-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-gray-200 text-sm font-medium">Endpoint های محافظت شده</h3>
                    <svg className="w-6 h-6 text-green-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </div>
                  <p className="text-white text-3xl font-bold">{data.rate_limit_config.protected_paths.length}</p>
                </div>

                {/* GapGPT Balance Card */}
                <div className={`rounded-xl p-6 shadow-lg ${
                  gapgptBalance?.is_low_balance 
                    ? 'bg-gradient-to-br from-orange-600 to-red-700' 
                    : typeof gapgptBalance?.balance === 'string' && gapgptBalance.balance === 'کافی'
                    ? 'bg-gradient-to-br from-purple-600 to-purple-700'
                    : 'bg-gradient-to-br from-purple-600 to-purple-700'
                }`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-gray-200 text-sm font-medium">موجودی GapGPT</h3>
                    <button
                      onClick={loadGapGPTBalance}
                      disabled={loadingBalance}
                      className="p-1 hover:bg-white/20 rounded transition disabled:opacity-50"
                      title="بررسی مجدد"
                    >
                      <svg className="w-5 h-5 text-purple-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </div>
                  {loadingBalance ? (
                    <div className="flex items-center gap-2">
                      <div className="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                      <p className="text-white text-sm">در حال بررسی...</p>
                    </div>
                  ) : gapgptBalance ? (
                    <div>
                      <p className={`text-2xl font-bold ${
                        gapgptBalance.is_low_balance ? 'text-red-100' : 'text-white'
                      }`}>
                        {gapgptBalance.balance_formatted}
                      </p>
                      {gapgptBalance.is_low_balance && (
                        <p className="text-red-200 text-xs mt-1">⚠️ موجودی کم</p>
                      )}
                    </div>
                  ) : (
                    <p className="text-white text-sm">نامشخص</p>
                  )}
                </div>
              </div>

              {/* Rate Limit Configuration */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-xl font-bold text-white mb-4">تنظیمات Rate Limit</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-700">
                    <thead>
                      <tr>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Endpoint
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          محدودیت
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          بازه زمانی
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-gray-700 divide-y divide-gray-600">
                      {Object.entries(data.rate_limit_config.limits).map(([path, [maxRequests, windowSeconds]]) => (
                        <tr key={path}>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300 font-mono">
                            {path}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-white">
                            {maxRequests} درخواست
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-white">
                            {windowSeconds} ثانیه
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Blocked IPs Tab */}
          {activeTab === 'blocked' && data && (
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-white">IP های مسدود شده</h3>
                {data.blocked_ips.length > 0 && (
                  <button
                    onClick={handleUnblockAll}
                    disabled={actionLoading === 'unblock-all'}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {actionLoading === 'unblock-all' ? 'در حال پردازش...' : 'آزاد کردن همه'}
                  </button>
                )}
              </div>

              {data.blocked_ips.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="mt-4 text-gray-400">هیچ IP مسدود شده‌ای وجود ندارد</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-700">
                    <thead>
                      <tr>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          IP Address
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          زمان آزاد شدن
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          زمان باقی‌مانده
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          عملیات
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-gray-700 divide-y divide-gray-600">
                      {data.blocked_ips.map((blocked: BlockedIP) => (
                        <tr key={blocked.ip}>
                          <td className="px-4 py-3 whitespace-nowrap text-sm font-mono text-white">
                            {blocked.ip}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                            {formatDate(blocked.blocked_until)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-yellow-400 font-medium">
                            {formatTime(blocked.remaining_seconds)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm">
                            <button
                              onClick={() => handleUnblockIP(blocked.ip)}
                              disabled={actionLoading === `unblock-${blocked.ip}`}
                              className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {actionLoading === `unblock-${blocked.ip}` ? '...' : 'آزاد کردن'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Rate Limit Stats Tab */}
          {activeTab === 'stats' && data && (
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-white">آمار Rate Limit</h3>
                <button
                  onClick={() => handleClearHistory()}
                  disabled={actionLoading === 'clear-all'}
                  className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading === 'clear-all' ? 'در حال پردازش...' : 'پاک کردن همه تاریخچه‌ها'}
                </button>
              </div>

              {Object.keys(data.rate_limit_stats).length === 0 ? (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="mt-4 text-gray-400">هیچ IP ردیابی شده‌ای وجود ندارد</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-700">
                    <thead>
                      <tr>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          IP Address
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          تعداد درخواست‌ها (5 دقیقه گذشته)
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          اولین درخواست
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          آخرین درخواست
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                          عملیات
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-gray-700 divide-y divide-gray-600">
                      {Object.values(data.rate_limit_stats).map((stat: RateLimitStat) => (
                        <tr key={stat.ip}>
                          <td className="px-4 py-3 whitespace-nowrap text-sm font-mono text-white">
                            {stat.ip}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-white">
                            <span className="px-2 py-1 bg-blue-600 rounded">{stat.requests_count}</span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                            {formatDate(stat.first_request)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                            {formatDate(stat.last_request)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm">
                            <button
                              onClick={() => handleClearHistory(stat.ip)}
                              disabled={actionLoading === `clear-${stat.ip}`}
                              className="px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {actionLoading === `clear-${stat.ip}` ? '...' : 'پاک کردن'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Security Logs Tab */}
          {activeTab === 'logs' && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-bold text-white mb-6">لاگ‌های امنیتی اخیر</h3>
              {logs.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="mt-4 text-gray-400">هیچ لاگی وجود ندارد</p>
                  <p className="mt-2 text-sm text-gray-500">برای مشاهده لاگ‌های کامل، فایل logs/api.log را بررسی کنید</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {logs.map((log, index) => (
                    <div
                      key={index}
                      className="bg-gray-700 rounded-lg p-4 border-r-4 border-blue-500"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${
                                log.level === 'ERROR'
                                  ? 'bg-red-600 text-white'
                                  : log.level === 'WARNING'
                                  ? 'bg-yellow-600 text-white'
                                  : 'bg-blue-600 text-white'
                              }`}
                            >
                              {log.level}
                            </span>
                            <span className="text-sm text-gray-400">{formatDate(log.timestamp)}</span>
                          </div>
                          <p className="text-white">{log.message}</p>
                          {log.ip && (
                            <p className="text-sm text-gray-400 mt-1 font-mono">IP: {log.ip}</p>
                          )}
                          {log.path && (
                            <p className="text-sm text-gray-400 mt-1 font-mono">Path: {log.path}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

