import { Navigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { checkProfileCompletion } from '../api/auth'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()
  const [profileCheckLoading, setProfileCheckLoading] = useState(true)
  const [profileComplete, setProfileComplete] = useState(true)
  const isCompleteProfilePage = location.pathname === '/complete-profile'

  useEffect(() => {
    // If not authenticated or on complete profile page, don't check profile
    if (!isAuthenticated || isCompleteProfilePage) {
      setProfileCheckLoading(false)
      return
    }

    // If still loading auth, don't check profile yet
    if (isLoading) {
      return
    }

    const checkProfile = async () => {
      // Check if user has skipped profile completion recently
      const skipUntil = localStorage.getItem('skip_profile_completion')
      if (skipUntil) {
        const skipTime = parseInt(skipUntil, 10)
        if (Date.now() < skipTime) {
          // User has skipped profile completion and it's still valid
          setProfileCheckLoading(false)
          setProfileComplete(true) // Allow access
          return
        } else {
          // Skip time has expired, remove the flag
          localStorage.removeItem('skip_profile_completion')
        }
      }

      try {
        // Add timeout for profile check (3 seconds for mobile)
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Profile check timeout')), 3000)
        })
        
        const response = await Promise.race([checkProfileCompletion(), timeoutPromise]) as Awaited<ReturnType<typeof checkProfileCompletion>>
        if (response.success) {
          setProfileComplete(response.is_complete)
        }
      } catch (error) {
        console.error('Error checking profile completion:', error)
        // On error, assume profile is complete to avoid blocking access
        setProfileComplete(true)
      } finally {
        setProfileCheckLoading(false)
      }
    }

    checkProfile()
  }, [isAuthenticated, isLoading, isCompleteProfilePage])

  // Fallback: if loading takes too long (6 seconds), stop loading
  useEffect(() => {
    if (profileCheckLoading) {
      const fallbackTimeout = setTimeout(() => {
        console.warn('Profile check loading timeout - allowing access')
        setProfileCheckLoading(false)
        setProfileComplete(true)
      }, 6000)
      
      return () => clearTimeout(fallbackTimeout)
    }
  }, [profileCheckLoading])

  if (isLoading || profileCheckLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
          <div className="text-white text-xl mb-2">در حال بارگذاری...</div>
          <div className="text-gray-400 text-sm mt-4">
            اگر بارگذاری طولانی شد، لطفاً صفحه را رفرش کنید
          </div>
          <a
            href="https://t.me/avxsupport"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.174 1.586-.927 5.442-1.31 7.22-.15.685-.445.913-.731.877-.384-.045-1.05-.206-1.63-.402-.645-.206-1.13-.32-1.828-.513-.72-.206-1.27-.319-1.97.319-.595.536-2.31 2.233-3.385 3.014-.38.319-.647.479-1.015.479-.67-.045-1.22-.492-1.89-.96-.693-.48-1.245-1.002-1.89-1.68-.65-.685-2.29-2.01-2.31-2.34-.02-.11.16-.32.445-.536 1.83-1.61 3.05-2.73 3.89-3.27.17-.11.38-.21.595-.21.32 0 .52.15.7.493 1.15 2.19 2.54 4.24 3.85 4.24.32 0 .64-.11.87-.32.35-.32.64-.7.93-1.08.6-.75 1.33-1.68 2.15-2.71.19-.24.38-.48.64-.48.15 0 .32.08.41.24.18.32.15.7.11 1.08z"/>
            </svg>
            پشتیبانی تلگرام
          </a>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // If profile is not complete and we're not on the complete-profile page, redirect
  if (!profileComplete && !isCompleteProfilePage) {
    return <Navigate to="/complete-profile" replace />
  }

  return <>{children}</>
}

