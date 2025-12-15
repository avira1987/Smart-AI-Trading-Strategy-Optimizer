/**
 * سیستم ردیابی Analytics برای Frontend
 * ردیابی جلسات و بازدید صفحات
 */

import { trackSession, trackPageVisit, endPageVisit, endSession } from '../api/client'

// تولید شناسه یکتا برای جلسه
function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// ذخیره session ID در localStorage
const SESSION_ID_KEY = 'analytics_session_id'
const CURRENT_VISIT_ID_KEY = 'analytics_current_visit_id'

class AnalyticsTracker {
  private sessionId: string | null = null
  private currentVisitId: number | null = null
  private isTracking: boolean = false

  /**
   * شروع ردیابی
   */
  async startTracking(deviceId?: string): Promise<void> {
    if (this.isTracking) {
      return
    }

    // دریافت یا ایجاد session ID
    const storedSessionId = localStorage.getItem(SESSION_ID_KEY)
    if (storedSessionId) {
      this.sessionId = storedSessionId
    } else {
      this.sessionId = generateSessionId()
      localStorage.setItem(SESSION_ID_KEY, this.sessionId)
    }

    this.isTracking = true

    try {
      await trackSession(this.sessionId, deviceId)
    } catch (error) {
      console.error('Error tracking session:', error)
    }
  }

  /**
   * ردیابی بازدید صفحه
   */
  async trackPage(pagePath: string, pageTitle?: string): Promise<void> {
    if (!this.isTracking || !this.sessionId) {
      await this.startTracking()
    }

    // پایان بازدید قبلی
    if (this.currentVisitId) {
      try {
        await endPageVisit(this.currentVisitId)
      } catch (error) {
        console.error('Error ending previous visit:', error)
      }
    }

    // شروع بازدید جدید
    const referrer = document.referrer || undefined

    try {
      const response = await trackPageVisit(
        this.sessionId!,
        pagePath,
        pageTitle || document.title,
        referrer
      )
      this.currentVisitId = response.data.visit_id
      localStorage.setItem(CURRENT_VISIT_ID_KEY, this.currentVisitId.toString())
    } catch (error) {
      console.error('Error tracking page visit:', error)
    }
  }

  /**
   * پایان بازدید صفحه
   */
  async endPageVisit(): Promise<void> {
    if (this.currentVisitId) {
      try {
        await endPageVisit(this.currentVisitId)
        this.currentVisitId = null
        localStorage.removeItem(CURRENT_VISIT_ID_KEY)
      } catch (error) {
        console.error('Error ending page visit:', error)
      }
    }
  }

  /**
   * پایان جلسه
   */
  async endSession(): Promise<void> {
    if (!this.isTracking || !this.sessionId) {
      return
    }

    // پایان بازدید فعلی
    await this.endPageVisit()

    try {
      await endSession(this.sessionId)
      this.sessionId = null
      this.isTracking = false
      localStorage.removeItem(SESSION_ID_KEY)
    } catch (error) {
      console.error('Error ending session:', error)
    }
  }

  /**
   * دریافت session ID
   */
  getSessionId(): string | null {
    return this.sessionId || localStorage.getItem(SESSION_ID_KEY)
  }

  /**
   * بررسی وضعیت ردیابی
   */
  isActive(): boolean {
    return this.isTracking
  }
}

// ایجاد instance یکتا
const analyticsTracker = new AnalyticsTracker()

// ردیابی خودکار هنگام تغییر صفحه (برای React Router)
export function setupPageTracking() {
  // ردیابی صفحه اول
  const currentPath = window.location.pathname
  analyticsTracker.trackPage(currentPath)

  // ردیابی تغییرات مسیر (برای SPA)
  let lastPath = currentPath
  const observer = new MutationObserver(() => {
    const newPath = window.location.pathname
    if (newPath !== lastPath) {
      lastPath = newPath
      analyticsTracker.trackPage(newPath)
    }
  })

  observer.observe(document.body, {
    childList: true,
    subtree: true
  })

  // ردیابی هنگام بستن صفحه
  window.addEventListener('beforeunload', () => {
    analyticsTracker.endPageVisit()
    analyticsTracker.endSession()
  })

  // ردیابی هنگام تغییر visibility
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      analyticsTracker.endPageVisit()
    } else {
      const currentPath = window.location.pathname
      analyticsTracker.trackPage(currentPath)
    }
  })
}

export default analyticsTracker

