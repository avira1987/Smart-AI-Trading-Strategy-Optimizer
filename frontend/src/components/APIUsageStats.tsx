import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from './ToastProvider'
import client from '../api/client'

interface ProviderStats {
  total_requests: number
  successful_requests: number
  failed_requests: number
  total_cost_usd: number
  total_cost_toman: number
}

interface APIUsageStats {
  total_requests: number
  successful_requests: number
  failed_requests: number
  success_rate: number
  total_cost_usd: number
  total_cost_toman: number
  provider_stats: Record<string, ProviderStats>
}

const PROVIDER_NAMES: Record<string, string> = {
  twelvedata: 'TwelveData',
  alphavantage: 'Alpha Vantage',
  oanda: 'OANDA',
  metalsapi: 'MetalsAPI',
  financialmodelingprep: 'Financial Modeling Prep',
  nerkh: 'Nerkh.io',
  gemini: 'Gemini AI',
  openai: 'OpenAI (ChatGPT)',
  kavenegar: 'Kavenegar',
  mt5: 'MetaTrader 5',
  zarinpal: 'Zarinpal',
}

export default function APIUsageStats() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [stats, setStats] = useState<APIUsageStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedDays, setSelectedDays] = useState<number | null>(30)
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null)

  useEffect(() => {
    if (!user?.id) {
      setStats(null)
      return
    }
    // Load stats for both admin and regular users
    loadStats()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDays, selectedProvider, user?.id])

  const loadStats = async () => {
    try {
      if (!user?.id) {
        return
      }
      setLoading(true)
      setStats(null)
      const params: Record<string, string> = {}
      if (selectedDays) {
        params.days = selectedDays.toString()
      }
      if (selectedProvider) {
        params.provider = selectedProvider
      }
      
      // Always use user-specific endpoint so each user only sees their own usage
      const endpoint = '/user/api-usage-stats/'
      
      console.log('Loading API usage stats with params:', params, 'endpoint:', endpoint)
      const response = await client.get<APIUsageStats>(endpoint, { params })
      console.log('API usage stats response:', response.data)
      
      if (response.data) {
        setStats(response.data)
      } else {
        console.warn('No data in response')
        setStats(null)
      }
    } catch (error: any) {
      console.error('Error loading API usage stats:', error)
      console.error('Error response:', error.response)
      console.error('Error data:', error.response?.data)
      showToast(error.response?.data?.message || 'خطا در بارگذاری آمار مصرف API', { type: 'error' })
      setStats(null)
    } finally {
      setLoading(false)
    }
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('fa-IR').format(num)
  }

  const formatCurrency = (amount: number, currency: 'usd' | 'toman' = 'toman') => {
    if (currency === 'usd') {
      return `$${amount.toFixed(4)}`
    }
    return `${formatNumber(Math.round(amount))} تومان`
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">آمار مصرف API و هزینه</h2>
          <p className="text-gray-400 text-sm">ردیابی و محاسبه هزینه استفاده از API ها</p>
        </div>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            بازه زمانی
          </label>
          <select
            value={selectedDays || ''}
            onChange={(e) => setSelectedDays(e.target.value ? parseInt(e.target.value) : null)}
            className="w-full px-3 py-2 border border-gray-600 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">همه زمان‌ها</option>
            <option value="7">۷ روز گذشته</option>
            <option value="30">۳۰ روز گذشته</option>
            <option value="90">۹۰ روز گذشته</option>
            <option value="365">یک سال گذشته</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            فیلتر بر اساس Provider
          </label>
          <select
            value={selectedProvider || ''}
            onChange={(e) => setSelectedProvider(e.target.value || null)}
            className="w-full px-3 py-2 border border-gray-600 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">همه Provider ها</option>
            {Object.keys(PROVIDER_NAMES).map((key) => (
              <option key={key} value={key}>
                {PROVIDER_NAMES[key]}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
          <div className="text-gray-400">در حال بارگذاری آمار...</div>
        </div>
      ) : stats ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {/* Total Requests */}
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-gray-200 text-sm font-medium">کل درخواست‌ها</h3>
                <svg className="w-6 h-6 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <p className="text-white text-2xl font-bold">
                {formatNumber(stats.total_requests)}
              </p>
            </div>

            {/* Success Rate */}
            <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-gray-200 text-sm font-medium">نرخ موفقیت</h3>
                <svg className="w-6 h-6 text-green-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-white text-2xl font-bold">
                {stats.success_rate.toFixed(1)}%
              </p>
            </div>

            {/* Total Cost USD */}
            <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-gray-200 text-sm font-medium">هزینه کل (USD)</h3>
                <svg className="w-6 h-6 text-purple-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-white text-2xl font-bold">
                {formatCurrency(stats.total_cost_usd, 'usd')}
              </p>
            </div>

            {/* Total Cost Toman */}
            <div className="bg-gradient-to-br from-orange-600 to-orange-700 rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-gray-200 text-sm font-medium">هزینه کل (تومان)</h3>
                <svg className="w-6 h-6 text-orange-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-white text-2xl font-bold">
                {formatCurrency(stats.total_cost_toman, 'toman')}
              </p>
            </div>
          </div>

          {/* Provider Stats Table */}
          {Object.keys(stats.provider_stats).length > 0 && (
            <div className="bg-gray-700 rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-600">
                <h3 className="text-xl font-semibold text-white">آمار بر اساس Provider</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-800">
                    <tr>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Provider
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                        کل درخواست‌ها
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                        موفق
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                        ناموفق
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                        هزینه (USD)
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                        هزینه (تومان)
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-600">
                    {Object.entries(stats.provider_stats).map(([provider, providerStats]) => (
                      <tr key={provider} className="hover:bg-gray-600 transition">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                          {PROVIDER_NAMES[provider] || provider}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {formatNumber(providerStats.total_requests)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-green-400">
                          {formatNumber(providerStats.successful_requests)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-400">
                          {formatNumber(providerStats.failed_requests)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {formatCurrency(providerStats.total_cost_usd, 'usd')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {formatCurrency(providerStats.total_cost_toman, 'toman')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {Object.keys(stats.provider_stats).length === 0 && (
            <div className="text-center py-12 bg-gray-700 rounded-lg">
              <p className="text-gray-400">هیچ داده‌ای برای نمایش وجود ندارد</p>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-400 mb-2">خطا در بارگذاری آمار</p>
          <button
            onClick={() => loadStats()}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
          >
            تلاش مجدد
          </button>
        </div>
      )}
    </div>
  )
}

