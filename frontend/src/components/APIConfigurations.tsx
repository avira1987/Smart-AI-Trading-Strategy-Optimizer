import { useState, useEffect } from 'react'
import { getAPIConfigurations, addAPIConfiguration, updateAPIConfiguration, deleteAPIConfiguration, testAPIConfiguration, getAvailableProviders, testMT5Connection, type APIConfiguration } from '../api/client'
import { checkIPLocation } from '../api/auth'
import { useToast } from './ToastProvider'
import { useAuth } from '../context/AuthContext'
import { useRateLimit } from '../hooks/useRateLimit'

export default function APIConfigurations() {
  const { isAdmin } = useAuth()
  const [apis, setApis] = useState<APIConfiguration[]>([])
  const [availableProviders, setAvailableProviders] = useState<string[]>([])
  const [showModal, setShowModal] = useState(false)
  const [editingApi, setEditingApi] = useState<APIConfiguration | null>(null)
  const [provider, setProvider] = useState('twelvedata')
  const [apiKey, setApiKey] = useState('')
  const [testing, setTesting] = useState<number | null>(null)
  const [testingMT5, setTestingMT5] = useState(false)
  const [checkingIP, setCheckingIP] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  // API providers for trading data (available to all users)
  const tradingDataProviders = [
    { value: 'twelvedata', label: 'TwelveData' },
    { value: 'alphavantage', label: 'Alpha Vantage' },
    { value: 'oanda', label: 'OANDA' },
    { value: 'metalsapi', label: 'MetalsAPI' },
    { value: 'financialmodelingprep', label: 'Financial Modeling Prep' },
    { value: 'nerkh', label: 'Nerkh.io (قیمت طلا)' },
    { value: 'gemini', label: 'Gemini AI (Google AI Studio)' },
    { value: 'openai', label: 'OpenAI (ChatGPT)' },
    { value: 'cohere', label: 'Cohere AI' },
    { value: 'openrouter', label: 'OpenRouter' },
    { value: 'together_ai', label: 'Together AI' },
    { value: 'deepinfra', label: 'DeepInfra' },
    { value: 'groq', label: 'GroqCloud' }
  ]
  
  // API providers for backend/system (admin only)
  const backendProviders = [
    { value: 'kavenegar', label: 'Kavenegar (SMS)' },
    { value: 'zarinpal', label: 'Zarinpal (Merchant ID)' }
  ]
  
  // All providers (for admin) or only trading data providers (for regular users)
  const supportedProviders = isAdmin 
    ? [...tradingDataProviders, ...backendProviders]
    : tradingDataProviders
  
  // Backend provider names for filtering
  const backendProviderNames = ['kavenegar', 'zarinpal']
  const { showToast } = useToast()
  const rateLimitClickSubmit = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'apiConfig-submit' })
  const rateLimitClickUpdate = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'apiConfig-update' })
  const rateLimitClickDelete = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'apiConfig-delete' })
  const rateLimitClickTest = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'apiConfig-test' })
  const rateLimitClickTestMT5 = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'apiConfig-testMT5' })
  const rateLimitClickCheckIP = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'apiConfig-checkIP' })

  useEffect(() => {
    loadAPIs()
    loadAvailableProviders()
  }, [isAdmin]) // Reload when admin status changes

  const loadAPIs = async () => {
    try {
      console.log('Loading API configurations...') // Debug log
      const response = await getAPIConfigurations()
      console.log('API Configurations response:', response) // Debug log
      
      // Handle Django REST Framework pagination format
      let apisData = []
      if (response.data && response.data.results) {
        apisData = response.data.results
        console.log('Using paginated results:', apisData.length, 'items') // Debug log
      } else if (Array.isArray(response.data)) {
        apisData = response.data
        console.log('Using direct array:', apisData.length, 'items') // Debug log
      } else {
        console.log('Unexpected response format:', response.data) // Debug log
        apisData = []
      }
      
      // Note: Backend filtering is done on the server side, but we also filter here for safety
      if (!isAdmin) {
        apisData = apisData.filter(api => !backendProviderNames.includes(api.provider))
      }
      
      console.log('Final API Configurations data:', apisData) // Debug log
      setApis(apisData)
    } catch (error: any) {
      console.error('Error loading APIs:', error)
      console.error('Error details:', error.response?.data) // Debug log
      setApis([])
      showToast('Failed to load API configurations', { type: 'error' })
    }
  }

  const loadAvailableProviders = async () => {
    try {
      const response = await getAvailableProviders()
      console.log('Available providers response:', response) // Debug log
      
    
      if (response.data && response.data.available_providers) {
        setAvailableProviders(response.data.available_providers)
      }
    } catch (error) {
      console.error('Error loading available providers:', error)
      setAvailableProviders([])
      showToast('Failed to load available providers', { type: 'error' })
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!apiKey.trim()) {
      showToast('Please enter an API key', { type: 'warning' })
      return
    }

    // Check if user is trying to add backend provider without admin access
    if (backendProviderNames.includes(provider) && !isAdmin) {
      showToast('فقط ادمین می‌تواند تنظیمات بک‌اند را اضافه کند', { type: 'error' })
      return
    }

    const submitAction = rateLimitClickSubmit(async () => {
      try {
        console.log('Submitting API configuration:', { provider, apiKey }) // Debug log
        
        const response = await addAPIConfiguration({ 
          provider, 
          api_key: apiKey, 
          is_active: true 
        })
        
        console.log('API configuration response:', response) // Debug log
        
        setSuccessMessage('API key added successfully')
        setTimeout(() => setSuccessMessage(null), 2500)
        showToast('API key added successfully', { type: 'success' })
        setShowModal(false)
        setApiKey('')
        setProvider('twelvedata')
        
        // Reload APIs after successful addition
        await loadAPIs()
        await loadAvailableProviders()
      } catch (error: any) {
        console.error('Error adding API:', error)
        console.error('Error response:', error?.response?.data) // Debug log
        
        // Handle Django REST Framework validation errors
        let errorMessage = 'خطا در افزودن تنظیمات API'
        if (error?.response?.data) {
          const errorData = error.response.data
          
          // Check for detail field (general error)
          if (errorData.detail) {
            errorMessage = errorData.detail
          }
          // Check for non_field_errors (general validation errors)
          else if (errorData.non_field_errors && Array.isArray(errorData.non_field_errors)) {
            errorMessage = errorData.non_field_errors.join(', ')
          }
          // Check for field-specific errors
          else if (typeof errorData === 'object') {
            const fieldErrors: string[] = []
            for (const [field, messages] of Object.entries(errorData)) {
              if (Array.isArray(messages)) {
                fieldErrors.push(`${field}: ${messages.join(', ')}`)
              } else if (typeof messages === 'string') {
                fieldErrors.push(`${field}: ${messages}`)
              }
            }
            if (fieldErrors.length > 0) {
              errorMessage = fieldErrors.join(' | ')
            }
          }
          // Fallback to string if errorData is a string
          else if (typeof errorData === 'string') {
            errorMessage = errorData
          }
        } else if (error?.message) {
          errorMessage = error.message
        }
        
        showToast(errorMessage, { type: 'error', duration: 5000 })
      }
    })
    
    submitAction()
  }

  const handleTest = (id: number) => {
    const testAction = rateLimitClickTest(async () => {
      setTesting(id)
      try {
        const response = await testAPIConfiguration(id)
        if (response.data.status === 'success') {
          showToast(`API Test Successful: ${response.data.provider}${response.data.data_points ? ` (${response.data.data_points} data points)` : ''}`, { type: 'success' })
        } else {
          showToast(`API Test Failed: ${response.data.message}`, { type: 'error' })
        }
      } catch (error: any) {
        console.error('Error testing API configuration:', error)
        // Try to extract error message from response
        const errorMessage = error?.response?.data?.message || error?.response?.data?.detail || error?.message || 'Unknown error'
        showToast(`API Test Failed: ${errorMessage}`, { type: 'error' })
      } finally {
        setTesting(null)
      }
    })
    
    testAction()
  }

  const handleTestMT5 = () => {
    const testMT5Action = rateLimitClickTestMT5(async () => {
      setTestingMT5(true)
      try {
        const response = await testMT5Connection()
        if (response.data.status === 'success') {
          const accountInfo = response.data.account_info
          let message = response.data.message
          if (accountInfo) {
            message += ` | موجودی: ${accountInfo.balance?.toFixed(2) || 'N/A'} ${accountInfo.currency || ''}`
          }
          showToast(message, { type: 'success', duration: 5000 })
        } else {
          showToast(`تست اتصال Meta5 ناموفق: ${response.data.message}`, { type: 'error' })
        }
      } catch (error: any) {
        console.error('Error testing MT5 connection:', error)
        const errorMessage = error?.response?.data?.message || error?.response?.data?.detail || error?.message || 'خطای ناشناخته'
        showToast(`تست اتصال Meta5 ناموفق: ${errorMessage}`, { type: 'error' })
      } finally {
        setTestingMT5(false)
      }
    })
    
    testMT5Action()
  }

  const handleEdit = (api: APIConfiguration) => {
    setEditingApi(api)
    setProvider(api.provider)
    setApiKey(api.api_key)
    setShowModal(true)
  }

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingApi) return

    if (!apiKey.trim()) {
      showToast('Please enter an API key', { type: 'warning' })
      return
    }

    // Check if user is trying to update backend provider without admin access
    if (backendProviderNames.includes(provider) && !isAdmin) {
      showToast('فقط ادمین می‌تواند تنظیمات بک‌اند را ویرایش کند', { type: 'error' })
      return
    }

    const updateAction = rateLimitClickUpdate(async () => {
      try {
      console.log('Updating API configuration:', { id: editingApi.id, provider, apiKey }) // Debug log
      
      const response = await updateAPIConfiguration(editingApi.id, { 
        provider, 
        api_key: apiKey, 
        is_active: editingApi.is_active 
      })
      
      console.log('API configuration update response:', response) // Debug log
      
      setSuccessMessage('API key updated successfully')
      setTimeout(() => setSuccessMessage(null), 2500)
      showToast('API key updated successfully', { type: 'success' })
      setShowModal(false)
      setEditingApi(null)
      setApiKey('')
      setProvider('twelvedata')
      
      await loadAPIs()
      await loadAvailableProviders()
    } catch (error: any) {
      console.error('Error updating API:', error)
      console.error('Error response:', error?.response?.data) // Debug log
      
      // Handle Django REST Framework validation errors
      let errorMessage = 'خطا در ویرایش تنظیمات API'
      if (error?.response?.data) {
        const errorData = error.response.data
        
        // Check for detail field (general error)
        if (errorData.detail) {
          errorMessage = errorData.detail
        }
        // Check for non_field_errors (general validation errors)
        else if (errorData.non_field_errors && Array.isArray(errorData.non_field_errors)) {
          errorMessage = errorData.non_field_errors.join(', ')
        }
        // Check for field-specific errors
        else if (typeof errorData === 'object') {
          const fieldErrors: string[] = []
          for (const [field, messages] of Object.entries(errorData)) {
            if (Array.isArray(messages)) {
              fieldErrors.push(`${field}: ${messages.join(', ')}`)
            } else if (typeof messages === 'string') {
              fieldErrors.push(`${field}: ${messages}`)
            }
          }
          if (fieldErrors.length > 0) {
            errorMessage = fieldErrors.join(' | ')
          }
        }
        // Fallback to string if errorData is a string
        else if (typeof errorData === 'string') {
          errorMessage = errorData
        }
      } else if (error?.message) {
        errorMessage = error.message
      }
      
      showToast(errorMessage, { type: 'error', duration: 5000 })
      }
    })
    
    updateAction()
  }

  const handleDelete = (id: number) => {
    // Find the API config to check if it's a backend provider
    const apiToDelete = apis.find(api => api.id === id)
    if (apiToDelete && backendProviderNames.includes(apiToDelete.provider) && !isAdmin) {
      showToast('فقط ادمین می‌تواند تنظیمات بک‌اند را حذف کند', { type: 'error' })
      return
    }

    // Remove blocking confirm; proceed and notify
    showToast('Deleting API configuration...', { type: 'info', duration: 1500 })
    
    const deleteAction = rateLimitClickDelete(async () => {
      try {
        console.log('Deleting API configuration:', id) // Debug log
        
        const response = await deleteAPIConfiguration(id)
        console.log('API configuration delete response:', response) // Debug log
        
        setSuccessMessage('API key deleted successfully')
        setTimeout(() => setSuccessMessage(null), 2500)
        showToast('API key deleted successfully', { type: 'success' })
        await loadAPIs()
        await loadAvailableProviders()
      } catch (error: any) {
        console.error('Error deleting API:', error)
        showToast('Error deleting API configuration: ' + (error?.response?.data?.detail || 'Unknown error'), { type: 'error' })
      }
    })
    
    deleteAction()
  }

  const handleCancel = () => {
    setShowModal(false)
    setEditingApi(null)
    setProvider('twelvedata')
    setApiKey('')
  }

  const handleCheckIP = () => {
    const checkIPAction = rateLimitClickCheckIP(async () => {
      setCheckingIP(true)
      try {
        const response = await checkIPLocation()
        
        if (!response.success) {
          showToast(response.message || 'خطا در بررسی IP. لطفاً دوباره تلاش کنید.', { type: 'error' })
          return
        }
        
        if (response.is_iran) {
          showToast('⚠️ هشدار: IP شما از ایران است. لطفاً از VPN استفاده کنید.', { 
            type: 'error', 
            duration: 8000 
          })
        } else {
          showToast('✓ IP شما از خارج از ایران است. وضعیت مناسب است.', { 
            type: 'success', 
            duration: 5000 
          })
        }
      } catch (error: any) {
        console.error('Error checking IP:', error)
        showToast('خطا در بررسی IP. لطفاً دوباره تلاش کنید.', { type: 'error' })
      } finally {
        setCheckingIP(false)
      }
    })
    
    checkIPAction()
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 mb-6 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      {successMessage && (
        <div className="fixed top-4 right-4 z-50">
          <div className="bg-green-600 text-white px-4 py-2 rounded shadow-lg" style={{ direction: 'rtl', textAlign: 'right', unicodeBidi: 'plaintext' }}>
            {successMessage}
          </div>
        </div>
      )}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">تنظیمات API</h2>
        <div className="flex gap-2">
          <button
            onClick={handleCheckIP}
            disabled={checkingIP}
            className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 text-white rounded-lg transition text-sm font-medium"
          >
            {checkingIP ? 'در حال بررسی...' : 'بررسی IP'}
          </button>
          <button
            onClick={handleTestMT5}
            disabled={testingMT5}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-lg transition text-sm font-medium"
          >
            {testingMT5 ? 'در حال تست...' : 'تست اتصال Meta5'}
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="btn-primary"
          >
            افزودن کلید API
          </button>
        </div>
      </div>

      {/* Available Providers Status */}
      {availableProviders.length > 0 && (
        <div className="bg-green-800 rounded-lg p-4 mb-4">
          <h3 className="text-lg font-semibold text-white mb-2">ارائه‌دهندگان داده‌ی موجود</h3>
          <div className="flex flex-wrap gap-2">
            {availableProviders.map((provider: string) => (
              <span
                key={provider}
                className="px-3 py-1 bg-green-600 text-white rounded-full text-sm"
              >
                {provider}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* API Configurations List */}
      {(() => {
        const tradingApis = apis.filter(api => !backendProviderNames.includes(api.provider))
        const backendApis = isAdmin ? apis.filter(api => backendProviderNames.includes(api.provider)) : []
        const totalApis = tradingApis.length + backendApis.length

        if (totalApis === 0) {
          return (
            <div className="text-gray-400 text-center py-8">
              <p className="text-lg mb-2">هنوز هیچ کلید API تعریف نشده است</p>
              <p className="text-sm">برای شروع، کلید API اضافه کنید</p>
            </div>
          )
        }

        return (
          <div className="space-y-6">
            {/* Trading Data APIs (for all users) */}
            {tradingApis.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-3">کلیدهای API داده‌های معاملاتی</h3>
                <div className="space-y-3">
                  {tradingApis.map((api) => (
                    <div key={api.id} className="bg-gray-700 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-white font-medium text-lg">{api.provider}</h3>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              api.is_active ? 'bg-green-700 text-green-200' : 'bg-gray-600 text-gray-300'
                            }`}>
                              {api.is_active ? 'فعال' : 'غیرفعال'}
                            </span>
                          </div>
                          <div className="text-gray-300 text-sm mb-2">
                            کلید: {api.api_key.substring(0, 10)}...
                          </div>
                          <div className="text-gray-400 text-xs">
                            تاریخ ثبت: {new Date(api.created_at).toLocaleDateString('fa-IR')}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          {(['twelvedata','alphavantage','oanda','metalsapi','financialmodelingprep','gemini','openai','chatgpt','gpt','gpt4','gpt-4','cohere','openrouter','together_ai','deepinfra','groq'].includes(api.provider)) && (
                            <button
                              onClick={() => handleTest(api.id)}
                              disabled={testing === api.id}
                              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg transition text-sm font-medium"
                            >
                              {testing === api.id ? 'در حال تست...' : 'تست' }
                            </button>
                          )}
                          <button
                            onClick={() => handleEdit(api)}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium"
                          >
                            ویرایش
                          </button>
                          <button
                            onClick={() => handleDelete(api.id)}
                            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition text-sm font-medium"
                          >
                            حذف
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Backend/System APIs (admin only) */}
            {isAdmin && backendApis.length > 0 && (
              <div className="border-t border-gray-700 pt-6">
                <h3 className="text-lg font-semibold text-white mb-3">تنظیمات بک‌اند وب‌سایت (فقط ادمین)</h3>
                <div className="space-y-3">
                  {backendApis.map((api) => (
                  <div key={api.id} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-white font-medium text-lg">{api.provider}</h3>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            api.is_active ? 'bg-green-700 text-green-200' : 'bg-gray-600 text-gray-300'
                          }`}>
                            {api.is_active ? 'فعال' : 'غیرفعال'}
                          </span>
                        </div>
                        <div className="text-gray-300 text-sm mb-2">
                          کلید: {api.api_key.substring(0, 10)}...
                        </div>
                        <div className="text-gray-400 text-xs">
                          تاریخ ثبت: {new Date(api.created_at).toLocaleDateString('fa-IR')}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(api)}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium"
                        >
                          ویرایش
                        </button>
                        <button
                          onClick={() => handleDelete(api.id)}
                          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition text-sm font-medium"
                        >
                          حذف
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                </div>
              </div>
            )}
          </div>
        )
      })()}

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="text-xl font-semibold text-white mb-4">{editingApi ? 'ویرایش تنظیمات API' : 'افزودن API جدید'}</h3>
            <form onSubmit={editingApi ? handleUpdate : handleSubmit}>
              <div className="mb-4">
                <label className="label-standard">ارائه‌دهنده</label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="select-standard"
                >
                  {supportedProviders.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-4">
                <label className="label-standard">کلید API</label>
                <input
                  type="text"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="input-standard"
                  placeholder={
                    provider === 'gemini' ? 'کلید API Gemini خود را از aistudio.google.com دریافت کنید' :
                    provider === 'kavenegar' ? 'کلید API Kavenegar خود را از panel.kavenegar.com دریافت کنید' :
                    provider === 'zarinpal' ? 'Merchant ID خود را از zarinpal.com دریافت کنید' :
                    provider === 'nerkh' ? 'کلید API Nerkh.io خود را وارد کنید' :
                    'کلید API خود را وارد کنید'
                  }
                  required
                />
                {provider === 'gemini' && (
                  <div className="mt-2 p-3 bg-blue-900/30 rounded-lg border border-blue-700">
                    <p className="text-blue-300 text-xs">
                      <strong>💡 راهنمای دریافت کلید Gemini از Google AI Studio:</strong>
                      <br />
                      1. به <a href="https://aistudio.google.com" target="_blank" rel="noopener noreferrer" className="underline font-semibold">Google AI Studio</a> بروید
                      <br />
                      2. با حساب Google خود وارد شوید
                      <br />
                      3. در سمت راست صفحه، روی دکمه <strong>"Get API key"</strong> کلیک کنید
                      <br />
                      4. یا از منوی سمت راست، گزینه <strong>"Get API key"</strong> را انتخاب کنید
                      <br />
                      5. یک پروژه جدید بسازید یا پروژه موجود را انتخاب کنید
                      <br />
                      6. کلید API تولید شده را کپی کرده و اینجا وارد کنید
                      <br />
                      <span className="text-yellow-300 mt-1 block">⚠️ توجه: کلید API را در جای امن نگه دارید و به اشتراک نگذارید</span>
                    </p>
                    <div className="mt-3 text-blue-200 text-xs leading-6">
                      <p>
                        برای استفاده رایگان از قابلیت‌های هوش مصنوعی و دریافت داده‌های قیمتی، کافی است در سرویس‌های زیر ثبت‌نام کرده و کلیدهای رایگانشان را در این بخش اضافه کنید:
                      </p>
                      <ul className="list-disc list-inside mt-1 space-y-1">
                        <li>Google AI Studio (برای کلید Gemini)</li>
                        <li>TwelveData، FinancialModelingPrep، MetalsAPI، OANDA و سایر ارائه‌دهندگان داده</li>
                      </ul>
                      <p className="mt-2 text-yellow-200 font-semibold">
                        اگر زمان یا دانش فنی برای انجام این مراحل ندارید، با شارژ حساب به مبلغ <span className="text-white">399,000 تومان</span> می‌توانید نسخه آمادهٔ تحلیل و تست استراتژی به همراه یک ماه پشتیبانی سریع (آنلاین و تلفنی) تهیه کنید تا در کوتاه‌ترین زمان به ساخت مدل‌های هوش مصنوعی اختصاصی برای استراتژی‌های معاملاتی خود برسید.
                      </p>
                    </div>
                  </div>
                )}
                {provider === 'kavenegar' && (
                  <div className="mt-2 p-3 bg-blue-900/30 rounded-lg border border-blue-700">
                    <p className="text-blue-300 text-xs">
                      <strong>💡 راهنمای دریافت کلید Kavenegar:</strong>
                      <br />
                      1. به <a href="https://panel.kavenegar.com" target="_blank" rel="noopener noreferrer" className="underline font-semibold">پنل Kavenegar</a> بروید
                      <br />
                      2. وارد حساب کاربری خود شوید
                      <br />
                      3. از منوی API، کلید API خود را کپی کنید
                      <br />
                      4. کلید را اینجا وارد کنید
                    </p>
                  </div>
                )}
                {provider === 'zarinpal' && (
                  <div className="mt-2 p-3 bg-blue-900/30 rounded-lg border border-blue-700">
                    <p className="text-blue-300 text-xs">
                      <strong>💡 راهنمای دریافت Zarinpal Merchant ID:</strong>
                      <br />
                      1. به <a href="https://zarinpal.com" target="_blank" rel="noopener noreferrer" className="underline font-semibold">Zarinpal</a> بروید
                      <br />
                      2. وارد حساب کاربری خود شوید
                      <br />
                      3. از بخش تنظیمات، Merchant ID خود را کپی کنید
                      <br />
                      4. Merchant ID را اینجا وارد کنید
                    </p>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="flex-1 btn-primary"
                >
                  {editingApi ? 'ویرایش' : 'افزودن'}
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
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