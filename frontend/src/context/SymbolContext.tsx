import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { getAccountInfo } from '../api/client'

type SymbolContextValue = {
  selectedSymbol: string
  setSelectedSymbol: (s: string) => void
}

const SymbolContext = createContext<SymbolContextValue | undefined>(undefined)

export function SymbolProvider({ children }: { children: React.ReactNode }) {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('XAUUSD')

  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const response = await getAccountInfo()
        if (mounted && response?.data?.recommended_symbol) {
          setSelectedSymbol(response.data.recommended_symbol)
        }
      } catch (_) {
        // ignore if not available
      }
    })()
    return () => {
      mounted = false
    }
  }, [])

  const value = useMemo(() => ({ selectedSymbol, setSelectedSymbol }), [selectedSymbol])

  return <SymbolContext.Provider value={value}>{children}</SymbolContext.Provider>
}

export function useSymbol() {
  const ctx = useContext(SymbolContext)
  if (!ctx) throw new Error('useSymbol must be used within SymbolProvider')
  return ctx
}


