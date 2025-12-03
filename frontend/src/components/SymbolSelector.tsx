import { useMemo, useState, useEffect } from 'react'
import { useSymbol } from '../context/SymbolContext'
import { updateProfile } from '../api/auth'
import { useToast } from './ToastProvider'
import { getMT5Symbols, MT5Symbol } from '../api/client'

export default function SymbolSelector() {
  const { selectedSymbol, setSelectedSymbol } = useSymbol()
  const { showToast } = useToast()
  const [mt5Symbols, setMt5Symbols] = useState<MT5Symbol[]>([])
  const [, setLoadingSymbols] = useState(false)

  type SymbolOption = {
    value: string
    label: string
    category: 'gold' | 'forex' | 'crypto'
  }

  // Default symbols (fallback)
  const defaultOptions: SymbolOption[] = [
    // طلا (Gold)
    { value: 'XAUUSD', label: 'XAUUSD - طلا/دلار', category: 'gold' },
    { value: 'XAUUSD_o', label: 'XAUUSD_o - طلا (Demo)', category: 'gold' },
    { value: 'XAUUSD_l', label: 'XAUUSD_l - طلا (Live)', category: 'gold' },
    
    // فارکس (Forex) - جفت ارزهای اصلی
    { value: 'EURUSD', label: 'EURUSD - یورو/دلار', category: 'forex' },
    { value: 'GBPUSD', label: 'GBPUSD - پوند/دلار', category: 'forex' },
    { value: 'USDJPY', label: 'USDJPY - دلار/ین', category: 'forex' },
    { value: 'USDCHF', label: 'USDCHF - دلار/فرانک', category: 'forex' },
    { value: 'AUDUSD', label: 'AUDUSD - دلار استرالیا/دلار', category: 'forex' },
    { value: 'USDCAD', label: 'USDCAD - دلار/دلار کانادا', category: 'forex' },
    { value: 'NZDUSD', label: 'NZDUSD - دلار نیوزیلند/دلار', category: 'forex' },
    { value: 'EURGBP', label: 'EURGBP - یورو/پوند', category: 'forex' },
    { value: 'EURJPY', label: 'EURJPY - یورو/ین', category: 'forex' },
    { value: 'GBPJPY', label: 'GBPJPY - پوند/ین', category: 'forex' },
    
    // کریپتو (Cryptocurrency) - ارزهای دیجیتال معروف
    { value: 'BTCUSD', label: 'BTCUSD - بیت‌کوین/دلار', category: 'crypto' },
    { value: 'ETHUSD', label: 'ETHUSD - اتریوم/دلار', category: 'crypto' },
    { value: 'BNBUSD', label: 'BNBUSD - بایننس کوین/دلار', category: 'crypto' },
    { value: 'ADAUSD', label: 'ADAUSD - کاردانو/دلار', category: 'crypto' },
    { value: 'SOLUSD', label: 'SOLUSD - سولانا/دلار', category: 'crypto' },
    { value: 'XRPUSD', label: 'XRPUSD - ریپل/دلار', category: 'crypto' },
    { value: 'DOTUSD', label: 'DOTUSD - پولکادات/دلار', category: 'crypto' },
    { value: 'DOGEUSD', label: 'DOGEUSD - دوج کوین/دلار', category: 'crypto' },
    { value: 'AVAXUSD', label: 'AVAXUSD - آوالانچ/دلار', category: 'crypto' },
    { value: 'MATICUSD', label: 'MATICUSD - پولیگان/دلار', category: 'crypto' },
  ]

  // Load MT5 symbols on mount
  useEffect(() => {
    const loadMT5Symbols = async () => {
      setLoadingSymbols(true)
      try {
        const response = await getMT5Symbols(true) // Only get available symbols
        if (response.data.status === 'success') {
          setMt5Symbols(response.data.symbols)
        }
      } catch (error) {
        console.error('Error loading MT5 symbols:', error)
        // If MT5 is not available, use default symbols
      } finally {
        setLoadingSymbols(false)
      }
    }
    
    loadMT5Symbols()
  }, [])

  // Helper function to detect category from symbol name
  const detectCategory = (symbolName: string): 'gold' | 'forex' | 'crypto' => {
    const name = symbolName.toUpperCase()
    if (name.includes('XAU') || name.includes('GOLD')) {
      return 'gold'
    }
    if (name.includes('BTC') || name.includes('ETH') || name.includes('CRYPTO')) {
      return 'crypto'
    }
    return 'forex'
  }

  // Combine MT5 symbols with default options
  const options = useMemo<SymbolOption[]>(() => {
    const symbolMap = new Map<string, SymbolOption>()
    
    // First, add all default options
    defaultOptions.forEach(opt => {
      symbolMap.set(opt.value, opt)
    })
    
    // Then, add available MT5 symbols (they will override defaults if same name)
    mt5Symbols.forEach(mt5Symbol => {
      if (mt5Symbol.is_available) {
        const existing = symbolMap.get(mt5Symbol.name)
        if (existing) {
          // Update existing with MT5 info
          symbolMap.set(mt5Symbol.name, {
            ...existing,
            label: `${mt5Symbol.name}${mt5Symbol.description ? ` - ${mt5Symbol.description}` : ''}`
          })
        } else {
          // Add new symbol from MT5
          symbolMap.set(mt5Symbol.name, {
            value: mt5Symbol.name,
            label: `${mt5Symbol.name}${mt5Symbol.description ? ` - ${mt5Symbol.description}` : ''}`,
            category: detectCategory(mt5Symbol.name)
          })
        }
      }
    })
    
    return Array.from(symbolMap.values())
  }, [mt5Symbols])

  const handleSymbolChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSymbol = e.target.value
    setSelectedSymbol(newSymbol)
    
    // Save to profile
    try {
      await updateProfile(undefined, undefined, newSymbol)
      showToast('نماد معاملاتی با موفقیت ذخیره شد', { type: 'success', duration: 2000 })
    } catch (error) {
      console.error('Error saving symbol:', error)
      // Don't show error toast, just log it - symbol is still changed in context
    }
  }

  // Group options by category for better organization
  const groupedOptions = useMemo(() => {
    const groups: { gold: SymbolOption[]; forex: SymbolOption[]; crypto: SymbolOption[] } = {
      gold: [],
      forex: [],
      crypto: []
    }
    options.forEach(opt => {
      groups[opt.category].push(opt)
    })
    return groups
  }, [options])

  return (
    <div className="w-full">
      <select
        value={selectedSymbol}
        onChange={handleSymbolChange}
        className="w-full px-4 py-2 text-sm bg-gray-700 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        <optgroup label="طلا (Gold)">
          {groupedOptions.gold.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </optgroup>
        <optgroup label="فارکس (Forex)">
          {groupedOptions.forex.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </optgroup>
        <optgroup label="کریپتو (Cryptocurrency)">
          {groupedOptions.crypto.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </optgroup>
      </select>
    </div>
  )
}


