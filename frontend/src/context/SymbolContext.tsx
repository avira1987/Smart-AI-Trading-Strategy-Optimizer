import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { getAccountInfo } from '../api/client'
import { checkProfileCompletion } from '../api/auth'
import { useAuth } from './AuthContext'

type SymbolContextValue = {
  selectedSymbol: string
  setSelectedSymbol: (s: string) => void
}

const SymbolContext = createContext<SymbolContextValue | undefined>(undefined)

export function SymbolProvider({ children }: { children: React.ReactNode }) {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('XAUUSD')
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    if (!isAuthenticated) {
      setSelectedSymbol('XAUUSD')
      return
    }

    let mounted = true
    ;(async () => {
      try {
        // First try to get from profile
        try {
          const profileResponse = await checkProfileCompletion()
          if (mounted && profileResponse?.preferred_symbol) {
            setSelectedSymbol(profileResponse.preferred_symbol)
            return
          }
        } catch (_) {
          // If profile check fails, try account info
        }
        
        // Fallback to account info
        const response = await getAccountInfo()
        if (mounted && response?.data?.recommended_symbol) {
          setSelectedSymbol(response.data.recommended_symbol)
        }
      } catch (_) {
        // ignore if not available, use default
      }
    })()
    return () => {
      mounted = false
    }
  }, [isAuthenticated])

  const value = useMemo(() => ({ selectedSymbol, setSelectedSymbol }), [selectedSymbol])

  return <SymbolContext.Provider value={value}>{children}</SymbolContext.Provider>
}

export function useSymbol() {
  const ctx = useContext(SymbolContext)
  if (!ctx) throw new Error('useSymbol must be used within SymbolProvider')
  return ctx
}


