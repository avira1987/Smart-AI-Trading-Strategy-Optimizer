import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { checkProfileCompletion } from '../api/auth'
import { useAuth } from './AuthContext'

type ProfileCompletionContextValue = {
  isComplete: boolean | null
  isChecking: boolean
  shouldRemind: boolean
  refresh: () => Promise<void>
  markComplete: () => void
  snooze: (durationMs?: number) => void
}

const ProfileCompletionContext = createContext<ProfileCompletionContextValue | undefined>(undefined)

const SKIP_KEY = 'skip_profile_completion'
const DEFAULT_SNOOZE_MS = 24 * 60 * 60 * 1000

function readSkipUntil() {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const storedValue = window.localStorage.getItem(SKIP_KEY)
    if (!storedValue) {
      return null
    }
    const parsed = parseInt(storedValue, 10)
    if (Number.isNaN(parsed) || parsed <= Date.now()) {
      window.localStorage.removeItem(SKIP_KEY)
      return null
    }
    return parsed
  } catch (error) {
    console.error('Failed to read skip profile completion timestamp:', error)
    return null
  }
}

export function ProfileCompletionProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const [isComplete, setIsComplete] = useState<boolean | null>(null)
  const [isChecking, setIsChecking] = useState(false)
  const [skipUntil, setSkipUntil] = useState<number | null>(() => readSkipUntil())
  const refreshInFlightRef = useRef<Promise<void> | null>(null)

  const clearSkip = useCallback(() => {
    if (typeof window !== 'undefined') {
      try {
        window.localStorage.removeItem(SKIP_KEY)
      } catch (error) {
        console.error('Failed to clear skip profile completion timestamp:', error)
      }
    }
    setSkipUntil(null)
  }, [])

  const applySkipUntil = useCallback((targetTimestamp: number | null) => {
    if (typeof window === 'undefined') {
      setSkipUntil(targetTimestamp)
      return
    }

    if (!targetTimestamp) {
      clearSkip()
      return
    }

    try {
      window.localStorage.setItem(SKIP_KEY, targetTimestamp.toString())
      setSkipUntil(targetTimestamp)
    } catch (error) {
      console.error('Failed to persist skip profile completion timestamp:', error)
      setSkipUntil(targetTimestamp)
    }
  }, [clearSkip])

  const refresh = useCallback(async () => {
    if (!isAuthenticated) {
      setIsComplete(null)
      setIsChecking(false)
      refreshInFlightRef.current = null
      return
    }

    if (refreshInFlightRef.current) {
      return refreshInFlightRef.current
    }

    const refreshPromise = (async () => {
      setIsChecking(true)
      try {
        const response = await checkProfileCompletion()
        if (response.success) {
          setIsComplete(response.is_complete)
        } else {
          // On failure response, assume complete to avoid blocking UX
          setIsComplete(true)
        }

        if (response.is_complete) {
          clearSkip()
        }
      } catch (error) {
        console.error('Failed to refresh profile completion state:', error)
        // Prevent disruptive reminders when status is unknown
        setIsComplete(true)
      } finally {
        setIsChecking(false)
        refreshInFlightRef.current = null
      }
    })()

    refreshInFlightRef.current = refreshPromise
    return refreshPromise
  }, [isAuthenticated, clearSkip])

  const markComplete = useCallback(() => {
    setIsComplete(true)
    clearSkip()
  }, [clearSkip])

  const snooze = useCallback((durationMs: number = DEFAULT_SNOOZE_MS) => {
    const target = Date.now() + durationMs
    applySkipUntil(target)
  }, [applySkipUntil])

  useEffect(() => {
    if (!skipUntil) {
      return
    }

    const now = Date.now()
    if (skipUntil <= now) {
      clearSkip()
      return
    }

    const timeout = window.setTimeout(() => {
      clearSkip()
    }, skipUntil - now)

    return () => window.clearTimeout(timeout)
  }, [skipUntil, clearSkip])

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const handleStorage = (event: StorageEvent) => {
      if (event.key !== SKIP_KEY) {
        return
      }

      if (!event.newValue) {
        setSkipUntil(null)
        return
      }

      const parsed = parseInt(event.newValue, 10)
      if (Number.isNaN(parsed)) {
        setSkipUntil(null)
        return
      }
      setSkipUntil(parsed)
    }

    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  useEffect(() => {
    if (isLoading) {
      return
    }

    if (!isAuthenticated) {
      setIsComplete(null)
      setIsChecking(false)
      clearSkip()
      return
    }

    refresh().catch((error) => {
      console.error('Profile completion refresh error:', error)
    })
  }, [isAuthenticated, isLoading, refresh, clearSkip])

  const shouldRemind = useMemo(() => {
    if (!isAuthenticated) {
      return false
    }
    if (isComplete !== false) {
      return false
    }
    if (!skipUntil) {
      return true
    }
    return skipUntil <= Date.now()
  }, [isAuthenticated, isComplete, skipUntil])

  const value = useMemo<ProfileCompletionContextValue>(() => ({
    isComplete,
    isChecking,
    shouldRemind,
    refresh,
    markComplete,
    snooze,
  }), [isComplete, isChecking, shouldRemind, refresh, markComplete, snooze])

  return (
    <ProfileCompletionContext.Provider value={value}>
      {children}
    </ProfileCompletionContext.Provider>
  )
}

export function useProfileCompletion() {
  const context = useContext(ProfileCompletionContext)
  if (!context) {
    throw new Error('useProfileCompletion must be used within a ProfileCompletionProvider')
  }
  return context
}


