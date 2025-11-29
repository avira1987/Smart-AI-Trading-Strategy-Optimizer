import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/ToastProvider'
import { useFeatureFlags } from '../context/FeatureFlagsContext'
import {
  getSystemSettings,
  updateSystemSettings,
  clearAICache,
  type SystemSettingsResponse,
} from '../api/client'

export default function SystemSettings() {
  const { isAdmin } = useAuth()
  const { showToast } = useToast()
  const { reload: reloadFeatureFlags } = useFeatureFlags()
  const [systemSettings, setSystemSettings] = useState<SystemSettingsResponse | null>(null)
  const [settingsLoading, setSettingsLoading] = useState(false)
  const [settingsActionLoading, setSettingsActionLoading] = useState(false)
  const [clearingCache, setClearingCache] = useState(false)

  useEffect(() => {
    if (isAdmin) {
      loadSystemSettings()
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

  const handleToggleAICache = async () => {
    if (!systemSettings) {
      return
    }

    try {
      setSettingsActionLoading(true)
      const response = await updateSystemSettings({
        use_ai_cache: !systemSettings.use_ai_cache,
      })
      setSystemSettings(response.data)
      showToast(
        response.data.use_ai_cache
          ? 'استفاده از کش برای پردازش هوش مصنوعی فعال شد'
          : 'استفاده از کش برای پردازش هوش مصنوعی غیرفعال شد. در زمان پردازش از API استفاده می‌شود.',
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

  const handleClearCache = async () => {
    if (!confirm('آیا مطمئن هستید که می‌خواهید همه فایل‌های کش AI را پاک کنید؟ این کار باعث می‌شود که درخواست‌های بعدی از API استفاده کنند.')) {
      return
    }

    try {
      setClearingCache(true)
      const response = await clearAICache()
      showToast(response.data.message || `${response.data.deleted_count} فایل کش پاک شد`, { type: 'success' })
    } catch (error: any) {
      const message = error.response?.data?.message || error.response?.data?.detail || 'خطا در پاک کردن کش'
      showToast(message, { type: 'error' })
    } finally {
      setClearingCache(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="bg-gray-800 rounded-lg p-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-white">تنظیمات وب‌سایت</h2>
            <p className="text-gray-400 text-sm mt-1">مدیریت تنظیمات عمومی وب‌سایت و ویژگی‌های سیستم</p>
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

            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-gray-900 rounded-lg p-5">
              <div>
                <h4 className="text-lg font-semibold text-white">استفاده از کش برای پردازش هوش مصنوعی</h4>
                <p className="text-gray-400 text-sm mt-1">
                  با غیرفعال کردن این گزینه، در زمان استفاده از دکمه پردازش، از داده‌های کش شده استفاده نمی‌شود و همیشه از API استفاده می‌شود. این باعث می‌شود که همیشه آخرین تحلیل از API دریافت شود اما هزینه توکن‌ها افزایش می‌یابد.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    systemSettings.use_ai_cache
                      ? 'bg-green-900 text-green-300'
                      : 'bg-red-900 text-red-300'
                  }`}
                >
                  {systemSettings.use_ai_cache ? 'فعال' : 'غیرفعال'}
                </span>
                <button
                  onClick={handleToggleAICache}
                  disabled={settingsActionLoading || !systemSettings}
                  className={`px-4 py-2 rounded-lg font-medium text-white transition disabled:opacity-50 disabled:cursor-not-allowed ${
                    systemSettings.use_ai_cache
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {settingsActionLoading
                    ? 'در حال اعمال...'
                    : systemSettings.use_ai_cache
                    ? 'غیرفعال کردن'
                    : 'فعال کردن'}
                </button>
              </div>
            </div>

            {/* Cost Settings */}
            <div className="bg-gray-900 rounded-lg p-5 space-y-4">
              <h4 className="text-lg font-semibold text-white">تنظیمات هزینه‌ها</h4>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    هزینه هر 1000 توکن (تومان)
                  </label>
                  <input
                    type="number"
                    value={systemSettings.token_cost_per_1000 || ''}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value)
                      if (!isNaN(value) && value >= 0) {
                        setSystemSettings({ ...systemSettings, token_cost_per_1000: value })
                      }
                    }}
                    onBlur={async () => {
                      if (systemSettings.token_cost_per_1000 !== undefined) {
                        try {
                          setSettingsActionLoading(true)
                          const response = await updateSystemSettings({
                            token_cost_per_1000: systemSettings.token_cost_per_1000,
                          })
                          setSystemSettings(response.data)
                          showToast('هزینه توکن به‌روزرسانی شد', { type: 'success' })
                        } catch (error: any) {
                          showToast('خطا در به‌روزرسانی هزینه توکن', { type: 'error' })
                        } finally {
                          setSettingsActionLoading(false)
                        }
                      }
                    }}
                    className="w-full px-4 py-2 bg-gray-800 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0"
                    step="0.01"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    هزینه هر بک‌تست (تومان)
                  </label>
                  <input
                    type="number"
                    value={systemSettings.backtest_cost || ''}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value)
                      if (!isNaN(value) && value >= 0) {
                        setSystemSettings({ ...systemSettings, backtest_cost: value })
                      }
                    }}
                    onBlur={async () => {
                      if (systemSettings.backtest_cost !== undefined) {
                        try {
                          setSettingsActionLoading(true)
                          const response = await updateSystemSettings({
                            backtest_cost: systemSettings.backtest_cost,
                          })
                          setSystemSettings(response.data)
                          showToast('هزینه بک‌تست به‌روزرسانی شد', { type: 'success' })
                        } catch (error: any) {
                          showToast('خطا در به‌روزرسانی هزینه بک‌تست', { type: 'error' })
                        } finally {
                          setSettingsActionLoading(false)
                        }
                      }
                    }}
                    className="w-full px-4 py-2 bg-gray-800 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0"
                    step="0.01"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    هزینه پردازش هر استراتژی (تومان)
                  </label>
                  <input
                    type="number"
                    value={systemSettings.strategy_processing_cost || ''}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value)
                      if (!isNaN(value) && value >= 0) {
                        setSystemSettings({ ...systemSettings, strategy_processing_cost: value })
                      }
                    }}
                    onBlur={async () => {
                      if (systemSettings.strategy_processing_cost !== undefined) {
                        try {
                          setSettingsActionLoading(true)
                          const response = await updateSystemSettings({
                            strategy_processing_cost: systemSettings.strategy_processing_cost,
                          })
                          setSystemSettings(response.data)
                          showToast('هزینه پردازش استراتژی به‌روزرسانی شد', { type: 'success' })
                        } catch (error: any) {
                          showToast('خطا در به‌روزرسانی هزینه پردازش استراتژی', { type: 'error' })
                        } finally {
                          setSettingsActionLoading(false)
                        }
                      }
                    }}
                    className="w-full px-4 py-2 bg-gray-800 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0"
                    step="0.01"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    مبلغ هدیه ثبت‌نام (تومان)
                  </label>
                  <input
                    type="number"
                    value={systemSettings.registration_bonus || ''}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value)
                      if (!isNaN(value) && value >= 0) {
                        setSystemSettings({ ...systemSettings, registration_bonus: value })
                      }
                    }}
                    onBlur={async () => {
                      if (systemSettings.registration_bonus !== undefined) {
                        try {
                          setSettingsActionLoading(true)
                          const response = await updateSystemSettings({
                            registration_bonus: systemSettings.registration_bonus,
                          })
                          setSystemSettings(response.data)
                          showToast('مبلغ هدیه ثبت‌نام به‌روزرسانی شد', { type: 'success' })
                        } catch (error: any) {
                          showToast('خطا در به‌روزرسانی مبلغ هدیه ثبت‌نام', { type: 'error' })
                        } finally {
                          setSettingsActionLoading(false)
                        }
                      }
                    }}
                    className="w-full px-4 py-2 bg-gray-800 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0"
                    step="0.01"
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-gray-900 rounded-lg p-5 border border-yellow-600/30">
              <div>
                <h4 className="text-lg font-semibold text-white">پاک کردن کش AI</h4>
                <p className="text-gray-400 text-sm mt-1">
                  با پاک کردن کش، تمام فایل‌های کش شده حذف می‌شوند و درخواست‌های بعدی از API استفاده می‌کنند. این کار برای تست یا دریافت تحلیل‌های جدید مفید است.
                </p>
              </div>
              <button
                onClick={handleClearCache}
                disabled={clearingCache}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {clearingCache ? 'در حال پاک کردن...' : 'پاک کردن کش'}
              </button>
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
    </div>
  )
}

