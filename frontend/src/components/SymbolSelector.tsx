import { useMemo } from 'react'
import { useSymbol } from '../context/SymbolContext'
import { updateProfile } from '../api/auth'
import { useToast } from './ToastProvider'

export default function SymbolSelector() {
  const { selectedSymbol, setSelectedSymbol } = useSymbol()
  const { showToast } = useToast()

  type SymbolOption = {
    value: string
    label: string
    category: 'gold' | 'forex' | 'crypto'
  }

  const options = useMemo<SymbolOption[]>(
    () => [
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
    ],
    []
  )

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


