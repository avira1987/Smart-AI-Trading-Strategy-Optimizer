/**
 * Self-managed CAPTCHA utility
 * Uses axios client for consistency with the rest of the app
 */

import client from '../api/client'

export interface CaptchaData {
  token: string
  challenge: string
  type: string
}

let captchaData: CaptchaData | null = null
let pageLoadTime: number = Date.now() / 1000 // Unix timestamp in seconds

/**
 * Initialize page load time
 */
export const initPageLoadTime = (): void => {
  pageLoadTime = Date.now() / 1000
}

/**
 * Get current page load time
 */
export const getPageLoadTime = (): number => {
  return pageLoadTime
}

/**
 * Get CAPTCHA challenge from backend
 * Uses axios client for consistent error handling and network configuration
 */
export const getCaptcha = async (action: string = 'default'): Promise<CaptchaData> => {
  try {
    const response = await client.post<{
      success: boolean
      token: string
      challenge: string
      type: string
      message?: string
    }>('/captcha/get/', { action })

    const data = response.data
    
    if (data.success) {
      captchaData = {
        token: data.token,
        challenge: data.challenge,
        type: data.type,
      }
      return captchaData
    } else {
      throw new Error(data.message || 'Failed to get CAPTCHA')
    }
  } catch (error: any) {
    // Enhanced error logging for debugging CORS and network issues
    const errorDetails = {
      message: error.message,
      code: error.code,
      response: error.response?.data,
      status: error.response?.status,
      url: error.config?.url,
      baseURL: error.config?.baseURL,
      origin: window.location.origin,
      hostname: window.location.hostname,
      isLocalhost: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
      timestamp: new Date().toISOString(),
    }
    
    console.error('Error getting CAPTCHA:', errorDetails)
    
    // Log CORS-specific errors with more detail
    if (error.code === 'ERR_CORS' || error.message?.includes('CORS') || 
        (error.response?.status === 0 && !error.response?.data)) {
      console.error('CORS Error Details:', {
        origin: window.location.origin,
        hostname: window.location.hostname,
        requestURL: error.config?.url,
        baseURL: error.config?.baseURL,
        fullURL: `${error.config?.baseURL}${error.config?.url}`,
        suggestion: 'Check CORS_ALLOWED_ORIGINS in backend settings.py to include this origin',
      })
    }
    
    // Provide more detailed error information
    let errorMessage = 'خطا در بارگذاری سوال امنیتی'
    
    if (error.response) {
      // Server responded with error status
      const status = error.response.status
      if (status === 0 || (status >= 200 && status < 300 && !error.response.data)) {
        // CORS preflight or network issue
        errorMessage = 'خطای CORS یا شبکه. لطفا تنظیمات CORS در Backend را بررسی کنید.'
      } else {
        errorMessage = error.response.data?.message || `خطای سرور: ${status}`
      }
    } else if (error.request) {
      // Request was made but no response received
      // Check if it's a timeout error
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage = 'زمان درخواست به پایان رسید. لطفا اتصال اینترنت خود را بررسی کرده و دوباره تلاش کنید.'
      } else if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        errorMessage = 'خطای شبکه. لطفا اتصال اینترنت خود را بررسی کنید.'
      } else if (error.code === 'ERR_CORS' || error.message?.includes('CORS')) {
        errorMessage = 'خطای CORS. لطفا تنظیمات CORS در Backend را بررسی کنید.'
      } else {
        // More detailed error message for connection issues
        const isInternetAccess = !(window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        if (isInternetAccess) {
          errorMessage = `درخواست به سرور ارسال شد اما پاسخی دریافت نشد.\n\nمشکلات احتمالی:\n1. Backend Django در حال اجرا نیست (پورت 8000)\n2. Nginx نمی‌تواند به Backend متصل شود\n3. مشکل در تنظیمات proxy\n\nلطفا بررسی کنید:\n- Backend روی http://127.0.0.1:8000 در حال اجرا است؟\n- Nginx به درستی پیکربندی شده است؟\n- لاگ‌های Nginx را بررسی کنید`
        } else {
          errorMessage = 'درخواست به سرور ارسال شد اما پاسخی دریافت نشد. لطفا اتصال شبکه را بررسی کنید.'
        }
      }
    } else {
      // Error in request setup
      if (error.message?.includes('CORS') || error.message?.includes('cors')) {
        errorMessage = 'خطای CORS. لطفا تنظیمات CORS در Backend را بررسی کنید.'
      } else {
        errorMessage = error.message || 'خطا در تنظیم درخواست'
      }
    }
    
    throw new Error(errorMessage)
  }
}

/**
 * Get current CAPTCHA data
 */
export const getCurrentCaptcha = (): CaptchaData | null => {
  return captchaData
}

/**
 * Clear CAPTCHA data (after successful submission)
 */
export const clearCaptcha = (): void => {
  captchaData = null
}

/**
 * Prepare CAPTCHA data for submission
 */
export const prepareCaptchaData = (answer: number): {
  captcha_token: string
  captcha_answer: number
  page_load_time: number
  website: string // Honeypot field (should be empty)
} | null => {
  if (!captchaData) {
    return null
  }

  return {
    captcha_token: captchaData.token,
    captcha_answer: answer,
    page_load_time: getPageLoadTime(),
    website: '', // Honeypot - always empty
  }
}

