import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react'
import { getSystemSettings, type SystemSettingsResponse } from '../api/client'

interface FeatureFlagsContextValue {
  liveTradingEnabled: boolean
  isLoading: boolean
  reload: () => Promise<void>
}

const FeatureFlagsContext = createContext<FeatureFlagsContextValue | undefined>(undefined)

export function FeatureFlagsProvider({ children }: { children: ReactNode }) {
  const [liveTradingEnabled, setLiveTradingEnabled] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const fetchFlags = useCallback(async () => {
    try {
      const response = await getSystemSettings()
      const data: SystemSettingsResponse = response.data
      setLiveTradingEnabled(Boolean(data.live_trading_enabled))
      setIsLoading(false)
    } catch (error) {
      console.error('Failed to load system settings:', error)
      setLiveTradingEnabled(false)
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchFlags()
  }, [fetchFlags])

  const value: FeatureFlagsContextValue = {
    liveTradingEnabled,
    isLoading,
    reload: fetchFlags,
  }

  return <FeatureFlagsContext.Provider value={value}>{children}</FeatureFlagsContext.Provider>
}

export function useFeatureFlags() {
  const context = useContext(FeatureFlagsContext)
  if (!context) {
    throw new Error('useFeatureFlags must be used within a FeatureFlagsProvider')
  }
  return context
}
