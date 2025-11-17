/**
 * Self-managed CAPTCHA utility
 * Lightweight, no external dependencies
 */

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
 * Get API base URL (same logic as client.ts)
 */
function getApiBaseUrl(): string {
  // In development, use Vite proxy which automatically handles local network IPs
  if (import.meta.env.DEV) {
    return '/api'
  }
  
  // In production, use the actual API URL
  const hostname = window.location.hostname
  const protocol = window.location.protocol
  
  // If accessing via localhost or 127.0.0.1, use localhost
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000/api'
  }
  
  // Otherwise, use the same hostname with port 8000
  return `${protocol}//${hostname}:8000/api`
}

/**
 * Get CAPTCHA challenge from backend
 */
export const getCaptcha = async (action: string = 'default'): Promise<CaptchaData> => {
  try {
    const apiBaseUrl = getApiBaseUrl()
    const response = await fetch(`${apiBaseUrl}/captcha/get/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ action }),
      credentials: 'include', // Important for session cookies
    })

    if (!response.ok) {
      throw new Error('Failed to get CAPTCHA')
    }

    const data = await response.json()
    
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
  } catch (error) {
    console.error('Error getting CAPTCHA:', error)
    throw error
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

