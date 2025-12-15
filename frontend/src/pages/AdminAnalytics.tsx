import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/ToastProvider'
import {
  getGoogleAnalyticsStats,
  getGoogleAnalyticsPages,
  getDatabaseAnalyticsStats,
  getDatabaseAnalyticsPages,
  getDatabaseAnalyticsUsers,
  type GoogleAnalyticsStats,
  type GoogleAnalyticsPage,
  type DatabaseAnalyticsStats,
  type DatabaseAnalyticsPage,
  type DatabaseAnalyticsUser,
} from '../api/client'
import Breadcrumbs from '../components/Breadcrumbs'

const AUTO_REFRESH_INTERVAL_MS = 60000 // 1 minute

export default function AdminAnalytics() {
  const { isAdmin } = useAuth()
  const { showToast } = useToast()
  
  // State
  const [activeTab, setActiveTab] = useState<'overview' | 'google' | 'database'>('overview')
  const [days, setDays] = useState(7)
  const [loading, setLoading] = useState(false)
  
  // Google Analytics Data
  const [gaStats, setGaStats] = useState<GoogleAnalyticsStats | null>(null)
  const [gaPages, setGaPages] = useState<GoogleAnalyticsPage[]>([])
  const [gaAvailable, setGaAvailable] = useState<boolean | null>(null)
  
  // Database Analytics Data
  const [dbStats, setDbStats] = useState<DatabaseAnalyticsStats | null>(null)
  const [dbPages, setDbPages] = useState<DatabaseAnalyticsPage[]>([])
  const [dbUsers, setDbUsers] = useState<DatabaseAnalyticsUser[]>([])

  // Load Google Analytics Data
  const loadGoogleAnalytics = async () => {
    try {
      setLoading(true)
      
      const [statsRes, pagesRes] = await Promise.allSettled([
        getGoogleAnalyticsStats(days),
        getGoogleAnalyticsPages(days, 10),
      ])
      
      if (statsRes.status === 'fulfilled' && statsRes.value.data.success) {
        setGaStats(statsRes.value.data.data)
        setGaAvailable(true)
      } else {
        setGaAvailable(false)
      }
      
      if (pagesRes.status === 'fulfilled' && pagesRes.value.data.success) {
        setGaPages(pagesRes.value.data.data)
      }
    } catch (error: any) {
      console.error('Error loading Google Analytics:', error)
      setGaAvailable(false)
    } finally {
      setLoading(false)
    }
  }

  // Load Database Analytics Data
  const loadDatabaseAnalytics = async () => {
    try {
      setLoading(true)
      
      const [statsRes, pagesRes, usersRes] = await Promise.allSettled([
        getDatabaseAnalyticsStats(days),
        getDatabaseAnalyticsPages(days, 10),
        getDatabaseAnalyticsUsers(days, 20),
      ])
      
      if (statsRes.status === 'fulfilled' && statsRes.value.data.success) {
        setDbStats(statsRes.value.data.data)
      }
      
      if (pagesRes.status === 'fulfilled' && pagesRes.value.data.success) {
        setDbPages(pagesRes.value.data.data)
      }
      
      if (usersRes.status === 'fulfilled' && usersRes.value.data.success) {
        setDbUsers(usersRes.value.data.data)
      }
    } catch (error: any) {
      console.error('Error loading Database Analytics:', error)
      showToast('خطا در بارگذاری آمار دیتابیس', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  // Load all data
  const loadAllData = async () => {
    await Promise.all([
      loadGoogleAnalytics(),
      loadDatabaseAnalytics(),
    ])
  }

  useEffect(() => {
    if (!isAdmin) {
      return
    }
    
    loadAllData()
    
    const interval = setInterval(() => {
      if (typeof document !== 'undefined' && !document.hidden) {
        loadAllData()
      }
    }, AUTO_REFRESH_INTERVAL_MS)
    
    return () => clearInterval(interval)
  }, [isAdmin, days])

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

  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat('fa-IR').format(num)
  }

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds} ثانیه`
    if (seconds < 3600) return `${Math.floor(seconds / 60)} دقیقه`
    return `${Math.floor(seconds / 3600)} ساعت و ${Math.floor((seconds % 3600) / 60)} دقیقه`
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <Breadcrumbs />
      
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
          آمار و Analytics
        </h1>
        <p className="text-gray-400 text-lg">آمار بازدید، کاربران و صفحات</p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex items-center gap-4">
        <label className="text-gray-300">بازه زمانی:</label>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600"
        >
          <option value={1}>1 روز</option>
          <option value={7}>7 روز</option>
          <option value={30}>30 روز</option>
          <option value={90}>90 روز</option>
        </select>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-700">
          <nav className="-mb-px flex space-x-8 space-x-reverse">
            {[
              { id: 'overview', label: 'نمای کلی', icon: '📊' },
              { id: 'google', label: 'Google Analytics', icon: '🔍' },
              { id: 'database', label: 'Database Analytics', icon: '💾' },
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
      {loading && !gaStats && !dbStats ? (
        <div className="bg-gray-800 rounded-lg p-12 text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
          <div className="text-white text-xl">در حال بارگذاری...</div>
        </div>
      ) : (
        <>
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Google Analytics Stats */}
                {gaAvailable && gaStats && (
                  <>
                    <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 shadow-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-gray-200 text-sm font-medium">کاربران فعال (GA)</h3>
                        <svg className="w-6 h-6 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                        </svg>
                      </div>
                      <p className="text-white text-3xl font-bold">{formatNumber(gaStats.activeUsers)}</p>
                    </div>
                    
                    <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl p-6 shadow-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-gray-200 text-sm font-medium">بازدید صفحات (GA)</h3>
                        <svg className="w-6 h-6 text-green-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      </div>
                      <p className="text-white text-3xl font-bold">{formatNumber(gaStats.screenPageViews)}</p>
                    </div>
                  </>
                )}
                
                {/* Database Analytics Stats */}
                {dbStats && (
                  <>
                    <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl p-6 shadow-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-gray-200 text-sm font-medium">جلسات (DB)</h3>
                        <svg className="w-6 h-6 text-purple-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <p className="text-white text-3xl font-bold">{formatNumber(dbStats.totalSessions)}</p>
                    </div>
                    
                    <div className="bg-gradient-to-br from-orange-600 to-orange-700 rounded-xl p-6 shadow-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-gray-200 text-sm font-medium">کاربران لاگین شده (DB)</h3>
                        <svg className="w-6 h-6 text-orange-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </div>
                      <p className="text-white text-3xl font-bold">{formatNumber(dbStats.uniqueUsers)}</p>
                    </div>
                    
                    <div className="bg-gradient-to-br from-teal-600 to-teal-700 rounded-xl p-6 shadow-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-gray-200 text-sm font-medium">کل کاربران ثبت‌نام شده</h3>
                        <svg className="w-6 h-6 text-teal-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                        </svg>
                      </div>
                      <p className="text-white text-3xl font-bold">{formatNumber(dbStats.totalRegisteredUsers || 0)}</p>
                    </div>
                    
                    <div className="bg-gradient-to-br from-cyan-600 to-cyan-700 rounded-xl p-6 shadow-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-gray-200 text-sm font-medium">شماره موبایل‌های منحصر به فرد</h3>
                        <svg className="w-6 h-6 text-cyan-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                        </svg>
                      </div>
                      <p className="text-white text-3xl font-bold">{formatNumber(dbStats.uniquePhoneNumbers || 0)}</p>
                    </div>
                    
                    {dbStats.registeredUsersInPeriod !== undefined && (
                      <div className="bg-gradient-to-br from-indigo-600 to-indigo-700 rounded-xl p-6 shadow-lg">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-gray-200 text-sm font-medium">ثبت‌نام در بازه زمانی</h3>
                          <svg className="w-6 h-6 text-indigo-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <p className="text-white text-3xl font-bold">{formatNumber(dbStats.registeredUsersInPeriod)}</p>
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Pages Tables */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Google Analytics Pages */}
                {gaAvailable && gaPages.length > 0 && (
                  <div className="bg-gray-800 rounded-lg p-6">
                    <h3 className="text-xl font-bold text-white mb-4">صفحات پربازدید (Google Analytics)</h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-700">
                        <thead>
                          <tr>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">صفحه</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">بازدید</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">کاربران</th>
                          </tr>
                        </thead>
                        <tbody className="bg-gray-700 divide-y divide-gray-600">
                          {gaPages.slice(0, 5).map((page, index) => (
                            <tr key={index}>
                              <td className="px-4 py-3 text-sm text-white">{page.title || page.path}</td>
                              <td className="px-4 py-3 text-sm text-white">{formatNumber(page.views)}</td>
                              <td className="px-4 py-3 text-sm text-white">{formatNumber(page.users)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Database Analytics Pages */}
                {dbPages.length > 0 && (
                  <div className="bg-gray-800 rounded-lg p-6">
                    <h3 className="text-xl font-bold text-white mb-4">صفحات پربازدید (Database)</h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-700">
                        <thead>
                          <tr>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">صفحه</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">بازدید</th>
                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">کاربران</th>
                          </tr>
                        </thead>
                        <tbody className="bg-gray-700 divide-y divide-gray-600">
                          {dbPages.slice(0, 5).map((page, index) => (
                            <tr key={index}>
                              <td className="px-4 py-3 text-sm text-white">{page.title || page.path}</td>
                              <td className="px-4 py-3 text-sm text-white">{formatNumber(page.views)}</td>
                              <td className="px-4 py-3 text-sm text-white">{formatNumber(page.users)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Google Analytics Tab */}
          {activeTab === 'google' && (
            <div className="space-y-6">
              {gaAvailable === false ? (
                <div className="bg-yellow-800 rounded-lg p-6 text-center">
                  <p className="text-yellow-200">
                    ⚠️ Google Analytics در دسترس نیست. لطفا Service Account و Property ID را تنظیم کنید.
                  </p>
                </div>
              ) : gaStats ? (
                <>
                  {/* Stats Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">کاربران فعال</h3>
                      <p className="text-white text-2xl font-bold">{formatNumber(gaStats.activeUsers)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">کاربران جدید</h3>
                      <p className="text-white text-2xl font-bold">{formatNumber(gaStats.newUsers)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">جلسات</h3>
                      <p className="text-white text-2xl font-bold">{formatNumber(gaStats.sessions)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">بازدید صفحات</h3>
                      <p className="text-white text-2xl font-bold">{formatNumber(gaStats.screenPageViews)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">میانگین مدت جلسه</h3>
                      <p className="text-white text-2xl font-bold">{formatDuration(gaStats.averageSessionDuration)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">نرخ پرش</h3>
                      <p className="text-white text-2xl font-bold">{(gaStats.bounceRate * 100).toFixed(1)}%</p>
                    </div>
                  </div>

                  {/* Pages Table */}
                  {gaPages.length > 0 && (
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-xl font-bold text-white mb-4">صفحات پربازدید</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-700">
                          <thead>
                            <tr>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">صفحه</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">بازدید</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">کاربران</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">میانگین مدت</th>
                            </tr>
                          </thead>
                          <tbody className="bg-gray-700 divide-y divide-gray-600">
                            {gaPages.map((page, index) => (
                              <tr key={index}>
                                <td className="px-4 py-3 text-sm text-white">{page.title || page.path}</td>
                                <td className="px-4 py-3 text-sm text-white">{formatNumber(page.views)}</td>
                                <td className="px-4 py-3 text-sm text-white">{formatNumber(page.users)}</td>
                                <td className="px-4 py-3 text-sm text-white">{formatDuration(page.avgDuration)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="bg-gray-800 rounded-lg p-12 text-center">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
                  <div className="text-white text-xl">در حال بارگذاری...</div>
                </div>
              )}
            </div>
          )}

          {/* Database Analytics Tab */}
          {activeTab === 'database' && (
            <div className="space-y-6">
              {dbStats ? (
                <>
                  {/* Stats Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">کل جلسات</h3>
                      <p className="text-white text-2xl font-bold">{formatNumber(dbStats.totalSessions)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">جلسات فعال</h3>
                      <p className="text-white text-2xl font-bold">{formatNumber(dbStats.activeSessions)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">کاربران لاگین شده</h3>
                      <p className="text-white text-2xl font-bold">{formatNumber(dbStats.uniqueUsers)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">کل کاربران ثبت‌نام شده</h3>
                      <p className="text-white text-2xl font-bold">{formatNumber(dbStats.totalRegisteredUsers || 0)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">شماره موبایل‌های منحصر به فرد</h3>
                      <p className="text-white text-2xl font-bold">{formatNumber(dbStats.uniquePhoneNumbers || 0)}</p>
                    </div>
                    {dbStats.registeredUsersInPeriod !== undefined && (
                      <div className="bg-gray-800 rounded-lg p-6">
                        <h3 className="text-gray-300 text-sm mb-2">ثبت‌نام در بازه زمانی</h3>
                        <p className="text-white text-2xl font-bold">{formatNumber(dbStats.registeredUsersInPeriod)}</p>
                      </div>
                    )}
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">بازدید صفحات</h3>
                      <p className="text-white text-2xl font-bold">{formatNumber(dbStats.totalPageVisits)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">صفحات منحصر به فرد</h3>
                      <p className="text-white text-2xl font-bold">{formatNumber(dbStats.uniquePages)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">میانگین مدت جلسه</h3>
                      <p className="text-white text-2xl font-bold">{formatDuration(dbStats.avgSessionDuration)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-gray-300 text-sm mb-2">میانگین مدت صفحه</h3>
                      <p className="text-white text-2xl font-bold">{formatDuration(dbStats.avgPageDuration)}</p>
                    </div>
                  </div>

                  {/* Pages Table */}
                  {dbPages.length > 0 && (
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-xl font-bold text-white mb-4">صفحات پربازدید</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-700">
                          <thead>
                            <tr>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">صفحه</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">بازدید</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">کاربران</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">میانگین مدت</th>
                            </tr>
                          </thead>
                          <tbody className="bg-gray-700 divide-y divide-gray-600">
                            {dbPages.map((page, index) => (
                              <tr key={index}>
                                <td className="px-4 py-3 text-sm text-white">{page.title || page.path}</td>
                                <td className="px-4 py-3 text-sm text-white">{formatNumber(page.views)}</td>
                                <td className="px-4 py-3 text-sm text-white">{formatNumber(page.users)}</td>
                                <td className="px-4 py-3 text-sm text-white">{formatDuration(page.avgDuration)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Users Table */}
                  {dbUsers.length > 0 && (
                    <div className="bg-gray-800 rounded-lg p-6">
                      <h3 className="text-xl font-bold text-white mb-4">کاربران فعال</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-700">
                          <thead>
                            <tr>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">کاربر</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">جلسات</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">کل مدت</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">بازدید صفحات</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">آخرین ورود</th>
                            </tr>
                          </thead>
                          <tbody className="bg-gray-700 divide-y divide-gray-600">
                            {dbUsers.map((user, index) => (
                              <tr key={index}>
                                <td className="px-4 py-3 text-sm text-white">{user.username}</td>
                                <td className="px-4 py-3 text-sm text-white">{formatNumber(user.sessions)}</td>
                                <td className="px-4 py-3 text-sm text-white">{formatDuration(user.totalDuration)}</td>
                                <td className="px-4 py-3 text-sm text-white">{formatNumber(user.pageVisits)}</td>
                                <td className="px-4 py-3 text-sm text-white">
                                  {user.lastLogin ? new Date(user.lastLogin).toLocaleDateString('fa-IR') : '-'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="bg-gray-800 rounded-lg p-12 text-center">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
                  <div className="text-white text-xl">در حال بارگذاری...</div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

