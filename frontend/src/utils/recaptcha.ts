/**
 * reCAPTCHA v3 utility functions
 * Lightweight implementation for bot protection
 */

declare global {
  interface Window {
    grecaptcha?: {
      ready: (callback: () => void) => void
      execute: (siteKey: string, options: { action: string }) => Promise<string>
    }
  }
}

/**
 * Get reCAPTCHA site key from environment or return empty string
 */
export const getRecaptchaSiteKey = (): string => {
  return import.meta.env.VITE_RECAPTCHA_SITE_KEY || ''
}

/**
 * Check if reCAPTCHA is available
 */
export const isRecaptchaAvailable = (): boolean => {
  return typeof window !== 'undefined' && typeof window.grecaptcha !== 'undefined'
}

/**
 * Execute reCAPTCHA v3 and get token
 * @param action - Action name (e.g., 'login', 'send_otp', 'verify_otp')
 * @returns Promise with reCAPTCHA token or empty string if not available
 */
export const executeRecaptcha = async (action: string = 'submit'): Promise<string> => {
  const siteKey = getRecaptchaSiteKey()
  
  // If no site key configured, return empty (will be handled by backend)
  if (!siteKey) {
    console.warn('reCAPTCHA site key not configured')
    return ''
  }
  
  // If reCAPTCHA not loaded, return empty
  if (!isRecaptchaAvailable()) {
    console.warn('reCAPTCHA not loaded')
    return ''
  }
  
  try {
    return new Promise((resolve) => {
      window.grecaptcha!.ready(() => {
        window.grecaptcha!
          .execute(siteKey, { action })
          .then((token) => {
            resolve(token)
          })
          .catch((error) => {
            console.error('reCAPTCHA execution error:', error)
            resolve('') // Fail gracefully
          })
      })
    })
  } catch (error) {
    console.error('reCAPTCHA error:', error)
    return '' // Fail gracefully
  }
}

/**
 * Load reCAPTCHA script dynamically
 */
export const loadRecaptcha = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    // Check if already loaded
    if (isRecaptchaAvailable()) {
      resolve()
      return
    }
    
    // Check if script is already in DOM
    const existingScript = document.querySelector('script[src*="recaptcha"]')
    if (existingScript) {
      // Wait for it to load
      const checkInterval = setInterval(() => {
        if (isRecaptchaAvailable()) {
          clearInterval(checkInterval)
          resolve()
        }
      }, 100)
      
      // Timeout after 5 seconds
      setTimeout(() => {
        clearInterval(checkInterval)
        if (!isRecaptchaAvailable()) {
          reject(new Error('reCAPTCHA failed to load'))
        }
      }, 5000)
      return
    }
    
    // Create and load script
    const script = document.createElement('script')
    const siteKey = getRecaptchaSiteKey()
    script.src = `https://www.google.com/recaptcha/api.js?render=${siteKey}`
    script.async = true
    script.defer = true
    
    script.onload = () => {
      // Wait for grecaptcha to be available
      const checkInterval = setInterval(() => {
        if (isRecaptchaAvailable()) {
          clearInterval(checkInterval)
          resolve()
        }
      }, 100)
      
      setTimeout(() => {
        clearInterval(checkInterval)
        if (isRecaptchaAvailable()) {
          resolve()
        } else {
          reject(new Error('reCAPTCHA failed to initialize'))
        }
      }, 5000)
    }
    
    script.onerror = () => {
      reject(new Error('Failed to load reCAPTCHA script'))
    }
    
    document.head.appendChild(script)
  })
}

