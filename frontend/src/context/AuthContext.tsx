import { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react'
import { checkAuth, logout as logoutAPI } from '../api/auth'
import type { GoldAPIAccessInfo } from '../api/client'

interface User {
  id: number
  username: string
  phone_number: string
  nickname?: string
  email?: string
  first_name?: string
  last_name?: string
  is_staff?: boolean
  is_superuser?: boolean
  gold_api_access?: GoldAPIAccessInfo
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  deviceId: string | null
  isAdmin: boolean
  login: (user: User, deviceId: string) => void
  logout: () => Promise<void>
  checkAuthentication: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [deviceId, setDeviceId] = useState<string | null>(null)
  const isAdmin = user ? Boolean(user.is_staff || user.is_superuser) : false
  const loadingTimeoutRef = useRef<number | null>(null)

  const checkAuthentication = async (showLoading: boolean = false) => {
    try {
      // Only show loading on initial mount, not on periodic checks
      if (showLoading) {
        setIsLoading(true)
      }
      
      // Add shorter timeout for mobile devices (5 seconds instead of 8)
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Authentication timeout')), 5000)
      })
      
      const response = await Promise.race([checkAuth(), timeoutPromise]) as Awaited<ReturnType<typeof checkAuth>>
      
      if (response.success && response.authenticated && response.user) {
        setUser(response.user)
        setIsAuthenticated(true)
        setDeviceId(response.device_id || null)
        
        // Store in localStorage for persistence
        localStorage.setItem('user', JSON.stringify(response.user))
        if (response.device_id) {
          localStorage.setItem('device_id', response.device_id)
        }
      } else {
        // Only clear auth state if we're not authenticated
        // Don't clear on errors during periodic checks to avoid disrupting user
        setUser(null)
        setIsAuthenticated(false)
        setDeviceId(null)
        localStorage.removeItem('user')
        localStorage.removeItem('device_id')
      }
    } catch (error: any) {
      // On error during periodic check, don't disrupt the user session
      // Only clear auth state if this is the initial check
      console.error('Authentication check error:', error)
      
      // Check if there's cached user data to use as fallback
      const cachedUser = localStorage.getItem('user')
      const cachedDeviceId = localStorage.getItem('device_id')
      
      if (showLoading) {
        // On initial load error, check if we have cached data
        if (cachedUser && cachedDeviceId) {
          try {
            const user = JSON.parse(cachedUser)
            setUser(user)
            setIsAuthenticated(true)
            setDeviceId(cachedDeviceId)
            console.log('Using cached authentication data due to connection error')
            // Don't set loading to false here, let finally block handle it
          } catch (e) {
            // If cached data is invalid, clear it
            setUser(null)
            setIsAuthenticated(false)
            setDeviceId(null)
            localStorage.removeItem('user')
            localStorage.removeItem('device_id')
          }
        } else {
          // No cached data, clear auth state
          setUser(null)
          setIsAuthenticated(false)
          setDeviceId(null)
          localStorage.removeItem('user')
          localStorage.removeItem('device_id')
        }
      }
      // For periodic checks, don't clear auth state to avoid disrupting user
    } finally {
      // Always set loading to false, even on error
      if (showLoading) {
        setIsLoading(false)
        // Clear the fallback timeout if authentication check completed
        if (loadingTimeoutRef.current) {
          clearTimeout(loadingTimeoutRef.current)
          loadingTimeoutRef.current = null
        }
      }
    }
  }

  useEffect(() => {
    // Set fallback timeout immediately - if loading takes too long, stop it
    loadingTimeoutRef.current = setTimeout(() => {
      console.warn('Authentication loading timeout - forcing stop after 6 seconds')
      setIsLoading(false)
    }, 6000)
    
    // Check authentication on mount with loading indicator
    checkAuthentication(true)
    
    // Check authentication periodically (every 5 minutes) without loading indicator
    // This prevents page refreshes and UI disruptions
    const interval = setInterval(() => {
      checkAuthentication(false)
    }, 5 * 60 * 1000)
    
    return () => {
      clearInterval(interval)
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current)
        loadingTimeoutRef.current = null
      }
    }
  }, [])

  const login = (userData: User, deviceIdData: string) => {
    setUser(userData)
    setIsAuthenticated(true)
    setDeviceId(deviceIdData)
    localStorage.setItem('user', JSON.stringify(userData))
    localStorage.setItem('device_id', deviceIdData)
  }

  const logout = async () => {
    try {
      await logoutAPI()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setUser(null)
      setIsAuthenticated(false)
      setDeviceId(null)
      localStorage.removeItem('user')
      localStorage.removeItem('device_id')
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        deviceId,
        isAdmin,
        login,
        logout,
        checkAuthentication,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

