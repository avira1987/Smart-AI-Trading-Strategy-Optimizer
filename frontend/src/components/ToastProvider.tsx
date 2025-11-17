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
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={
              `px-4 py-2 rounded shadow-lg text-white transition-opacity ` +
              (t.type === 'success' ? 'bg-green-600' : '') +
              (t.type === 'error' ? 'bg-red-600' : '') +
              (t.type === 'warning' ? 'bg-yellow-600' : '') +
              (t.type === 'info' ? 'bg-blue-600' : '')
            }
            style={{ direction: 'rtl', textAlign: 'right', unicodeBidi: 'plaintext' }}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
