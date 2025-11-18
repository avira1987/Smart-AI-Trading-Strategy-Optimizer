import { useRef, useCallback } from 'react'
import { useToast } from '../components/ToastProvider'

interface UseRateLimitOptions {
  minInterval?: number // حداقل فاصله زمانی بین کلیک‌ها به میلی‌ثانیه (پیش‌فرض: 2000ms = 2 ثانیه)
  message?: string // پیام نمایش داده شده در صورت کلیک سریع
  key?: string // کلید منحصر به فرد برای این handler (اختیاری)
}

// نگه‌داری زمان آخرین کلیک در سطح ماژول (global)
const globalLastClickTimes = new Map<string, number>()

/**
 * هوک برای محدود کردن کلیک‌های پشت‌سرهم روی دکمه‌ها
 * این هوک از ارسال درخواست‌های مکرر به سرور جلوگیری می‌کند
 * 
 * @param options - تنظیمات محدودیت کلیک
 * @returns تابعی که باید یک تابع دیگر را wrap کند
 * 
 * @example
 * const rateLimitClick = useRateLimit({ minInterval: 2000, key: 'openTrade' })
 * 
 * const handleClick = rateLimitClick(async () => {
 *   // کد شما
 * })
 * 
 * <button onClick={handleClick}>
 *   کلیک کنید
 * </button>
 */
// Counter برای ایجاد ID منحصر به فرد
let instanceCounter = 0

export function useRateLimit(options: UseRateLimitOptions = {}) {
  const { minInterval = 2000, message = 'لطفاً صبر کنید قبل از کلیک مجدد', key } = options
  const instanceIdRef = useRef<string | null>(null)
  
  // تنظیم instanceId فقط یک بار
  if (instanceIdRef.current === null) {
    instanceIdRef.current = key || `rate-limit-${++instanceCounter}-${Date.now()}`
  }
  
  const { showToast } = useToast()

  return useCallback(
    <T extends (...args: any[]) => any>(fn: T): ((...args: Parameters<T>) => ReturnType<T> | void) => {
      return (...args: Parameters<T>) => {
        const instanceId = instanceIdRef.current!
        const now = Date.now()
        const lastClickTime = globalLastClickTimes.get(instanceId) || 0
        const timeSinceLastClick = now - lastClickTime

        if (timeSinceLastClick < minInterval) {
          const remainingTime = ((minInterval - timeSinceLastClick) / 1000).toFixed(1)
          showToast(`${message} (${remainingTime} ثانیه باقی مانده)`, { type: 'warning', duration: 2000 })
          return
        }

        globalLastClickTimes.set(instanceId, now)
        return fn(...args)
      }
    },
    [minInterval, message, showToast]
  )
}

