import { useMemo } from 'react'
import { useSymbol } from '../context/SymbolContext'

export default function SymbolSelector() {
  const { selectedSymbol, setSelectedSymbol } = useSymbol()

  const options = useMemo(
    () => [
      { value: 'XAUUSD', label: 'XAUUSD (Auto)' },
      { value: 'XAUUSD_o', label: 'XAUUSD_o (Demo)' },
      { value: 'XAUUSD_l', label: 'XAUUSD_l (Live)' },
    ],
    []
  )

  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-gray-300">نماد:</label>
      <select
        value={selectedSymbol}
        onChange={(e) => setSelectedSymbol(e.target.value)}
        className="px-2 py-1 text-sm bg-gray-700 text-white rounded border border-gray-600"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  )
}


