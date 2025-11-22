import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'

export type ToastType = 'info' | 'success' | 'error' | 'warning'

export interface Toast {
  id: number
  message: string
  type: ToastType
  duration: number
}

interface ToastContextValue {
  showToast: (message: string, options?: { type?: ToastType; duration?: number }) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) {
    throw new Error('useToast must be used within <ToastProvider>')
  }
  return ctx
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const idRef = useRef(1)

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const showToast = useCallback(
    (message: string, options?: { type?: ToastType; duration?: number }) => {
      const id = idRef.current++
      const type = options?.type ?? 'info'
      const duration = Math.max(2000, options?.duration ?? 6000)
      setToasts((prev) => [...prev, { id, message, type, duration }])
      window.setTimeout(() => removeToast(id), duration)
    },
    [removeToast]
  )

  const value = useMemo(() => ({ showToast }), [showToast])

  return (
    <ToastContext.Provider value={value}>
      {children}
      {/* Toast Container */}
      <div className="fixed top-4 right-4 z-50 space-y-2 direction-rtl" style={{ direction: 'rtl' }}>
        {toasts.map((t) => (
          <div
            key={t.id}
            className={
              `px-4 py-3 rounded-lg shadow-lg text-white transition-all duration-300 max-w-md direction-rtl text-right ` +
              (t.type === 'success' ? 'bg-green-600' : '') +
              (t.type === 'error' ? 'bg-red-600' : '') +
              (t.type === 'warning' ? 'bg-yellow-600' : '') +
              (t.type === 'info' ? 'bg-blue-600' : '')
            }
            style={{ 
              direction: 'rtl', 
              textAlign: 'right',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontSize: '14px',
              lineHeight: '1.6'
            }}
          >
            {t.message.split('\n').map((line, index, array) => (
              <div 
                key={index} 
                className="direction-rtl text-right"
                style={{ direction: 'rtl', textAlign: 'right' }}
              >
                {line}
                {index < array.length - 1 && <br />}
              </div>
            ))}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
