import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from './ToastProvider'
import client from '../api/client'

interface DDNSConfiguration {
  id?: number
  provider: string
  domain: string
  token?: string
  username?: string
  password?: string
  update_url?: string
  is_enabled: boolean
  update_interval_minutes: number
  last_update?: string
  last_ip?: string
  created_at?: string
  updated_at?: string
}

export default function DDNSConfiguration() {
  const { isAdmin } = useAuth()
  const { showToast } = useToast()
  const [configs, setConfigs] = useState<DDNSConfiguration[]>([])
  const [loading, setLoading] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [editingConfig, setEditingConfig] = useState<DDNSConfiguration | null>(null)
  const [formData, setFormData] = useState<DDNSConfiguration>({
    provider: 'duckdns',
    domain: '',
    token: '',
    username: '',
    password: '',
    update_url: '',
    is_enabled: false,
    update_interval_minutes: 5,
  })
  const [testing, setTesting] = useState<number | null>(null)
  const [updating, setUpdating] = useState(false)
  const [publicIP, setPublicIP] = useState<string>('')

  useEffect(() => {
    if (isAdmin) {
      loadConfigs()
      loadPublicIP()
    }
  }, [isAdmin])

  if (!isAdmin) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="text-red-400 text-center">
          ⚠️ فقط ادمین می‌تواند به این بخش دسترسی داشته باشد
        </div>
      </div>
    )
  }

  const loadConfigs = async () => {
    try {
      setLoading(true)
      const response = await client.get<DDNSConfiguration[]>('/ddns-configurations/')
      setConfigs(response.data)
    } catch (error: any) {
      console.error('Error loading DDNS configs:', error)
      showToast('خطا در بارگذاری تنظیمات DDNS', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const loadPublicIP = async () => {
    try {
      const response = await client.get<{ success: boolean; ip: string }>('/ddns-configurations/get_public_ip/')
      if (response.data.success) {
        setPublicIP(response.data.ip)
      }
    } catch (error) {
      console.error('Error loading public IP:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.domain.trim()) {
      showToast('لطفاً دامنه را وارد کنید', { type: 'warning' })
      return
    }

    if (formData.provider === 'duckdns' && !formData.token?.trim()) {
      showToast('لطفاً Token را وارد کنید', { type: 'warning' })
      return
    }

    if ((formData.provider === 'noip' || formData.provider === 'dynu') && (!formData.username?.trim() || !formData.password?.trim())) {
      showToast('لطفاً Username و Password را وارد کنید', { type: 'warning' })
      return
    }

    if (formData.provider === 'custom' && !formData.update_url?.trim()) {
      showToast('لطفاً Update URL را وارد کنید', { type: 'warning' })
      return
    }

    try {
      setLoading(true)
      if (editingConfig?.id) {
        await client.put(`/ddns-configurations/${editingConfig.id}/`, formData)
        showToast('تنظیمات DDNS به‌روزرسانی شد', { type: 'success' })
      } else {
        await client.post('/ddns-configurations/', formData)
        showToast('تنظیمات DDNS ایجاد شد', { type: 'success' })
      }
      setShowModal(false)
      setEditingConfig(null)
      setFormData({
        provider: 'duckdns',
        domain: '',
        token: '',
        username: '',
        password: '',
        update_url: '',
        is_enabled: false,
        update_interval_minutes: 5,
      })
      loadConfigs()
    } catch (error: any) {
      console.error('Error saving DDNS config:', error)
      showToast(error.response?.data?.message || 'خطا در ذخیره تنظیمات', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (config: DDNSConfiguration) => {
    setEditingConfig(config)
    setFormData({
      provider: config.provider,
      domain: config.domain,
      token: config.token || '',
      username: config.username || '',
      password: config.password || '',
      update_url: config.update_url || '',
      is_enabled: config.is_enabled,
      update_interval_minutes: config.update_interval_minutes,
    })
    setShowModal(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('آیا مطمئن هستید که می‌خواهید این تنظیمات را حذف کنید؟')) {
      return
    }

    try {
      await client.delete(`/ddns-configurations/${id}/`)
      showToast('تنظیمات DDNS حذف شد', { type: 'success' })
      loadConfigs()
    } catch (error: any) {
      console.error('Error deleting DDNS config:', error)
      showToast('خطا در حذف تنظیمات', { type: 'error' })
    }
  }

  const handleTest = async (id: number) => {
    setTesting(id)
    try {
      const response = await client.post<{ success: boolean; message: string; response?: string }>(`/ddns-configurations/${id}/test/`)
      if (response.data.success) {
        showToast(`✅ ${response.data.message}`, { type: 'success', duration: 5000 })
      } else {
        showToast(`❌ ${response.data.message}`, { type: 'error', duration: 5000 })
      }
      loadConfigs()
    } catch (error: any) {
      console.error('Error testing DDNS:', error)
      showToast(error.response?.data?.message || 'خطا در تست DDNS', { type: 'error' })
    } finally {
      setTesting(null)
    }
  }

  const handleUpdateNow = async () => {
    setUpdating(true)
    try {
      const response = await client.post<{ success: boolean; message: string }>('/ddns-configurations/update_now/')
      if (response.data.success) {
        showToast('✅ به‌روزرسانی DDNS انجام شد', { type: 'success' })
      } else {
        showToast(`❌ ${response.data.message}`, { type: 'error' })
      }
      loadConfigs()
    } catch (error: any) {
      console.error('Error updating DDNS:', error)
      showToast(error.response?.data?.message || 'خطا در به‌روزرسانی', { type: 'error' })
    } finally {
      setUpdating(false)
    }
  }

  const providerOptions = [
    { value: 'duckdns', label: 'DuckDNS (رایگان)' },
    { value: 'noip', label: 'No-IP (رایگان)' },
    { value: 'dynu', label: 'Dynu (رایگان)' },
    { value: 'freedns', label: 'FreeDNS (رایگان)' },
    { value: 'custom', label: 'سرویس سفارشی' },
  ]

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-white">تنظیمات DDNS</h2>
        <div className="flex gap-2">
          <button
            onClick={handleUpdateNow}
            disabled={updating}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {updating ? 'در حال به‌روزرسانی...' : '🔄 به‌روزرسانی دستی'}
          </button>
          <button
            onClick={() => {
              setEditingConfig(null)
              setFormData({
                provider: 'duckdns',
                domain: '',
                token: '',
                username: '',
                password: '',
                update_url: '',
                is_enabled: false,
                update_interval_minutes: 5,
              })
              setShowModal(true)
            }}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            ➕ افزودن تنظیمات
          </button>
        </div>
      </div>

      {publicIP && (
        <div className="mb-4 p-3 bg-blue-900 rounded text-blue-100">
          <strong>IP عمومی فعلی:</strong> {publicIP}
        </div>
      )}

      <div className="mb-4 p-4 bg-yellow-900 rounded text-yellow-100">
        <strong>💡 نکته:</strong> برای راهنمای کامل تنظیم DDNS، فایل <code className="bg-gray-800 px-2 py-1 rounded">راهنمای_تنظیم_DDNS.md</code> را مطالعه کنید.
      </div>

      {loading && !configs.length ? (
        <div className="text-center text-gray-400">در حال بارگذاری...</div>
      ) : configs.length === 0 ? (
        <div className="text-center text-gray-400 py-8">
          هیچ تنظیمات DDNS ثبت نشده است. روی "افزودن تنظیمات" کلیک کنید.
        </div>
      ) : (
        <div className="space-y-4">
          {configs.map((config) => (
            <div key={config.id} className="bg-gray-700 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-xl font-semibold text-white">{config.domain}</h3>
                    <span className={`px-2 py-1 rounded text-sm ${config.is_enabled ? 'bg-green-600 text-white' : 'bg-gray-600 text-gray-300'}`}>
                      {config.is_enabled ? 'فعال' : 'غیرفعال'}
                    </span>
                    <span className="px-2 py-1 rounded text-sm bg-blue-600 text-white">
                      {providerOptions.find(p => p.value === config.provider)?.label}
                    </span>
                  </div>
                  <div className="text-gray-300 text-sm space-y-1">
                    <div>فاصله به‌روزرسانی: هر {config.update_interval_minutes} دقیقه</div>
                    {config.last_update && (
                      <div>آخرین به‌روزرسانی: {new Date(config.last_update).toLocaleString('fa-IR')}</div>
                    )}
                    {config.last_ip && (
                      <div>آخرین IP: {config.last_ip}</div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleTest(config.id!)}
                    disabled={testing === config.id}
                    className="px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700 disabled:opacity-50"
                  >
                    {testing === config.id ? 'در حال تست...' : '🧪 تست'}
                  </button>
                  <button
                    onClick={() => handleEdit(config)}
                    className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                  >
                    ✏️ ویرایش
                  </button>
                  <button
                    onClick={() => handleDelete(config.id!)}
                    className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                  >
                    🗑️ حذف
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-white mb-4">
              {editingConfig ? 'ویرایش تنظیمات DDNS' : 'افزودن تنظیمات DDNS'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-gray-300 mb-2">سرویس DDNS</label>
                <select
                  value={formData.provider}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-700 text-white rounded"
                  required
                >
                  {providerOptions.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-gray-300 mb-2">
                  دامنه {formData.provider === 'duckdns' && '(بدون .duckdns.org)'}
                </label>
                <input
                  type="text"
                  value={formData.domain}
                  onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-700 text-white rounded"
                  placeholder={formData.provider === 'duckdns' ? 'myforex' : 'mydomain.ddns.net'}
                  required
                />
              </div>

              {formData.provider === 'duckdns' && (
                <div>
                  <label className="block text-gray-300 mb-2">Token</label>
                  <input
                    type="password"
                    value={formData.token}
                    onChange={(e) => setFormData({ ...formData, token: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-700 text-white rounded"
                    placeholder="Token از DuckDNS"
                    required
                  />
                </div>
              )}

              {(formData.provider === 'noip' || formData.provider === 'dynu') && (
                <>
                  <div>
                    <label className="block text-gray-300 mb-2">Username</label>
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      className="w-full px-4 py-2 bg-gray-700 text-white rounded"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-gray-300 mb-2">Password</label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full px-4 py-2 bg-gray-700 text-white rounded"
                      required
                    />
                  </div>
                </>
              )}

              {formData.provider === 'custom' && (
                <div>
                  <label className="block text-gray-300 mb-2">Update URL</label>
                  <input
                    type="url"
                    value={formData.update_url}
                    onChange={(e) => setFormData({ ...formData, update_url: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-700 text-white rounded"
                    placeholder="https://example.com/update?domain=DOMAIN&token=TOKEN&ip=IP"
                    required
                  />
                  <p className="text-sm text-gray-400 mt-1">IP به صورت خودکار جایگزین می‌شود</p>
                </div>
              )}

              <div>
                <label className="block text-gray-300 mb-2">فاصله به‌روزرسانی (دقیقه)</label>
                <input
                  type="number"
                  value={formData.update_interval_minutes}
                  onChange={(e) => setFormData({ ...formData, update_interval_minutes: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 bg-gray-700 text-white rounded"
                  min="1"
                  required
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_enabled"
                  checked={formData.is_enabled}
                  onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
                  className="w-4 h-4"
                />
                <label htmlFor="is_enabled" className="text-gray-300">فعال کردن DDNS</label>
              </div>

              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false)
                    setEditingConfig(null)
                  }}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  انصراف
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? 'در حال ذخیره...' : 'ذخیره'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

