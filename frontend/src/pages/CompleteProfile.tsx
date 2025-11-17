import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { checkProfileCompletion, updateProfile } from '../api/auth'
import { useToast } from '../components/ToastProvider'

export default function CompleteProfile() {
  const [email, setEmail] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(true)
  const { user, checkAuthentication } = useAuth()
  const navigate = useNavigate()
  const { showToast } = useToast()

  useEffect(() => {
    const checkProfile = async () => {
      try {
        const response = await checkProfileCompletion()
        if (response.success) {
          if (response.is_complete) {
            // Profile is already complete, redirect to dashboard
            navigate('/')
            return
          }
          
          // Pre-fill existing values
          if (user?.email && !user.email.endsWith('@example.com')) {
            setEmail(user.email)
          }
          if (user?.phone_number && user.phone_number.startsWith('09')) {
            setPhoneNumber(user.phone_number)
          }
        }
      } catch (error) {
        console.error('Error checking profile:', error)
      } finally {
        setChecking(false)
      }
    }

    checkProfile()
  }, [user, navigate])

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
        // Check if profile is now complete
        const profileCheck = await checkProfileCompletion()
        if (profileCheck.success && profileCheck.is_complete) {
          navigate('/')
        }
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

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-white">در حال بارگذاری...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
            تکمیل پروفایل
          </h2>
          <p className="mt-2 text-center text-sm text-gray-400">
            لطفا اطلاعات خود را برای تکمیل پروفایل وارد کنید
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm space-y-4">
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
                className="appearance-none relative block w-full px-3 py-3 border border-gray-600 placeholder-gray-500 text-white bg-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                className="appearance-none relative block w-full px-3 py-3 border border-gray-600 placeholder-gray-500 text-white bg-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                dir="ltr"
                disabled={loading}
              />
              {user?.phone_number && !user.phone_number.startsWith('09') && (
                <p className="mt-1 text-xs text-yellow-400">
                  لطفا شماره موبایل معتبر خود را وارد کنید
                </p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading || (!email && !phoneNumber)}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading ? 'در حال ذخیره...' : 'ذخیره و ادامه'}
            </button>
          </div>

          <div className="text-center">
            <button
              type="button"
              onClick={() => {
                // Set a flag in localStorage to skip profile completion for 24 hours
                const skipUntil = Date.now() + (24 * 60 * 60 * 1000) // 24 hours from now
                localStorage.setItem('skip_profile_completion', skipUntil.toString())
                navigate('/')
              }}
              className="text-sm text-gray-400 hover:text-gray-300"
              disabled={loading}
            >
              بعدا تکمیل می‌کنم
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

