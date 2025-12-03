import { useState, useEffect, Component, ReactNode } from 'react'
import { useSearchParams, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { checkProfileCompletion, updateProfile } from '../api/auth'
import { useToast } from '../components/ToastProvider'
import APIConfigurations from '../components/APIConfigurations'
import APIUsageStats from '../components/APIUsageStats'
import SymbolSelector from '../components/SymbolSelector'
import {
  getWalletBalance,
  chargeWallet,
  updateSystemSettings,
  getUserGoldAPIAccess,
  updateUserGoldAPIAccess,
  createGoldAPIAccessRequest,
  listGoldAPIAccessRequests,
  cancelGoldAPIAccessRequest,
  assignGoldAPIAccessRequest,
  getUserActivityLogs,
  type GoldAPIAccessInfo,
  type GoldAPIAccessRequest,
  type UserActivityLog,
} from '../api/client'
import { useFeatureFlags } from '../context/FeatureFlagsContext'

// Simple Error Boundary component
class ErrorBoundary extends Component<{ children: ReactNode; fallback: ReactNode }> {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback
    }
    return this.props.children
  }
}

export default function Profile() {
  const [email, setEmail] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [nickname, setNickname] = useState('')
  const [loading, setLoading] = useState(false)
  const [editingProfile, setEditingProfile] = useState(false)
  const [walletBalance, setWalletBalance] = useState<number>(0)
  const [walletLoading, setWalletLoading] = useState(false)
  const [charging, setCharging] = useState(false)
  const { user, checkAuthentication, isAdmin } = useAuth()
  const { showToast } = useToast()
  const [searchParams, setSearchParams] = useSearchParams()
  const { liveTradingEnabled, isLoading: featureFlagsLoading, reload: reloadFeatureFlags } = useFeatureFlags()
  const [toggleLiveTradingLoading, setToggleLiveTradingLoading] = useState(false)
  const [goldAccess, setGoldAccess] = useState<GoldAPIAccessInfo | null>(null)
  const [goldAccessLoading, setGoldAccessLoading] = useState(false)
  const [goldProviderInput, setGoldProviderInput] = useState('')
  const [goldKeyInput, setGoldKeyInput] = useState('')
  const [goldNotesInput, setGoldNotesInput] = useState('')
  const [updatingGoldAccess, setUpdatingGoldAccess] = useState(false)
  const [creatingGoldRequest, setCreatingGoldRequest] = useState(false)
  const [goldRequests, setGoldRequests] = useState<GoldAPIAccessRequest[]>([])
  const [goldRequestsLoading, setGoldRequestsLoading] = useState(false)
  const [assigningRequestId, setAssigningRequestId] = useState<number | null>(null)
  const [assignProvider, setAssignProvider] = useState('')
  const [assignApiKey, setAssignApiKey] = useState('')
  const [assignNotes, setAssignNotes] = useState('')
  const [assignIsActive, setAssignIsActive] = useState(true)
  const [assignAllowMt5, setAssignAllowMt5] = useState(false)
  const [assignSubmitting, setAssignSubmitting] = useState(false)
  const [activityLogs, setActivityLogs] = useState<UserActivityLog[]>([])
  const [activityLogsLoading, setActivityLogsLoading] = useState(false)
  const navigate = useNavigate()

  const liveTradingStatusLabel = featureFlagsLoading
    ? 'در حال بارگذاری...'
    : liveTradingEnabled
    ? 'فعال'
    : 'مخفی'

  const liveTradingStatusClasses = featureFlagsLoading
    ? 'bg-gray-700 text-gray-300'
    : liveTradingEnabled
    ? 'bg-green-900 text-green-300'
    : 'bg-red-900 text-red-300'
  const rawProfilePhone =
    (phoneNumber && phoneNumber.trim()) ||
    (user?.phone_number && user.phone_number.trim()) ||
    ''
  const profilePhoneDisplay = rawProfilePhone || ''
  const normalizedProfilePhone = profilePhoneDisplay.replace(/\D/g, '')
  const normalizedUsername = (user?.username || '').replace(/\D/g, '')
  const usernameLooksLikePhone =
    normalizedProfilePhone.length > 0 &&
    normalizedProfilePhone === normalizedUsername &&
    normalizedProfilePhone.length >= 8
  const profileNameFallback =
    user?.nickname?.trim() ||
    (email && email.trim()) ||
    (user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}`.trim() : '') ||
    'نامشخص'
  const profileUsernameDisplay = usernameLooksLikePhone
    ? profileNameFallback
    : user?.username?.trim() || profileNameFallback
  const GOLD_API_ASSISTANCE_PRICE = 450000
  const goldRequestStatusLabels: Record<string, string> = {
    pending_payment: 'در انتظار پرداخت',
    awaiting_admin: 'در انتظار ادمین',
    completed: 'تکمیل شده',
    cancelled: 'لغو شده',
  }
  const activeGoldRequest = goldRequests.find((req) => ['pending_payment', 'awaiting_admin'].includes(req.status))
  const hasAdminAssignedApi = Boolean(goldAccess?.assigned_by_admin && goldAccess?.has_credentials)
  const isAdminUser = isAdmin === true || user?.is_staff || user?.is_superuser
  const hasMt5Delegate = Boolean(goldAccess?.allow_mt5_access)
  const goldAccessStatusText = goldAccess?.has_credentials
    ? hasAdminAssignedApi
      ? 'کلید API توسط ادمین ثبت شده است'
      : 'کلید API توسط شما ثبت شده و فعال است'
    : 'کلید API فعالی ثبت نشده است'
  const canCreateGoldRequest = !activeGoldRequest

  // Load profile and wallet when component mounts or user becomes available
  useEffect(() => {
    let isMounted = true
    let timeoutId: number | null = null
    
    const initializeProfile = async () => {
      if (!isMounted) return
      
      try {
        if (user?.id) {
          // User is available, load profile and wallet
          try {
            await loadProfile()
          } catch (profileError) {
            console.error('Error loading profile:', profileError)
          }
          
          if (isMounted) {
            try {
              await loadWalletBalance()
            } catch (walletError) {
              console.error('Error loading wallet:', walletError)
            }
            if (isMounted) {
              try {
                await Promise.all([loadGoldAccess(), loadGoldRequests(), loadActivityLogs()])
              } catch (goldError) {
                console.error('Error loading gold access data:', goldError)
              }
            }
          }
        } else {
          // If user is not loaded, wait a bit then check authentication
          timeoutId = setTimeout(async () => {
            if (isMounted) {
              try {
                await checkAuthentication()
                if (isMounted && user?.id) {
                  try {
                    await loadProfile()
                  } catch (profileError) {
                    console.error('Error loading profile after auth:', profileError)
                  }
                  if (isMounted) {
                    try {
                      await loadWalletBalance()
                    } catch (walletError) {
                      console.error('Error loading wallet after auth:', walletError)
                    }
                  }
                  if (isMounted) {
                    try {
                      await Promise.all([loadGoldAccess(), loadGoldRequests(), loadActivityLogs()])
                    } catch (goldError) {
                      console.error('Error loading gold access after auth:', goldError)
                    }
                  }
                }
              } catch (error) {
                console.error('Error checking authentication:', error)
              }
            }
          }, 100) // Small delay to avoid race conditions
        }
      } catch (error) {
        console.error('Error initializing profile:', error)
      }
    }
    
    initializeProfile()
    
    return () => {
      isMounted = false
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]) // Run when user id changes (user loaded or changed)

  // Handle payment callback from Zarinpal
  useEffect(() => {
    const paymentSuccess = searchParams.get('payment_success')
    const paymentError = searchParams.get('payment_error')
    const goldPayment = searchParams.get('gold_api_payment')

    if (paymentSuccess === '1') {
      showToast('پرداخت با موفقیت انجام شد! حساب شما شارژ شد.', { type: 'success', duration: 5000 })
      // Remove query params from URL
      searchParams.delete('payment_success')
      searchParams.delete('transaction_id')
      setSearchParams(searchParams, { replace: true })
      // Refresh wallet balance
      loadWalletBalance()
      loadGoldRequests()
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

    if (goldPayment === '1') {
      showToast('پرداخت شما ثبت شد. درخواست برای ادمین ارسال گردید.', { type: 'success', duration: 6000 })
      searchParams.delete('gold_api_payment')
      searchParams.delete('transaction_id')
      setSearchParams(searchParams, { replace: true })
      loadGoldRequests()
    }
  }, [searchParams, setSearchParams, showToast])

  const loadProfile = async () => {
    try {
      // Always load from user object first (from auth context)
      if (user) {
        // Pre-fill existing values from user object
        if (user.email && !user.email.endsWith('@example.com')) {
          setEmail(user.email)
        } else {
          setEmail('')
        }
        if (user.phone_number && user.phone_number.startsWith('09')) {
          setPhoneNumber(user.phone_number)
        } else {
          setPhoneNumber(user.phone_number || '')
        }
        setNickname(user.nickname || '')
      }
      
      // Also check profile completion status (don't call checkAuthentication here to avoid loops)
      try {
        const response = await checkProfileCompletion()
        if (response.success) {
          // Profile check successful, data already loaded from user object above
        }
      } catch (profileError) {
        console.error('Error checking profile completion:', profileError)
        // Continue with user data if available
      }
    } catch (error) {
      console.error('Error loading profile:', error)
      // Even on error, try to use user data if available
      if (user) {
        if (user.email && !user.email.endsWith('@example.com')) {
          setEmail(user.email)
        }
        if (user.phone_number && user.phone_number.startsWith('09')) {
          setPhoneNumber(user.phone_number)
        }
        setNickname(user.nickname || '')
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!nickname) {
      showToast('لطفا نیک‌نیم خود را وارد کنید', { type: 'error' })
      return
    }

    if (!email && !phoneNumber) {
      showToast('لطفا حداقل ایمیل یا شماره موبایل را وارد کنید', { type: 'error' })
      return
    }

    // Validate email if provided
    if (email && (!email.includes('@') || !email.includes('.'))) {
      showToast('ایمیل معتبر نیست', { type: 'error' })
      return
    }

    // Validate phone if provided
    if (phoneNumber && (!phoneNumber.match(/^09\d{9}$/))) {
      showToast('شماره موبایل باید 11 رقم و با 09 شروع شود', { type: 'error' })
      return
    }

    if (nickname.length < 3) {
      showToast('نیک‌نیم باید حداقل ۳ کاراکتر باشد', { type: 'error' })
      return
    }

    setLoading(true)
    try {
      const response = await updateProfile(email || undefined, undefined, undefined, nickname)
      if (response.success) {
        showToast('پروفایل با موفقیت به‌روزرسانی شد', { type: 'success' })
        // Refresh user data
        await checkAuthentication()
        setEditingProfile(false)
        await loadProfile()
      } else {
        if (response.errors) {
          const errorMessages = Object.values(response.errors).filter(Boolean).join(' و ')
          showToast(errorMessages || response.message || 'خطا در به‌روزرسانی پروفایل', { type: 'error' })
        } else {
          showToast(response.message || 'خطا در به‌روزرسانی پروفایل', { type: 'error' })
        }
      }
    } catch (error: any) {
      console.error('Error updating profile:', error)
      showToast(error.response?.data?.message || 'خطا در به‌روزرسانی پروفایل', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    loadProfile()
    setEditingProfile(false)
  }

  const handleRequestPhoneChange = () => {
    navigate('/tickets', {
      state: {
        createTicket: {
          title: 'درخواست تغییر شماره موبایل',
          description: `سلام، لطفاً شماره موبایل حساب من را تغییر دهید.\nشماره فعلی: ${profilePhoneDisplay || 'ثبت نشده'}\nشماره جدید: [شماره جدید را وارد کنید]`,
          category: 'other',
          priority: 'medium',
        },
      },
    })
  }

  const loadWalletBalance = async () => {
    try {
      setWalletLoading(true)
      const response = await getWalletBalance()
      if (response?.data?.balance !== undefined) {
        setWalletBalance(response.data.balance)
      }
    } catch (error) {
      console.error('Error loading wallet balance:', error)
      // Set default balance on error
      setWalletBalance(0)
    } finally {
      setWalletLoading(false)
    }
  }

  const loadGoldAccess = async () => {
    try {
      setGoldAccessLoading(true)
      const response = await getUserGoldAPIAccess()
      const data = response.data as GoldAPIAccessInfo
      setGoldAccess(data)
      setGoldProviderInput(data?.provider || '')
      setGoldKeyInput(data?.api_key || '')
      setGoldNotesInput(data?.notes || '')
    } catch (error) {
      console.error('Error loading gold API access:', error)
      setGoldAccess(null)
    } finally {
      setGoldAccessLoading(false)
    }
  }

  const loadGoldRequests = async () => {
    try {
      setGoldRequestsLoading(true)
      const response = await listGoldAPIAccessRequests()
      const payload = response.data as any
      const items: GoldAPIAccessRequest[] = Array.isArray(payload) ? payload : payload?.results || []
      items.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      setGoldRequests(items)
    } catch (error) {
      console.error('Error loading gold API requests:', error)
      setGoldRequests([])
    } finally {
      setGoldRequestsLoading(false)
    }
  }

  const loadActivityLogs = async () => {
    try {
      setActivityLogsLoading(true)
      const response = await getUserActivityLogs(50, 0)
      if (response.data.success) {
        setActivityLogs(response.data.logs)
      }
    } catch (error) {
      console.error('Error loading activity logs:', error)
      setActivityLogs([])
    } finally {
      setActivityLogsLoading(false)
    }
  }

  const handleUpdateGoldAccess = async () => {
    try {
      setUpdatingGoldAccess(true)
      const response = await updateUserGoldAPIAccess({
        provider: goldProviderInput.trim(),
        api_key: goldKeyInput.trim(),
        notes: goldNotesInput.trim(),
      })
      const data = response.data as GoldAPIAccessInfo
      setGoldAccess(data)
      showToast('تنظیمات API طلا ذخیره شد', { type: 'success' })
      await loadGoldAccess()
    } catch (error: any) {
      console.error('Error updating gold API access:', error)
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        'خطا در ذخیره تنظیمات API طلا'
      showToast(message, { type: 'error' })
    } finally {
      setUpdatingGoldAccess(false)
    }
  }

  const handleCreateGoldRequest = async () => {
    if (creatingGoldRequest) return
    try {
      setCreatingGoldRequest(true)
      const response = await createGoldAPIAccessRequest({
        preferred_provider: goldProviderInput.trim() || undefined,
        user_notes: goldNotesInput.trim() || undefined,
      })
      const data = response.data as GoldAPIAccessRequest & { payment_url?: string }
      showToast('درخواست ثبت شد. در حال انتقال به درگاه پرداخت...', { type: 'info' })
      await loadGoldRequests()
      if (data.payment_url) {
        window.location.href = data.payment_url
      }
    } catch (error: any) {
      console.error('Error creating gold API request:', error)
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        'خطا در ایجاد درخواست API طلا'
      showToast(message, { type: 'error' })
    } finally {
      setCreatingGoldRequest(false)
    }
  }

  const handleCancelGoldRequest = async (requestId: number) => {
    try {
      await cancelGoldAPIAccessRequest(requestId)
      showToast('درخواست با موفقیت لغو شد', { type: 'success' })
      await loadGoldRequests()
    } catch (error: any) {
      console.error('Error cancelling gold API request:', error)
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        'خطا در لغو درخواست'
      showToast(message, { type: 'error' })
    }
  }

  const handleAssignRequest = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!assigningRequestId) {
      showToast('هیچ درخواستی انتخاب نشده است', { type: 'warning' })
      return
    }
    if (!assignProvider.trim() || !assignApiKey.trim()) {
      showToast('لطفاً ارائه‌دهنده و کلید API را وارد کنید', { type: 'error' })
      return
    }
    try {
      setAssignSubmitting(true)
      await assignGoldAPIAccessRequest(assigningRequestId, {
        provider: assignProvider.trim(),
        api_key: assignApiKey.trim(),
        admin_notes: assignNotes.trim() || undefined,
        is_active: assignIsActive,
        allow_mt5_access: assignAllowMt5,
      })
      showToast('اطلاعات API برای کاربر ثبت شد', { type: 'success' })
      setAssigningRequestId(null)
      setAssignProvider('')
      setAssignApiKey('')
      setAssignNotes('')
      setAssignIsActive(true)
      setAssignAllowMt5(false)
      await Promise.all([loadGoldRequests(), loadGoldAccess()])
    } catch (error: any) {
      console.error('Error assigning gold API request:', error)
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        'خطا در ثبت اطلاعات'
      showToast(message, { type: 'error' })
    } finally {
      setAssignSubmitting(false)
    }
  }

  const startAssignRequest = (request: GoldAPIAccessRequest) => {
    setAssigningRequestId(request.id)
    setAssignProvider(request.assigned_provider || request.preferred_provider || '')
    setAssignApiKey(request.assigned_api_key || '')
    setAssignNotes(request.admin_notes || '')
    setAssignIsActive(true)
    setAssignAllowMt5(Boolean(request.user_allow_mt5_access))
  }

  const handleCharge = async (amount: number) => {
    if (!amount) return

    try {
      setCharging(true)
      const response = await chargeWallet(amount)
      if (response.data.status === 'success' && response.data.payment_url) {
        // Redirect to Zarinpal payment page
        window.location.href = response.data.payment_url
      } else {
        showToast(response.data.error || 'خطا در ایجاد درخواست پرداخت', { type: 'error' })
      }
    } catch (error: any) {
      console.error('Error charging wallet:', error)
      showToast(error.response?.data?.error || 'خطا در ایجاد درخواست پرداخت', { type: 'error' })
    } finally {
      setCharging(false)
    }
  }

  const handleToggleLiveTradingVisibility = async () => {
    if (featureFlagsLoading) {
      return
    }

    try {
      setToggleLiveTradingLoading(true)
      const nextValue = !liveTradingEnabled
      await updateSystemSettings({ live_trading_enabled: nextValue })
      await reloadFeatureFlags()
      showToast(
        nextValue
          ? 'بخش معاملات زنده برای کاربران فعال شد'
          : 'بخش معاملات زنده برای کاربران مخفی شد',
        { type: 'success' }
      )
    } catch (error: any) {
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        'خطا در به‌روزرسانی تنظیمات سیستم'
      showToast(message, { type: 'error' })
    } finally {
      setToggleLiveTradingLoading(false)
    }
  }

  // Debug logging
  useEffect(() => {
    console.log('Profile component - user:', user)
    console.log('Profile component - user.is_staff:', user?.is_staff)
    console.log('Profile component - user.is_superuser:', user?.is_superuser)
    console.log('Profile component - isAdmin:', isAdmin)
    console.log('Profile component - isAdmin type:', typeof isAdmin)
    console.log('Profile component - email:', email)
    console.log('Profile component - phoneNumber:', phoneNumber)
    console.log('Profile component - nickname:', nickname)
  }, [user, isAdmin, email, phoneNumber, nickname])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">پروفایل کاربر</h1>
        <p className="text-gray-400">مدیریت اطلاعات شخصی و تنظیمات API</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Profile Information */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-white">اطلاعات شخصی</h2>
            {!editingProfile && (
              <button
                onClick={() => setEditingProfile(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium"
              >
                ویرایش
              </button>
            )}
          </div>

          {editingProfile ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                  ایمیل
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="example@email.com"
                  className="appearance-none relative block w-full px-3 py-3 border border-gray-600 placeholder-gray-500 text-white bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  dir="ltr"
                  disabled={loading}
                />
                {user?.email && user.email.endsWith('@example.com') && (
                  <p className="mt-1 text-xs text-yellow-400">
                    لطفا ایمیل معتبر خود را وارد کنید
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="nickname" className="block text-sm font-medium text-gray-300 mb-2">
                  نیک‌نیم
                </label>
                <input
                  id="nickname"
                  name="nickname"
                  type="text"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value.slice(0, 50))}
                  placeholder="مثال: trader_ali"
                  className="appearance-none relative block w-full px-3 py-3 border border-gray-600 placeholder-gray-500 text-white bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loading}
                />
                {nickname.length > 0 && nickname.length < 3 && (
                  <p className="mt-1 text-xs text-yellow-400">
                    نیک‌نیم باید حداقل ۳ کاراکتر باشد
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-300 mb-2">
                  شماره موبایل
                </label>
                <div
                  className="appearance-none relative block w-full px-3 py-3 border border-gray-600 text-white bg-gray-700 rounded-lg"
                  dir="ltr"
                >
                  {profilePhoneDisplay || <span className="text-gray-400">ثبت نشده</span>}
                </div>
                <p className="mt-2 text-xs text-gray-400">
                  برای تغییر شماره موبایل باید تیکت پشتیبانی ثبت کنید.
                </p>
                <button
                  type="button"
                  onClick={handleRequestPhoneChange}
                  className="mt-3 inline-flex items-center justify-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition text-sm font-medium"
                >
                  ثبت درخواست تغییر شماره
                </button>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={loading || (!email && !phoneNumber) || nickname.length < 3}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition text-sm font-medium"
                >
                  {loading ? 'در حال ذخیره...' : 'ذخیره'}
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition text-sm font-medium"
                >
                  انصراف
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  نام کاربری
                </label>
                <p className="text-white text-lg">
                  {profileUsernameDisplay}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  ایمیل
                </label>
                <p className="text-white text-lg">
                  {email || (user?.email && !user.email.endsWith('@example.com') ? user.email : 'تعریف نشده')}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  نیک‌نیم
                </label>
                <p className="text-white text-lg">
                  {nickname || user?.nickname || 'تعریف نشده'}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  نقش کاربر
                </label>
                <p className="text-white text-lg">
                  {isAdmin ? 'ادمین' : 'کاربر عادی'}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  شماره موبایل
                </label>
                <p className="text-sm text-gray-500">
                  شماره موبایل در این بخش نمایش داده نمی‌شود. برای تغییر آن تیکت پشتیبانی ثبت کنید.
                </p>
                <button
                  type="button"
                  onClick={handleRequestPhoneChange}
                  className="mt-3 inline-flex items-center justify-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition text-sm font-medium"
                >
                  ثبت درخواست تغییر شماره
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Trading Settings */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">تنظیمات معاملاتی</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                نماد معاملاتی
              </label>
              <div className="flex items-center gap-2">
                <SymbolSelector />
              </div>
              <p className="mt-2 text-xs text-gray-400">
                نماد انتخابی برای معاملات و تست‌های استراتژی استفاده می‌شود
              </p>
            </div>
          </div>
        </div>

        {/* Gold API Access */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-2">دسترسی به قیمت لحظه‌ای طلا</h2>
          <p className="text-sm text-gray-400 mb-6">
            دریافت قیمت طلا فقط برای ادمین فعال است. برای اجرای بک‌تست‌ها لازم است کلید API شخصی خود را ثبت کنید یا از تیم پشتیبانی بخواهید این کار را برای شما انجام دهد.
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-gray-900 rounded-lg border border-gray-700 p-5">
              <h3 className="text-lg font-semibold text-white mb-3">تنظیمات API شخصی</h3>
              {goldAccessLoading ? (
                <p className="text-gray-400 text-sm">در حال بارگذاری اطلاعات...</p>
              ) : (
                <div className="space-y-4">
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-300">{goldAccessStatusText}</div>
                    {goldAccess?.provider && (
                      <div className="text-xs text-gray-500 mt-2">
                        <span className="font-semibold text-gray-300">ارائه‌دهنده فعلی:</span>{' '}
                        {goldAccess.provider}
                      </div>
                    )}
                    {goldAccess?.source && (
                      <div className="text-xs text-gray-500 mt-1">
                        <span className="font-semibold text-gray-300">منبع ثبت:</span>{' '}
                        {goldAccess.source === 'admin' ? 'ادمین' : 'کاربر'}
                      </div>
                    )}
                    {goldAccess?.updated_at && (
                      <div className="text-xs text-gray-500 mt-1">
                        <span className="font-semibold text-gray-300">آخرین بروزرسانی:</span>{' '}
                        {new Date(goldAccess.updated_at).toLocaleString('fa-IR')}
                      </div>
                    )}
                    <div className="text-xs text-gray-500 mt-2 flex items-center gap-2">
                      <span className="font-semibold text-gray-300">دسترسی متاتریدر 5:</span>
                      <span
                        className={`px-2 py-0.5 rounded-full ${
                          hasMt5Delegate
                            ? 'bg-green-900 text-green-300'
                            : 'bg-gray-700 text-gray-300'
                        }`}
                      >
                        {hasMt5Delegate ? 'فعال' : 'غیرفعال'}
                      </span>
                    </div>
                  </div>

                  {hasMt5Delegate && (
                    <div className="bg-green-900/40 border border-green-700 text-green-200 text-xs rounded-lg p-3">
                      دسترسی دریافت قیمت از MetaTrader 5 برای شما فعال است. در صورت بروز مشکل با پشتیبانی تماس بگیرید.
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      ارائه‌دهنده API
                    </label>
                    <input
                      value={goldProviderInput}
                      onChange={(e) => setGoldProviderInput(e.target.value)}
                      placeholder="مثال: TwelveData"
                      className="w-full px-3 py-3 rounded-lg bg-gray-700 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      کلید API
                    </label>
                    <input
                      value={goldKeyInput}
                      onChange={(e) => setGoldKeyInput(e.target.value)}
                      placeholder="کلید را وارد کنید یا برای حذف خالی بگذارید"
                      className="w-full px-3 py-3 rounded-lg bg-gray-700 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      dir="ltr"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      یادداشت (اختیاری)
                    </label>
                    <textarea
                      value={goldNotesInput}
                      onChange={(e) => setGoldNotesInput(e.target.value)}
                      placeholder="یادداشت یا توضیح برای آینده"
                      className="w-full px-3 py-3 rounded-lg bg-gray-700 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={3}
                    />
                  </div>
                  <button
                    onClick={handleUpdateGoldAccess}
                    disabled={updatingGoldAccess}
                    className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition text-sm font-medium"
                  >
                    {updatingGoldAccess ? 'در حال ذخیره...' : 'ذخیره تنظیمات'}
                  </button>
                </div>
              )}
            </div>

            <div className="bg-gray-900 rounded-lg border border-gray-700 p-5">
              <h3 className="text-lg font-semibold text-white mb-3">درخواست کمک از تیم پشتیبانی</h3>
              <p className="text-sm text-gray-400 mb-4">
                اگر زمان کافی برای ثبت ‌نام در سرویس‌های ارائه‌دهنده API ندارید، می‌توانید با پرداخت هزینه زیر درخواست خود را ثبت کنید تا تیم پشتیبانی یک API معتبر برای شما تهیه و در حساب شما ثبت کند.
              </p>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">هزینه سرویس</span>
                  <span className="text-lg font-semibold text-green-400">
                    {GOLD_API_ASSISTANCE_PRICE.toLocaleString('fa-IR')} تومان
                  </span>
                </div>
                <div className="mt-3 text-xs text-gray-400">
                  <span className="font-semibold text-gray-300">راهنما:</span>{' '}
                  <Link to="/guides/free-gold-api" className="text-blue-400 hover:text-blue-300">
                    آموزش دریافت API رایگان
                  </Link>
                </div>
              </div>

              <div className="space-y-3">
                {goldRequestsLoading ? (
                  <p className="text-gray-400 text-sm">در حال بررسی وضعیت درخواست‌ها...</p>
                ) : activeGoldRequest ? (
                  <div className="bg-gray-800 border border-yellow-600 rounded-lg p-4 text-sm text-gray-200">
                    <div className="font-semibold text-yellow-400 mb-1">درخواست فعال دارید</div>
                    <div>وضعیت: {goldRequestStatusLabels[activeGoldRequest.status] || activeGoldRequest.status_display}</div>
                    {activeGoldRequest.status === 'pending_payment' && (
                      <button
                        onClick={() => handleCancelGoldRequest(activeGoldRequest.id)}
                        className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-medium transition"
                      >
                        لغو درخواست
                      </button>
                    )}
                    {activeGoldRequest.status === 'awaiting_admin' && (
                      <p className="mt-2 text-xs text-gray-400">
                        درخواست شما ثبت شده است. پس از ثبت API توسط ادمین، از طریق همین بخش مطلع خواهید شد.
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-gray-400">
                    در حال حاضر درخواست فعالی ندارید. برای ثبت درخواست جدید روی دکمه زیر کلیک کنید.
                  </div>
                )}

                <button
                  onClick={handleCreateGoldRequest}
                  disabled={!canCreateGoldRequest || creatingGoldRequest}
                  className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition text-sm font-medium"
                >
                  {creatingGoldRequest ? 'در حال هدایت...' : 'ثبت درخواست و انتقال به درگاه پرداخت'}
                </button>
              </div>

              {goldRequests.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-semibold text-white mb-2">تاریخچه درخواست‌ها</h4>
                  <div className="max-h-40 overflow-y-auto space-y-3 pr-1">
                    {goldRequests.map((request) => (
                      <div key={request.id} className="bg-gray-800 border border-gray-700 rounded-lg p-3 text-xs text-gray-300">
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-semibold text-white">درخواست #{request.id}</span>
                          <span className="text-yellow-300">
                            {goldRequestStatusLabels[request.status] || request.status_display}
                          </span>
                        </div>
                        <div>ثبت: {new Date(request.created_at).toLocaleString('fa-IR')}</div>
                        {request.payment_confirmed_at && (
                          <div>تایید پرداخت: {new Date(request.payment_confirmed_at).toLocaleString('fa-IR')}</div>
                        )}
                        {request.assigned_provider && (
                          <div className="mt-1 text-green-400">
                            ارائه‌دهنده اختصاص داده شده: {request.assigned_provider}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Wallet and Credit */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">کیف پول و اعتبار</h2>
          <div className="space-y-6">
            {/* Wallet Balance */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                موجودی کیف پول
              </label>
              {walletLoading ? (
                <p className="text-white text-lg">در حال بارگذاری...</p>
              ) : (
                <p className="text-white text-2xl font-bold">
                  {walletBalance.toLocaleString('fa-IR')} تومان
                </p>
              )}
            </div>

            {/* Payment Methods Description */}
            <div className="pt-4 border-t border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-2">روش‌های شارژ کیف پول</h3>
              <p className="text-gray-400 text-sm mb-6">
                برای شارژ کیف پول خود می‌توانید از دو روش زیر استفاده کنید. روش کارت به کارت سریع‌تر و بدون کارمزد است.
              </p>
          
              <div className="space-y-6">
                {/* Method 1: Card to Card */}
                <div className="bg-gray-700 rounded-lg p-4 border-r-4 border-green-500">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="bg-green-500 text-white text-xs font-bold px-2 py-1 rounded">اولویت اول</span>
                        <h3 className="text-lg font-semibold text-white">پرداخت کارت به کارت</h3>
                      </div>
                      <p className="text-gray-300 text-sm mb-4">
                        سریع‌ترین روش پرداخت بدون کارمزد. پس از واریز مبلغ، رسید پرداخت را از طریق تلگرام ارسال کنید تا حساب شما در کمتر از ۱۰ دقیقه شارژ شود.
                      </p>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-800 rounded-lg p-4">
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        شماره کارت بانک پاسارگاد
                      </label>
                      <div className="space-y-2">
                        <p className="text-gray-300 text-sm">
                          به نام: <span className="font-semibold text-white">امیر اویرا</span>
                        </p>
                        <div className="flex items-center gap-2">
                          <p className="text-white text-lg font-mono font-semibold">
                            5022-2913-0084-2760
                          </p>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText('5022291300842760')
                              showToast('شماره کارت کپی شد', { type: 'success' })
                            }}
                            className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-white rounded transition"
                            title="کپی شماره کارت"
                          >
                            کپی
                          </button>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-gray-800 rounded-lg p-4">
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        ارسال رسید پرداخت
                      </label>
                      <p className="text-gray-400 text-xs mb-3">
                        پس از واریز مبلغ، تصویر رسید پرداخت را از طریق تلگرام ارسال کنید.
                      </p>
                      <a
                        href="https://t.me/avxsupport"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium"
                      >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.174 1.586-.927 5.442-1.31 7.22-.15.685-.445.913-.731.877-.384-.045-1.05-.206-1.63-.402-.645-.206-1.13-.32-1.828-.513-.72-.206-1.27-.319-1.97.319-.595.536-2.31 2.233-3.385 3.014-.38.319-.647.479-1.015.479-.67-.045-1.22-.492-1.89-.96-.693-.48-1.245-1.002-1.89-1.68-.65-.685-2.29-2.01-2.31-2.34-.02-.11.16-.32.445-.536 1.83-1.61 3.05-2.73 3.89-3.27.17-.11.38-.21.595-.21.32 0 .52.15.7.493 1.15 2.19 2.54 4.24 3.85 4.24.32 0 .64-.11.87-.32.35-.32.64-.7.93-1.08.6-.75 1.33-1.68 2.15-2.71.19-.24.38-.48.64-.48.15 0 .32.08.41.24.18.32.15.7.11 1.08z"/>
                        </svg>
                        ارسال رسید در تلگرام
                      </a>
                    </div>
                  </div>
                </div>

                {/* Method 2: Zarinpal */}
                <div className="bg-gray-700 rounded-lg p-4 border-r-4 border-blue-500">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="bg-blue-500 text-white text-xs font-bold px-2 py-1 rounded">اولویت دوم</span>
                        <h3 className="text-lg font-semibold text-white">پرداخت آنلاین زرین‌پال</h3>
                      </div>
                      <p className="text-gray-300 text-sm mb-4">
                        پرداخت آنلاین و امن از طریق درگاه پرداخت زرین‌پال. پس از تکمیل پرداخت، حساب شما به صورت خودکار شارژ می‌شود.
                      </p>
                    </div>
                  </div>
                  
                  <div className="bg-gray-800 rounded-lg p-4">
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      شارژ کیف پول از طریق زرین‌پال
                    </label>
                    <div className="grid grid-cols-3 gap-3 mb-3">
                      <button
                        onClick={() => handleCharge(150000)}
                        disabled={charging}
                        className="px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition font-medium text-sm"
                      >
                        {charging ? '...' : '150,000 تومان'}
                      </button>
                      <button
                        onClick={() => handleCharge(300000)}
                        disabled={charging}
                        className="px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition font-medium text-sm"
                      >
                        {charging ? '...' : '300,000 تومان'}
                      </button>
                      <button
                        onClick={() => handleCharge(900000)}
                        disabled={charging}
                        className="px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition font-medium text-sm"
                      >
                        {charging ? '...' : '900,000 تومان'}
                      </button>
                    </div>
                    <p className="text-gray-400 text-xs mb-3">
                      با کلیک روی دکمه‌ها به صفحه پرداخت زرین‌پال هدایت می‌شوید.
                    </p>
                    <div className="flex items-center gap-2 text-gray-300 text-sm">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>پرداخت از طریق تمامی کارت‌های عضو شتاب</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* API Settings */}
        <div className="bg-gray-800 rounded-lg overflow-hidden">
          <ErrorBoundary fallback={<div className="p-6 text-red-400">خطا در بارگذاری تنظیمات API</div>}>
            <APIConfigurations />
          </ErrorBoundary>
        </div>

        {isAdminUser && (
          <div className="bg-gray-800 rounded-lg overflow-hidden mt-6 p-6 space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-white mb-2">مدیریت درخواست‌های API طلا</h2>
              <p className="text-sm text-gray-400">
                درخواست‌های کاربران برای دریافت API اختصاصی را در این بخش مشاهده و پس از تهیه کلید، آن را ثبت کنید. پس از ثبت، کاربر بلافاصله امکان استفاده خواهد داشت.
              </p>
            </div>

            <div className="overflow-x-auto">
              {goldRequestsLoading ? (
                <p className="text-gray-400 text-sm">در حال بارگذاری درخواست‌ها...</p>
              ) : goldRequests.length === 0 ? (
                <p className="text-gray-400 text-sm">درخواستی ثبت نشده است.</p>
              ) : (
                <table className="min-w-full divide-y divide-gray-700 text-sm">
                  <thead className="bg-gray-900">
                    <tr>
                      <th className="px-3 py-2 text-right text-gray-300 font-medium">#</th>
                      <th className="px-3 py-2 text-right text-gray-300 font-medium">کاربر</th>
                      <th className="px-3 py-2 text-right text-gray-300 font-medium">وضعیت</th>
                      <th className="px-3 py-2 text-right text-gray-300 font-medium">تاریخ ثبت</th>
                      <th className="px-3 py-2 text-right text-gray-300 font-medium">پرداخت</th>
                      <th className="px-3 py-2 text-right text-gray-300 font-medium">اقدامات</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {goldRequests.map((request) => (
                      <tr key={request.id} className="bg-gray-800">
                        <td className="px-3 py-2 text-gray-200">#{request.id}</td>
                        <td className="px-3 py-2 text-gray-300">
                          <div className="font-semibold text-white">{request.username || 'نامشخص'}</div>
                          {request.user_phone && <div className="text-xs text-gray-400 mt-1">{request.user_phone}</div>}
                          {request.user_email && <div className="text-xs text-gray-500 mt-1">{request.user_email}</div>}
                        </td>
                        <td className="px-3 py-2 text-gray-300">
                          <div>{goldRequestStatusLabels[request.status] || request.status_display}</div>
                          {request.preferred_provider && (
                            <div className="text-xs text-gray-400 mt-1">ترجیح کاربر: {request.preferred_provider}</div>
                          )}
                          {request.assigned_provider && (
                            <div className="text-xs text-green-400 mt-1">ثبت شده: {request.assigned_provider}</div>
                          )}
                          {request.user_allow_mt5_access && (
                            <div className="inline-flex items-center gap-1 text-[11px] text-green-300 bg-green-900/30 border border-green-700 rounded-full px-2 py-0.5 mt-2">
                              <span className="h-1.5 w-1.5 rounded-full bg-green-400" />
                              دسترسی MT5 فعال
                            </div>
                          )}
                        </td>
                        <td className="px-3 py-2 text-gray-300">
                          <div>{new Date(request.created_at).toLocaleString('fa-IR')}</div>
                        </td>
                        <td className="px-3 py-2 text-gray-300">
                          {request.payment_confirmed_at ? (
                            <div className="text-green-400">
                              تایید شد
                              <div className="text-xs text-gray-400">
                                {new Date(request.payment_confirmed_at).toLocaleString('fa-IR')}
                              </div>
                            </div>
                          ) : (
                            <div className="text-yellow-400">در انتظار پرداخت</div>
                          )}
                        </td>
                        <td className="px-3 py-2">
                          {request.status === 'awaiting_admin' ? (
                            <button
                              onClick={() => startAssignRequest(request)}
                              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg transition"
                            >
                              ثبت API
                            </button>
                          ) : request.status === 'completed' ? (
                            <span className="text-xs text-green-400">تکمیل شده</span>
                          ) : (
                            <span className="text-xs text-gray-500">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {assigningRequestId && (
              <form onSubmit={handleAssignRequest} className="bg-gray-900 border border-gray-700 rounded-lg p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">ثبت API برای درخواست #{assigningRequestId}</h3>
                  <button
                    type="button"
                    onClick={() => {
                      setAssigningRequestId(null)
                      setAssignProvider('')
                      setAssignApiKey('')
                      setAssignNotes('')
                      setAssignIsActive(true)
                    setAssignAllowMt5(false)
                    }}
                    className="text-xs text-gray-400 hover:text-gray-200"
                  >
                    بستن
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">ارائه‌دهنده</label>
                    <input
                      value={assignProvider}
                      onChange={(e) => setAssignProvider(e.target.value)}
                      className="w-full px-3 py-3 rounded-lg bg-gray-800 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="مثال: TwelveData"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">کلید API</label>
                    <input
                      value={assignApiKey}
                      onChange={(e) => setAssignApiKey(e.target.value)}
                      className="w-full px-3 py-3 rounded-lg bg-gray-800 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      dir="ltr"
                      placeholder="کلید را وارد کنید"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">یادداشت برای کاربر</label>
                  <textarea
                    value={assignNotes}
                    onChange={(e) => setAssignNotes(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-3 rounded-lg bg-gray-800 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="یادداشت اختیاری (برای مثال توضیح ارائه‌دهنده یا محدودیت‌ها)"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    id="assign-is-active"
                    type="checkbox"
                    checked={assignIsActive}
                    onChange={(e) => setAssignIsActive(e.target.checked)}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                  />
                  <label htmlFor="assign-is-active" className="text-sm text-gray-300">
                    فعال‌سازی فوری دسترسی کاربر
                  </label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    id="assign-allow-mt5"
                    type="checkbox"
                    checked={assignAllowMt5}
                    onChange={(e) => setAssignAllowMt5(e.target.checked)}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                  />
                  <label htmlFor="assign-allow-mt5" className="text-sm text-gray-300">
                    فعال کردن دسترسی دریافت قیمت از MetaTrader 5
                  </label>
                </div>
                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={assignSubmitting}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg text-sm font-medium transition"
                  >
                    {assignSubmitting ? 'در حال ثبت...' : 'ثبت اطلاعات برای کاربر'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setAssigningRequestId(null)
                      setAssignProvider('')
                      setAssignApiKey('')
                      setAssignNotes('')
                      setAssignIsActive(true)
                    setAssignAllowMt5(false)
                    }}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm font-medium transition"
                  >
                    انصراف
                  </button>
                </div>
              </form>
            )}
          </div>
        )}
        {/* API Usage Stats - Available for all users */}
        <div className="bg-gray-800 rounded-lg overflow-hidden mt-6">
          <ErrorBoundary fallback={<div className="p-6 text-red-400">خطا در بارگذاری آمار API</div>}>
            <APIUsageStats />
          </ErrorBoundary>
        </div>

        {/* User Activity Logs */}
        <div className="bg-gray-800 rounded-lg p-6 mt-6">
          <h2 className="text-xl font-semibold text-white mb-4">لاگ فعالیت‌ها</h2>
          {activityLogsLoading ? (
            <div className="text-center py-8">
              <div className="text-gray-400">در حال بارگذاری...</div>
            </div>
          ) : activityLogs.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400">هیچ فعالیتی ثبت نشده است</div>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {activityLogs.map((log) => {
                const date = new Date(log.created_at)
                const formattedDate = date.toLocaleDateString('fa-IR', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })
                const tokenInfo = log.metadata?.token_info
                return (
                  <div
                    key={log.id}
                    className="bg-gray-700 rounded-lg p-4 border border-gray-600 hover:border-gray-500 transition"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <div className="text-white font-medium">{log.action_type_display}</div>
                        <div className="text-gray-300 text-sm mt-1">{log.action_description}</div>
                        {tokenInfo && tokenInfo.total_tokens && (
                          <div className="text-blue-300 text-xs mt-2">
                            توکن‌های مصرفی: {tokenInfo.total_tokens.toLocaleString('fa-IR')}
                            {tokenInfo.input_tokens && tokenInfo.output_tokens && (
                              <span className="text-gray-400 mr-2">
                                (ورودی: {tokenInfo.input_tokens.toLocaleString('fa-IR')}، خروجی:{' '}
                                {tokenInfo.output_tokens.toLocaleString('fa-IR')})
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="text-gray-400 text-xs whitespace-nowrap mr-4">{formattedDate}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Security & Admin Controls - Admin Only */}
        {(isAdmin === true || user?.is_staff || user?.is_superuser) && (
          <div className="bg-gray-800 rounded-lg overflow-hidden mt-6 p-6 space-y-6">
            <div className="bg-gray-900 rounded-lg p-5 border border-gray-700">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h3 className="text-xl font-bold text-white">نمایش بخش معاملات زنده</h3>
                  <p className="text-gray-400 text-sm mt-2">
                    با غیرفعال کردن این گزینه، صفحه و تمام لینک‌های مربوط به معاملات زنده برای کاربران پنهان می‌شود.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${liveTradingStatusClasses}`}>
                    {liveTradingStatusLabel}
                  </span>
                  <button
                    onClick={handleToggleLiveTradingVisibility}
                    disabled={toggleLiveTradingLoading || featureFlagsLoading}
                    className={`px-4 py-2 rounded-lg font-medium text-white transition disabled:opacity-50 disabled:cursor-not-allowed ${
                      liveTradingEnabled
                        ? 'bg-red-600 hover:bg-red-700'
                        : 'bg-green-600 hover:bg-green-700'
                    }`}
                  >
                    {toggleLiveTradingLoading
                      ? 'در حال اعمال...'
                      : liveTradingEnabled
                      ? 'مخفی کردن'
                      : 'فعال کردن'}
                  </button>
                </div>
              </div>
              <p className="text-gray-500 text-xs mt-3">
                تغییرات بلافاصله اعمال می‌شود و کاربران پس از بارگذاری مجدد صفحه وضعیت جدید را مشاهده می‌کنند.
              </p>
            </div>

            <div className="flex flex-col gap-4">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">مدیریت امنیت و مسائل حساس</h3>
                  <p className="text-gray-400 text-sm">مدیریت IP های مسدود شده، Rate Limiting و لاگ‌های امنیتی</p>
                </div>
                <Link
                  to="/admin/security"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition font-medium"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  ورود به صفحه مدیریت امنیت
                </Link>
              </div>

              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">تنظیمات وب‌سایت</h3>
                  <p className="text-gray-400 text-sm">مدیریت تنظیمات عمومی وب‌سایت و ویژگی‌های سیستم</p>
                </div>
                <Link
                  to="/admin/settings"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition font-medium"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  ورود به صفحه تنظیمات
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

