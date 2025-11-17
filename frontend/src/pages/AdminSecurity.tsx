import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/ToastProvider'
import { useFeatureFlags } from '../context/FeatureFlagsContext'
import {
  getSecurityManagement,
  unblockIP,
  clearRateLimitHistory,
  unblockAllIPs,
  getSecurityLogs,
  type SecurityManagementData,
  type BlockedIP,
  type RateLimitStat,
  type SecurityLog,
  getSystemSettings,
  updateSystemSettings,
  type SystemSettingsResponse,
} from '../api/client'

export default function AdminSecurity() {
  const { isAdmin } = useAuth()
  const { showToast } = useToast()
  const { reload: reloadFeatureFlags } = useFeatureFlags()
  const [data, setData] = useState<SecurityManagementData | null>(null)
  const [logs, setLogs] = useState<SecurityLog[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'blocked' | 'stats' | 'logs' | 'settings'>('overview')
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [systemSettings, setSystemSettings] = useState<SystemSettingsResponse | null>(null)
  const [settingsLoading, setSettingsLoading] = useState(false)
  const [settingsActionLoading, setSettingsActionLoading] = useState(false)

  useEffect(() => {
    if (isAdmin) {
      loadData()
      loadLogs()
      loadSystemSettings()
      // Auto-refresh every 30 seconds
      const interval = setInterval(() => {
        loadData()
        loadLogs()
      }, 30000)
      return () => clearInterval(interval)
    }
  }, [isAdmin])

  if (!isAdmin) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-red-400 text-center">
            ⚠️ فقط ادمین می‌تواند به این بخش دسترسی داشته باشد
          </div>
        </div>
      </div>
    )
  }

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

  const loadSystemSettings = async () => {
    try {
      setSettingsLoading(true)
      const response = await getSystemSettings()
      setSystemSettings(response.data)
    } catch (error: any) {
      console.error('Error loading system settings:', error)
      showToast('خطا در بارگذاری تنظیمات سیستم', { type: 'error' })
    } finally {
      setSettingsLoading(false)
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

  const handleToggleLiveTrading = async () => {
    if (!systemSettings) {
      return
    }

    try {
      setSettingsActionLoading(true)
      const response = await updateSystemSettings({
        live_trading_enabled: !systemSettings.live_trading_enabled,
      })
      setSystemSettings(response.data)
      await reloadFeatureFlags()
      showToast(
        response.data.live_trading_enabled
          ? 'بخش معاملات زنده برای کاربران فعال شد'
          : 'بخش معاملات زنده برای کاربران مخفی شد',
        { type: 'success' }
      )
    } catch (error: any) {
      const message = error.response?.data?.detail || error.response?.data?.message || 'خطا در به‌روزرسانی تنظیمات'
      showToast(message, { type: 'error' })
    } finally {
      setSettingsActionLoading(false)
    }
  }

  const handleRefreshSettings = async () => {
    await loadSystemSettings()
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
              { id: 'settings', label: 'تنظیمات وب‌سایت', icon: '⚙️' },
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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

          {activeTab === 'settings' && (
            <div className="bg-gray-800 rounded-lg p-6 space-y-6">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h3 className="text-xl font-bold text-white">تنظیمات وب‌سایت</h3>
                  <p className="text-gray-400 text-sm">کنترل نمایش ویژگی‌های حساس برای کاربران سامانه</p>
                </div>
                <button
                  onClick={handleRefreshSettings}
                  disabled={settingsLoading}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {settingsLoading ? 'در حال بارگذاری...' : 'بارگذاری مجدد'}
                </button>
              </div>

              {settingsLoading && !systemSettings ? (
                <div className="bg-gray-900 rounded-lg p-6 text-center">
                  <div className="inline-block animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500 mb-4"></div>
                  <p className="text-gray-300">در حال بارگذاری تنظیمات سیستم...</p>
                </div>
              ) : systemSettings ? (
                <div className="space-y-4">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-gray-900 rounded-lg p-5">
                    <div>
                      <h4 className="text-lg font-semibold text-white">نمایش بخش معاملات زنده</h4>
                      <p className="text-gray-400 text-sm mt-1">
                        با غیرفعال کردن این گزینه، لینک‌ها و صفحه معاملات زنده برای تمامی کاربران پنهان می‌شود.
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          systemSettings.live_trading_enabled
                            ? 'bg-green-900 text-green-300'
                            : 'bg-red-900 text-red-300'
                        }`}
                      >
                        {systemSettings.live_trading_enabled ? 'فعال' : 'غیرفعال'}
                      </span>
                      <button
                        onClick={handleToggleLiveTrading}
                        disabled={settingsActionLoading}
                        className={`px-4 py-2 rounded-lg font-medium text-white transition disabled:opacity-50 disabled:cursor-not-allowed ${
                          systemSettings.live_trading_enabled
                            ? 'bg-red-600 hover:bg-red-700'
                            : 'bg-green-600 hover:bg-green-700'
                        }`}
                      >
                        {settingsActionLoading
                          ? 'در حال اعمال...'
                          : systemSettings.live_trading_enabled
                          ? 'مخفی کردن'
                          : 'فعال کردن'}
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-gray-900 rounded-lg p-6 text-center">
                  <p className="text-gray-300 mb-4">تنظیمات سیستم در دسترس نیست. لطفاً دوباره تلاش کنید.</p>
                  <button
                    onClick={handleRefreshSettings}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                  >
                    تلاش مجدد
                  </button>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

