import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { sendOTP, verifyOTP } from '../api/auth'
import { useToast } from '../components/ToastProvider'
import { getCaptcha, initPageLoadTime, prepareCaptchaData, clearCaptcha } from '../utils/selfCaptcha'

export default function Login() {
  const [step, setStep] = useState<'phone' | 'otp'>('phone')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [otpCode, setOtpCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const [captchaChallenge, setCaptchaChallenge] = useState('')
  const [captchaAnswer, setCaptchaAnswer] = useState('')
  const [captchaLoading, setCaptchaLoading] = useState(true)
  const [captchaError, setCaptchaError] = useState<string | null>(null)
  const [failedAttempts, setFailedAttempts] = useState(0)
  const [isBlocked, setIsBlocked] = useState(false)
  const [otpCodeFromBackend, setOtpCodeFromBackend] = useState<string | null>(null)
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const isSubmittingRef = useRef(false) // Prevent multiple simultaneous submissions
  
  const MAX_FAILED_ATTEMPTS = 5

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/')
    }
  }, [isAuthenticated, navigate])

  // Initialize page load time and get CAPTCHA on mount
  useEffect(() => {
    initPageLoadTime()
    loadCaptcha()
  }, [])

  const loadCaptcha = async (showErrorToast: boolean = true) => {
    setCaptchaLoading(true)
    setCaptchaError(null)
    
    try {
      const captcha = await getCaptcha('login')
      setCaptchaChallenge(captcha.challenge)
      setCaptchaAnswer('') // Clear previous answer
      setCaptchaError(null)
    } catch (error: any) {
      console.error('Failed to load CAPTCHA:', error)
      
      // تشخیص نوع خطا و نمایش پیام مناسب
      let errorMessage = 'خطا در بارگذاری سوال امنیتی'
      const errorText = error.message || error.toString() || ''
      
      if (errorText.includes('ECONNREFUSED') || errorText.includes('Failed to fetch') || errorText.includes('NetworkError')) {
        errorMessage = 'اتصال به سرور برقرار نشد. لطفا اتصال اینترنت خود را بررسی کنید.'
      } else if (errorText.includes('CORS')) {
        errorMessage = 'خطای CORS. لطفا تنظیمات CORS در Backend را بررسی کنید.'
      } else if (errorText.includes('timeout') || errorText.includes('ECONNABORTED')) {
        errorMessage = 'زمان درخواست به پایان رسید. لطفا دوباره تلاش کنید.'
      } else {
        errorMessage = errorText || 'خطا در بارگذاری سوال امنیتی'
      }
      
      setCaptchaError(errorMessage)
      setCaptchaChallenge('') // Clear challenge on error
      
      if (showErrorToast) {
        showToast(`خطا: ${errorMessage}`, { type: 'error', duration: 5000 })
      }
      
      // تلاش مجدد خودکار فقط برای خطاهای timeout (نه برای خطاهای شبکه)
      if (errorText.includes('timeout') || errorText.includes('ECONNABORTED')) {
        setTimeout(() => {
          loadCaptcha(false) // Retry without showing toast again
        }, 3000)
      }
    } finally {
      setCaptchaLoading(false)
    }
  }

  const handleRefreshCaptcha = async () => {
    await loadCaptcha(true)
  }

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [countdown])

  // Auto-verify OTP when 4 digits are entered
  useEffect(() => {
    if (step === 'otp' && otpCode.length === 4 && !loading && !isBlocked && otpCode.match(/^\d+$/) && !isSubmittingRef.current) {
      // Auto-submit OTP when 4 digits are entered
      const autoSubmit = async () => {
        // Prevent multiple simultaneous submissions
        if (isSubmittingRef.current) {
          return
        }
        
        isSubmittingRef.current = true
        setLoading(true)
        
        try {
          // Prepare CAPTCHA data (optional for OTP verification)
          const captchaData = captchaAnswer ? prepareCaptchaData(Number(captchaAnswer)) : null
          
          const response = await verifyOTP(phoneNumber, otpCode, captchaData)
          
          // Only proceed with login if response is explicitly successful
          if (response.success && response.user && response.device_id) {
            // Reset failed attempts on success
            setFailedAttempts(0)
            setIsBlocked(false)
            clearCaptcha() // Clear CAPTCHA after successful submission
            login(response.user, response.device_id)
            
            // Check if this is a new user
            const isNewUser = response.is_new_user || false
            
            if (isNewUser) {
              // Show welcome message with registration bonus
              showToast(
                '🎉 به پلتفرم خوش آمدید! مبلغ 399 تومان هدیه ثبت‌نام به حساب شما اضافه شد.',
                { type: 'success', duration: 8000 }
              )
              navigate('/complete-profile')
            } else {
              showToast('ورود با موفقیت انجام شد', { type: 'success' })
              navigate('/')
            }
            // Clear OTP code after successful login
            setOtpCode('')
          } else {
            // Explicitly handle failure - do NOT login
            const errorMessage = response.message || 'کد وارد شده اشتباه است'
            
            // Clear OTP code on error to prevent re-submission
            setOtpCode('')
            
            // Increment failed attempts for wrong OTP codes
            if (errorMessage.includes('اشتباه') || errorMessage.includes('کد وارد شده')) {
              const newFailedAttempts = failedAttempts + 1
              setFailedAttempts(newFailedAttempts)
              
              if (newFailedAttempts >= MAX_FAILED_ATTEMPTS) {
                setIsBlocked(true)
                showToast(
                  `شما ${MAX_FAILED_ATTEMPTS} بار کد اشتباه وارد کرده‌اید. لطفا کد جدید درخواست کنید.`,
                  { type: 'error', duration: 10000 }
                )
                return
              } else {
                const remainingAttempts = MAX_FAILED_ATTEMPTS - newFailedAttempts
                showToast(
                  `کد اشتباه است. ${remainingAttempts} تلاش باقی مانده است.`,
                  { type: 'error', duration: 5000 }
                )
              }
            }
            
            // اگر خطا مربوط به CAPTCHA منقضی شده است
            if (errorMessage.includes('منقضی شده') || errorMessage.includes('expired')) {
              await loadCaptcha()
              showToast('CAPTCHA منقضی شده است. لطفا CAPTCHA جدید را حل کنید.', { type: 'error' })
            } else if (errorMessage.includes('wrong_answer')) {
              await loadCaptcha()
              showToast('پاسخ CAPTCHA اشتباه است. لطفا CAPTCHA جدید را حل کنید.', { type: 'error' })
            } else if (!errorMessage.includes('اشتباه') && !errorMessage.includes('کد وارد شده')) {
              showToast(errorMessage, { type: 'error' })
            }
          }
        } catch (error: any) {
          // On error, explicitly do NOT login
          const errorMsg = error.response?.data?.message || 'خطا در تایید کد'
          
          // Clear OTP code on error
          setOtpCode('')
          
          // Increment failed attempts for network errors too
          if (errorMsg.includes('اشتباه') || errorMsg.includes('کد وارد شده')) {
            const newFailedAttempts = failedAttempts + 1
            setFailedAttempts(newFailedAttempts)
            
            if (newFailedAttempts >= MAX_FAILED_ATTEMPTS) {
              setIsBlocked(true)
              showToast(
                `شما ${MAX_FAILED_ATTEMPTS} بار کد اشتباه وارد کرده‌اید. لطفا کد جدید درخواست کنید.`,
                { type: 'error', duration: 10000 }
              )
            } else {
              const remainingAttempts = MAX_FAILED_ATTEMPTS - newFailedAttempts
              showToast(
                `کد اشتباه است. ${remainingAttempts} تلاش باقی مانده است.`,
                { type: 'error', duration: 5000 }
              )
            }
          } else {
            showToast(errorMsg, { type: 'error' })
          }
        } finally {
          setLoading(false)
          isSubmittingRef.current = false
        }
      }
      
      // Small delay to allow user to see the code they entered
      const timeoutId = setTimeout(() => {
        autoSubmit()
      }, 500)
      
      return () => {
        clearTimeout(timeoutId)
        isSubmittingRef.current = false
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [otpCode, step, loading, isBlocked, failedAttempts])

  const handlePhoneSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!phoneNumber.match(/^09\d{9}$/)) {
      showToast('شماره موبایل معتبر نیست', { type: 'error' })
      return
    }

    // Validate CAPTCHA answer
    if (!captchaAnswer || isNaN(Number(captchaAnswer))) {
      showToast('لطفا پاسخ CAPTCHA را وارد کنید', { type: 'error' })
      return
    }

    setLoading(true)
    try {
      // Prepare CAPTCHA data
      const captchaData = prepareCaptchaData(Number(captchaAnswer))
      
      const response = await sendOTP(phoneNumber, captchaData)
      if (response.success) {
        clearCaptcha() // Clear CAPTCHA after successful submission
        
        // Reset failed attempts and block status when new OTP is sent
        setFailedAttempts(0)
        setIsBlocked(false)
        
        // Check if this is development mode (API key not configured)
        const isDevMode = (response as any).development_mode
        const otpCode = (response as any).otp_code
        
        // Store OTP code from backend for debugging
        if (isDevMode && otpCode) {
          setOtpCodeFromBackend(otpCode)
          showToast(`کد یکبار مصرف: ${otpCode} (حالت توسعه)`, { type: 'success', duration: 10000 })
        } else {
          setOtpCodeFromBackend(null)
          showToast('کد یکبار مصرف به شماره شما ارسال شد', { type: 'success' })
        }
        
        setStep('otp')
        setCountdown(300) // 5 minutes
        // Load new CAPTCHA for OTP step
        await loadCaptcha()
        setCaptchaAnswer('')
        setOtpCode('') // Clear previous OTP code
      } else {
        // نمایش پیام خطای واضح‌تر
        const errorMessage = response.message || 'خطا در ارسال کد'
        let detailedMessage = errorMessage
        
        // اگر خطا مربوط به CAPTCHA منقضی شده است
        if (errorMessage.includes('منقضی شده') || errorMessage.includes('expired')) {
          // بارگذاری مجدد CAPTCHA به جای رفرش صفحه
          await loadCaptcha()
          detailedMessage = 'CAPTCHA منقضی شده است. لطفا CAPTCHA جدید را حل کنید.'
        }
        // اگر خطا مربوط به شماره فرستنده است، راهنمایی نمایش بده
        else if (errorMessage.includes('ارسال کننده') || errorMessage.includes('نامعتبر') || errorMessage.includes('412')) {
          detailedMessage = 'خطا در ارسال پیامک: شماره فرستنده نامعتبر است. لطفاً فایل راهنمای_تنظیم_Kavenegar_SMS.md را مطالعه کنید.'
        }
        // اگر خطا مربوط به پاسخ اشتباه CAPTCHA است
        else if (errorMessage.includes('اشتباه') || errorMessage.includes('wrong_answer')) {
          // بارگذاری مجدد CAPTCHA
          await loadCaptcha()
          detailedMessage = 'پاسخ CAPTCHA اشتباه است. لطفا CAPTCHA جدید را حل کنید.'
        }
        
        showToast(detailedMessage, { type: 'error', duration: 8000 })
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || error.message || 'خطا در ارسال کد'
      let detailedMessage = errorMessage
      
      // اگر خطا مربوط به شبکه است
      if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT' || !error.response) {
        const currentOrigin = window.location.origin
        detailedMessage = `خطا در اتصال به Backend.\n\nلطفاً بررسی کنید:\n1. Backend در حال اجرا است؟\n2. Nginx proxy فعال است؟ (در production)\n3. Vite proxy فعال است؟ (در development)\n\nآدرس فعلی: ${currentOrigin}\n\nراه حل:\n- در Development: Backend باید روی localhost:8000 اجرا شود\n- در Production: Backend باید از طریق Nginx در دسترس باشد`
      }
      
      showToast(detailedMessage, { type: 'error', duration: 8000 })
    } finally {
      setLoading(false)
    }
  }

  const handleOTPSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (isBlocked) {
      showToast('شما بلاک شده‌اید. لطفا کد جدید درخواست کنید.', { type: 'error' })
      return
    }
    
    if (otpCode.length !== 4 || !otpCode.match(/^\d+$/)) {
      showToast('کد باید 4 رقم باشد', { type: 'error' })
      return
    }

    // Prevent multiple simultaneous submissions
    if (isSubmittingRef.current) {
      return
    }

    isSubmittingRef.current = true
    setLoading(true)
    
    try {
      // Prepare CAPTCHA data (optional for OTP verification)
      const captchaData = captchaAnswer ? prepareCaptchaData(Number(captchaAnswer)) : null
      
      const response = await verifyOTP(phoneNumber, otpCode, captchaData)
      
      // Only proceed with login if response is explicitly successful
      if (response.success && response.user && response.device_id) {
        // Reset failed attempts on success
        setFailedAttempts(0)
        setIsBlocked(false)
        clearCaptcha() // Clear CAPTCHA after successful submission
        login(response.user, response.device_id)
        
        // Check if this is a new user
        const isNewUser = response.is_new_user || false
        
        if (isNewUser) {
          // Show welcome message with registration bonus
          showToast(
            '🎉 به پلتفرم خوش آمدید! مبلغ 399 تومان هدیه ثبت‌نام به حساب شما اضافه شد.',
            { type: 'success', duration: 8000 }
          )
          navigate('/complete-profile')
        } else {
          showToast('ورود با موفقیت انجام شد', { type: 'success' })
          navigate('/')
        }
        // Clear OTP code after successful login
        setOtpCode('')
      } else {
        // Explicitly handle failure - do NOT login
        const errorMessage = response.message || 'کد وارد شده اشتباه است'
        
        // Clear OTP code on error to prevent re-submission
        setOtpCode('')
        
        // Increment failed attempts for wrong OTP codes
        if (errorMessage.includes('اشتباه') || errorMessage.includes('کد وارد شده')) {
          const newFailedAttempts = failedAttempts + 1
          setFailedAttempts(newFailedAttempts)
          
          if (newFailedAttempts >= MAX_FAILED_ATTEMPTS) {
            setIsBlocked(true)
            showToast(
              `شما ${MAX_FAILED_ATTEMPTS} بار کد اشتباه وارد کرده‌اید. لطفا کد جدید درخواست کنید.`,
              { type: 'error', duration: 10000 }
            )
            return
          } else {
            const remainingAttempts = MAX_FAILED_ATTEMPTS - newFailedAttempts
            showToast(
              `کد اشتباه است. ${remainingAttempts} تلاش باقی مانده است.`,
              { type: 'error', duration: 5000 }
            )
          }
        }
        
        // اگر خطا مربوط به CAPTCHA منقضی شده است
        if (errorMessage.includes('منقضی شده') || errorMessage.includes('expired')) {
          await loadCaptcha()
          showToast('CAPTCHA منقضی شده است. لطفا CAPTCHA جدید را حل کنید.', { type: 'error' })
        } else if (errorMessage.includes('wrong_answer')) {
          await loadCaptcha()
          showToast('پاسخ CAPTCHA اشتباه است. لطفا CAPTCHA جدید را حل کنید.', { type: 'error' })
        } else if (!errorMessage.includes('اشتباه') && !errorMessage.includes('کد وارد شده')) {
          showToast(errorMessage, { type: 'error' })
        }
      }
    } catch (error: any) {
      // On error, explicitly do NOT login
      const errorMsg = error.response?.data?.message || 'خطا در تایید کد'
      
      // Clear OTP code on error
      setOtpCode('')
      
      // Increment failed attempts for network errors too
      if (errorMsg.includes('اشتباه') || errorMsg.includes('کد وارد شده')) {
        const newFailedAttempts = failedAttempts + 1
        setFailedAttempts(newFailedAttempts)
        
        if (newFailedAttempts >= MAX_FAILED_ATTEMPTS) {
          setIsBlocked(true)
          showToast(
            `شما ${MAX_FAILED_ATTEMPTS} بار کد اشتباه وارد کرده‌اید. لطفا کد جدید درخواست کنید.`,
            { type: 'error', duration: 10000 }
          )
        } else {
          const remainingAttempts = MAX_FAILED_ATTEMPTS - newFailedAttempts
          showToast(
            `کد اشتباه است. ${remainingAttempts} تلاش باقی مانده است.`,
            { type: 'error', duration: 5000 }
          )
        }
      } else {
        showToast(errorMsg, { type: 'error' })
      }
    } finally {
      setLoading(false)
      isSubmittingRef.current = false
    }
  }

  const handleResendOTP = async () => {
    if (countdown > 0) return
    
    // Reload CAPTCHA for resend
    await loadCaptcha()
    setCaptchaAnswer('')
    
    setLoading(true)
    try {
      // Prepare CAPTCHA data
      const captchaData = captchaAnswer ? prepareCaptchaData(Number(captchaAnswer)) : null
      
      const response = await sendOTP(phoneNumber, captchaData)
      if (response.success) {
        clearCaptcha() // Clear CAPTCHA after successful submission
        
        // Reset failed attempts and block status when resending OTP
        setFailedAttempts(0)
        setIsBlocked(false)
        
        // Check if this is development mode (API key not configured)
        const isDevMode = (response as any).development_mode
        const otpCode = (response as any).otp_code
        
        // Store OTP code from backend for debugging
        if (isDevMode && otpCode) {
          setOtpCodeFromBackend(otpCode)
        } else {
          setOtpCodeFromBackend(null)
        }
        
        showToast('کد مجددا ارسال شد', { type: 'success' })
        setCountdown(300)
        setOtpCode('') // Clear previous OTP code
        // Reload CAPTCHA
        await loadCaptcha()
        setCaptchaAnswer('')
      } else {
        const errorMessage = response.message || 'خطا در ارسال کد'
        
        // اگر خطا مربوط به CAPTCHA منقضی شده است
        if (errorMessage.includes('منقضی شده') || errorMessage.includes('expired')) {
          await loadCaptcha()
          showToast('CAPTCHA منقضی شده است. لطفا CAPTCHA جدید را حل کنید.', { type: 'error' })
        } else if (errorMessage.includes('اشتباه') || errorMessage.includes('wrong_answer')) {
          await loadCaptcha()
          showToast('پاسخ CAPTCHA اشتباه است. لطفا CAPTCHA جدید را حل کنید.', { type: 'error' })
        } else {
          showToast(errorMessage, { type: 'error' })
        }
      }
    } catch (error: any) {
      showToast(error.response?.data?.message || 'خطا در ارسال کد', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-gray-800 rounded-xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">ورود به سیستم</h1>
            <p className="text-gray-400">ورود با شماره موبایل و کد یکبار مصرف</p>
          </div>

          {step === 'phone' ? (
            <>
              <form onSubmit={handlePhoneSubmit} className="space-y-6">
                <div>
                  <label htmlFor="phone" className="label-standard text-center">
                    شماره موبایل
                  </label>
                  <input
                    type="tel"
                    id="phone"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value.replace(/\D/g, '').slice(0, 11))}
                    placeholder="09123456789"
                    className="input-standard-lg placeholder-gray-400 text-center"
                    required
                    disabled={loading}
                    dir="ltr"
                  />
                </div>

                {/* CAPTCHA Challenge */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label htmlFor="captcha" className="label-standard text-center flex-1">
                      {captchaLoading ? (
                        <span className="text-gray-400">در حال بارگذاری سوال امنیتی...</span>
                      ) : captchaError ? (
                        <span className="text-red-400">خطا در بارگذاری سوال امنیتی</span>
                      ) : captchaChallenge ? (
                        <>امنیت: {captchaChallenge} = ?</>
                      ) : (
                        <span className="text-gray-400">سوال امنیتی</span>
                      )}
                    </label>
                    <button
                      type="button"
                      onClick={handleRefreshCaptcha}
                      disabled={loading || captchaLoading}
                      className="mr-2 p-2 text-blue-400 hover:text-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition"
                      title="تازه‌سازی CAPTCHA"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                        />
                      </svg>
                    </button>
                  </div>
                  
                  {captchaLoading ? (
                    <div className="input-standard-lg text-center text-gray-400 py-3">
                      <div className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>در حال بارگذاری...</span>
                      </div>
                    </div>
                  ) : captchaError ? (
                    <div className="space-y-2">
                      <div className="input-standard-lg text-center text-red-400 py-3 bg-red-900/20 border-red-500/50">
                        {captchaError}
                      </div>
                      <button
                        type="button"
                        onClick={handleRefreshCaptcha}
                        disabled={loading}
                        className="w-full btn-secondary py-2 text-sm"
                      >
                        تلاش مجدد
                      </button>
                    </div>
                  ) : captchaChallenge ? (
                    <input
                      type="number"
                      id="captcha"
                      value={captchaAnswer}
                      onChange={(e) => setCaptchaAnswer(e.target.value)}
                      placeholder="پاسخ را وارد کنید"
                      className="input-standard-lg placeholder-gray-400 text-center"
                      required
                      disabled={loading}
                      dir="ltr"
                    />
                  ) : null}
                </div>

                {/* Honeypot field - hidden from users */}
                <input
                  type="text"
                  name="website"
                  tabIndex={-1}
                  autoComplete="off"
                  style={{ position: 'absolute', left: '-9999px' }}
                  aria-hidden="true"
                />

                <button
                  type="submit"
                  disabled={loading || phoneNumber.length !== 11 || !captchaAnswer || !captchaChallenge || captchaLoading}
                  className="w-full btn-primary py-3"
                >
                  {loading ? 'در حال ارسال...' : 'ارسال کد'}
                </button>
              </form>
            </>
          ) : (
            <form onSubmit={handleOTPSubmit} className="space-y-6">
              <div>
                <label htmlFor="otp" className="label-standard">
                  کد یکبار مصرف
                </label>
                <input
                  type="text"
                  id="otp"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  value={otpCode}
                  onChange={(e) => {
                    if (!isBlocked) {
                      setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 4))
                    }
                  }}
                  placeholder="1234"
                  className={`input-standard-lg placeholder-gray-400 text-center text-2xl tracking-widest font-mono ${
                    isBlocked ? 'bg-red-900/20 border-red-500 cursor-not-allowed' : ''
                  }`}
                  required
                  disabled={loading || isBlocked}
                  dir="ltr"
                  maxLength={4}
                />
                <p className="text-sm text-gray-400 mt-2 text-center">
                  کد به شماره {phoneNumber} ارسال شد
                </p>
                {isBlocked && (
                  <p className="text-sm text-red-400 mt-2 text-center">
                    شما {MAX_FAILED_ATTEMPTS} بار کد اشتباه وارد کرده‌اید. لطفا کد جدید درخواست کنید.
                  </p>
                )}
                {failedAttempts > 0 && !isBlocked && (
                  <p className="text-sm text-yellow-400 mt-2 text-center">
                    {MAX_FAILED_ATTEMPTS - failedAttempts} تلاش باقی مانده است
                  </p>
                )}
              </div>
              
              {/* Display OTP code from backend for debugging (development mode only) */}
              {otpCodeFromBackend && (
                <div className="bg-gray-700/50 border border-gray-600 rounded-lg p-3">
                  <label className="text-xs text-gray-400 block mb-1">
                    کد ارسال شده (فقط برای debugging - حالت توسعه):
                  </label>
                  <input
                    type="text"
                    value={otpCodeFromBackend}
                    readOnly
                    className="w-full px-3 py-2 bg-gray-800 text-white text-center text-lg font-mono rounded border border-gray-600 cursor-text"
                    onClick={(e) => {
                      (e.target as HTMLInputElement).select()
                      document.execCommand('copy')
                      showToast('کد کپی شد', { type: 'success', duration: 2000 })
                    }}
                  />
                  <p className="text-xs text-gray-500 mt-1 text-center">
                    برای کپی کردن کد، روی آن کلیک کنید
                  </p>
                </div>
              )}

              {/* Honeypot field */}
              <input
                type="text"
                name="website"
                tabIndex={-1}
                autoComplete="off"
                style={{ position: 'absolute', left: '-9999px' }}
                aria-hidden="true"
              />

              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => setStep('phone')}
                  className="flex-1 btn-secondary py-3"
                  disabled={loading}
                >
                  تغییر شماره
                </button>
                <button
                  type="submit"
                  disabled={loading || otpCode.length !== 4 || isBlocked}
                  className="flex-1 btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'در حال بررسی...' : isBlocked ? 'بلاک شده' : 'ورود'}
                </button>
              </div>

              <div className="text-center">
                {countdown > 0 ? (
                  <p className="text-sm text-gray-400">
                    ارسال مجدد کد در {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, '0')}
                  </p>
                ) : (
                  <button
                    type="button"
                    onClick={handleResendOTP}
                    disabled={loading}
                    className="text-sm text-blue-400 hover:text-blue-300 underline disabled:opacity-50"
                  >
                    ارسال مجدد کد
                  </button>
                )}
              </div>
            </form>
          )}

          <div className="mt-6 text-center text-sm text-gray-400 leading-relaxed">
            ورود شما به وب‌سایت به معنی قبول قوانین وب‌سایت است. قوانین را از{' '}
            <Link to="/terms" className="text-blue-400 hover:text-blue-300 underline">
              اینجا
            </Link>{' '}
            مطالعه کنید.
          </div>

          {/* Telegram Support Link */}
          <div className="mt-8 pt-6 border-t border-gray-700">
            <div className="text-center">
              <p className="text-sm text-gray-400 mb-3">
                در صورت بروز مشکل در ورود، با ما در تماس باشید
              </p>
              <a
                href="https://t.me/avxsupport"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium w-full justify-center"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.174 1.586-.927 5.442-1.31 7.22-.15.685-.445.913-.731.877-.384-.045-1.05-.206-1.63-.402-.645-.206-1.13-.32-1.828-.513-.72-.206-1.27-.319-1.97.319-.595.536-2.31 2.233-3.385 3.014-.38.319-.647.479-1.015.479-.67-.045-1.22-.492-1.89-.96-.693-.48-1.245-1.002-1.89-1.68-.65-.685-2.29-2.01-2.31-2.34-.02-.11.16-.32.445-.536 1.83-1.61 3.05-2.73 3.89-3.27.17-.11.38-.21.595-.21.32 0 .52.15.7.493 1.15 2.19 2.54 4.24 3.85 4.24.32 0 .64-.11.87-.32.35-.32.64-.7.93-1.08.6-.75 1.33-1.68 2.15-2.71.19-.24.38-.48.64-.48.15 0 .32.08.41.24.18.32.15.7.11 1.08z"/>
                </svg>
                پشتیبانی تلگرام
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

