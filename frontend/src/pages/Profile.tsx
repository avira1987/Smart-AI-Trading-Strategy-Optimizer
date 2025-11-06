import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { checkProfileCompletion, updateProfile } from '../api/auth'
import { useToast } from '../components/ToastProvider'
import APIConfigurations from '../components/APIConfigurations'
import DDNSConfiguration from '../components/DDNSConfiguration'
import APIUsageStats from '../components/APIUsageStats'
import SymbolSelector from '../components/SymbolSelector'
import { getWalletBalance, chargeWallet } from '../api/client'

export default function Profile() {
  const [email, setEmail] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [loading, setLoading] = useState(false)
  const [editingProfile, setEditingProfile] = useState(false)
  const [walletBalance, setWalletBalance] = useState<number>(0)
  const [walletLoading, setWalletLoading] = useState(false)
  const [charging, setCharging] = useState(false)
  const { user, checkAuthentication, isAdmin } = useAuth()
  const { showToast } = useToast()
  const [searchParams, setSearchParams] = useSearchParams()

  useEffect(() => {
    loadProfile()
    loadWalletBalance()
  }, [user])

  // Handle payment callback from Zarinpal
  useEffect(() => {
    const paymentSuccess = searchParams.get('payment_success')
    const paymentError = searchParams.get('payment_error')

    if (paymentSuccess === '1') {
      showToast('پرداخت با موفقیت انجام شد! حساب شما شارژ شد.', { type: 'success', duration: 5000 })
      // Remove query params from URL
      searchParams.delete('payment_success')
      searchParams.delete('transaction_id')
      setSearchParams(searchParams, { replace: true })
      // Refresh wallet balance
      loadWalletBalance()
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
  }, [searchParams, setSearchParams, showToast])

  const loadProfile = async () => {
    try {
      const response = await checkProfileCompletion()
      if (response.success) {
        // Pre-fill existing values
        if (user?.email && !user.email.endsWith('@example.com')) {
          setEmail(user.email)
        } else {
          setEmail('')
        }
        if (user?.phone_number && user.phone_number.startsWith('09')) {
          setPhoneNumber(user.phone_number)
        } else {
          setPhoneNumber(user?.phone_number || '')
        }
      }
    } catch (error) {
      console.error('Error loading profile:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
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

    setLoading(true)
    try {
      const response = await updateProfile(email || undefined, phoneNumber || undefined)
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

  const loadWalletBalance = async () => {
    try {
      setWalletLoading(true)
      const response = await getWalletBalance()
      setWalletBalance(response.data.balance)
    } catch (error) {
      console.error('Error loading wallet balance:', error)
    } finally {
      setWalletLoading(false)
    }
  }

  const handleCharge = async (amount: number) => {
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
                <label htmlFor="phone" className="block text-sm font-medium text-gray-300 mb-2">
                  شماره موبایل
                </label>
                <input
                  id="phone"
                  name="phone"
                  type="tel"
                  autoComplete="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value.replace(/\D/g, '').slice(0, 11))}
                  placeholder="09123456789"
                  className="appearance-none relative block w-full px-3 py-3 border border-gray-600 placeholder-gray-500 text-white bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  dir="ltr"
                  disabled={loading}
                />
                {user?.phone_number && !user.phone_number.startsWith('09') && (
                  <p className="mt-1 text-xs text-yellow-400">
                    لطفا شماره موبایل معتبر خود را وارد کنید
                  </p>
                )}
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={loading || (!email && !phoneNumber)}
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
                <p className="text-white text-lg">{user?.username || 'نامشخص'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  ایمیل
                </label>
                <p className="text-white text-lg">{user?.email && !user.email.endsWith('@example.com') ? user.email : 'تعریف نشده'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  شماره موبایل
                </label>
                <p className="text-white text-lg">{user?.phone_number && user.phone_number.startsWith('09') ? user.phone_number : 'تعریف نشده'}</p>
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
          <APIConfigurations />
        </div>

        {/* DDNS Configuration - Admin Only */}
        {isAdmin && (
          <div className="bg-gray-800 rounded-lg overflow-hidden mt-6">
            <DDNSConfiguration />
          </div>
        )}

        {/* API Usage Stats - Admin Only */}
        {isAdmin && (
          <div className="bg-gray-800 rounded-lg overflow-hidden mt-6">
            <APIUsageStats />
          </div>
        )}
      </div>
    </div>
  )
}

