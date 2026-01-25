import { useState, useEffect } from 'react'
import { getLiveTrades, getAccountInfo, closeTrade, syncPositions, getForwardTestReports, buildForwardTestReport, getAutoTradingSettings, toggleAutoTrading, deleteAutoTradingSettings, LiveTrade, AccountInfo, ForwardTestReport, AutoTradingSettings } from '../api/client'
import { useToast } from './ToastProvider'
import { useRateLimit } from '../hooks/useRateLimit'

const REFRESH_INTERVAL_MS = 30000

export default function LiveTrading() {
  const [trades, setTrades] = useState<LiveTrade[]>([])
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null)
  const [reports, setReports] = useState<ForwardTestReport[]>([])
  const [activeTab, setActiveTab] = useState<'monitoring' | 'trades' | 'reports'>('monitoring')
  const [deployedStrategies, setDeployedStrategies] = useState<AutoTradingSettings[]>([])
  const [loadingStrategies, setLoadingStrategies] = useState(false)
  const { showToast } = useToast()
  
  const normalizeArrayResponse = <T = any>(data: any): T[] => {
    if (!data) return []
    if (Array.isArray(data)) return data
    if (Array.isArray(data?.results)) return data.results
    if (Array.isArray(data?.data)) return data.data
    if (Array.isArray(data?.data?.results)) return data.data.results
    if (Array.isArray(data?.results?.data)) return data.results.data
    return []
  }

  const rateLimitClickCloseTrade = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'liveTrading-closeTrade' })
  const rateLimitClickSync = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'liveTrading-sync' })
  const rateLimitClickToggleMonitoring = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'liveTrading-toggleMonitoring' })
  const rateLimitClickDeleteMonitoring = useRateLimit({ minInterval: 2000, message: 'لطفاً صبر کنید قبل از کلیک مجدد', key: 'liveTrading-deleteMonitoring' })

  useEffect(() => {
    loadData()
    const interval = setInterval(() => {
      if (typeof document !== 'undefined' && document.hidden) return
      refreshData()
    }, REFRESH_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      // Sequential calls or wrapped Promise.all to avoid one failure blocking everything
      await loadTrades(false).catch(e => console.error('Error loading trades:', e))
      await loadAccountInfo().catch(e => console.error('Error loading account info:', e))
      await loadReports().catch(e => console.error('Error loading reports:', e))
      await loadDeployedStrategies().catch(e => console.error('Error loading strategies:', e))
    } catch (error: any) {
      console.error('Error in loadData:', error)
      showToast('خطا در بارگذاری برخی داده‌ها', { type: 'error' })
    }
  }

  const loadDeployedStrategies = async () => {
    try {
      setLoadingStrategies(true)
      console.log('Fetching deployed strategies...')
      const response = await getAutoTradingSettings()
      console.log('Deployed strategies raw response:', response)
      
      const data = normalizeArrayResponse<AutoTradingSettings>(response.data)
      console.log('Normalized deployed strategies:', data)
      
      setDeployedStrategies(data)
    } catch (error: any) {
      console.error('Error loading deployed strategies:', error)
      showToast('خطا در بارگذاری استراتژی‌های مستقر شده', { type: 'error' })
    } finally {
      setLoadingStrategies(false)
    }
  }

  const refreshData = async () => {
    try {
      await Promise.all([
        loadTrades(true),
        loadAccountInfo(),
        loadDeployedStrategies(),
      ])
    } catch (error) {}
  }

  const loadTrades = async (silent: boolean = false) => {
    try {
      const response = await getLiveTrades()
      let data = response.data as any
      setTrades(Array.isArray(data) ? data : (data.results || []))
    } catch (error: any) {
      if (!silent) showToast('خطا در بارگذاری معاملات', { type: 'error' })
      setTrades([])
    }
  }

  const loadReports = async () => {
    try {
      const response = await getForwardTestReports()
      let data = response.data as any
      setReports(Array.isArray(data) ? data : (data.results || []))
    } catch (error) {}
  }

  const loadAccountInfo = async () => {
    try {
      const response = await getAccountInfo()
      if (response.data.status === 'success') {
        setAccountInfo(response.data.account)
      }
    } catch (error) {}
  }

  const handleBuildReport = async (strategyId: number) => {
      try {
      const response = await buildForwardTestReport(strategyId)
        if (response.data.status === 'success') {
        showToast('گزارش راستی‌آزمایی با موفقیت بیلد شد', { type: 'success' })
        await loadReports()
        setActiveTab('reports')
        }
      } catch (error: any) {
      showToast(error.response?.data?.message || 'خطا در بیلد گزارش', { type: 'error' })
      }
  }

  const handleCloseTrade = (tradeId: number) => {
    if (!confirm('آیا مطمئن هستید؟')) return
    const closeTradeAction = rateLimitClickCloseTrade(async () => {
      try {
        const response = await closeTrade(tradeId)
        if (response.data.status === 'success') {
          showToast('معامله بسته شد', { type: 'success' })
          await loadTrades(true)
          await loadAccountInfo()
        }
      } catch (error: any) {
        showToast('خطا در بستن معامله', { type: 'error' })
      }
    })
    closeTradeAction()
  }

  const handleSyncPositions = rateLimitClickSync(async () => {
    try {
      const response = await syncPositions()
      if (response.data.status === 'success') {
        showToast(`همگام‌سازی انجام شد`, { type: 'success' })
        await loadTrades(true)
      }
    } catch (error: any) {
      showToast('خطا در همگام‌سازی', { type: 'error' })
    }
  })

  const handleDeleteMonitoring = (settingId: number) => {
    if (!confirm('آیا از حذف این استراتژی از پایش مطمئن هستید؟')) return

    const deleteAction = rateLimitClickDeleteMonitoring(async () => {
      try {
        const response = await deleteAutoTradingSettings(settingId)
        if (!response || response.status === 204 || response.data?.status === 'success') {
          showToast('استراتژی از فهرست پایش حذف شد', { type: 'success' })
          await loadDeployedStrategies()
        } else {
          const message =
            response.data?.message ||
            'خطا در حذف استراتژی از پایش'
          showToast(message, { type: 'error' })
        }
      } catch (error: any) {
        const message =
          error?.response?.data?.message ||
          error?.response?.data?.detail ||
          error?.message ||
          'خطا در حذف استراتژی از پایش'
        showToast(message, { type: 'error' })
      }
    })

    deleteAction()
  }

  const handleToggleMonitoring = (settingId: number) => {
    const toggleAction = rateLimitClickToggleMonitoring(async () => {
      try {
        const response = await toggleAutoTrading(settingId)
        if (response.data.status === 'success') {
          const isEnabled = response.data.is_enabled
          showToast(
            isEnabled
              ? 'پایش خودکار برای این استراتژی فعال شد'
              : 'پایش خودکار برای این استراتژی متوقف شد',
            { type: 'success' }
          )
          await loadDeployedStrategies()
        } else {
          showToast(response.data.message || 'خطا در تغییر وضعیت پایش استراتژی', { type: 'error' })
        }
      } catch (error: any) {
        const message =
          error?.response?.data?.message ||
          error?.response?.data?.detail ||
          error?.message ||
          'خطا در تغییر وضعیت پایش استراتژی'
        showToast(message, { type: 'error' })
      }
    })

    toggleAction()
  }

  const openTrades = trades.filter(t => t.status === 'open')
  
  return (
    <div className="space-y-4 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      {/* Account Info */}
      {accountInfo && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-blue-500">💰</span>
              حساب Litefinex
            </h2>
            <span className={`px-3 py-1 rounded-full text-xs font-bold ${accountInfo.is_demo ? 'bg-yellow-500/20 text-yellow-500' : 'bg-green-500/20 text-green-500'}`}>
                {accountInfo.is_demo ? 'حساب دمو' : 'حساب واقعی'}
              </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-900/50 p-3 rounded-lg">
              <div className="text-gray-400 text-xs mb-1">موجودی</div>
              <div className="text-white font-bold">{accountInfo.balance.toLocaleString()} {accountInfo.currency}</div>
            </div>
            <div className="bg-gray-900/50 p-3 rounded-lg">
              <div className="text-gray-400 text-xs mb-1">سرمایه (Equity)</div>
              <div className="text-white font-bold">{accountInfo.equity.toLocaleString()} {accountInfo.currency}</div>
            </div>
            <div className="bg-gray-900/50 p-3 rounded-lg">
              <div className="text-gray-400 text-xs mb-1">مارجین آزاد</div>
              <div className="text-white font-bold">{accountInfo.free_margin.toLocaleString()} {accountInfo.currency}</div>
            </div>
            <div className="bg-gray-900/50 p-3 rounded-lg">
              <div className="text-gray-400 text-xs mb-1">سطح مارجین</div>
              <div className="text-white font-bold">{accountInfo.margin_level ? accountInfo.margin_level.toFixed(1) + '%' : '---'}</div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex bg-gray-800 p-1 rounded-xl border border-gray-700">
        <button onClick={() => setActiveTab('monitoring')} className={`flex-1 py-2 rounded-lg font-bold text-sm transition ${activeTab === 'monitoring' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}>پایش استراتژی‌ها</button>
        <button onClick={() => setActiveTab('trades')} className={`flex-1 py-2 rounded-lg font-bold text-sm transition ${activeTab === 'trades' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}>معاملات باز ({openTrades.length})</button>
        <button onClick={() => setActiveTab('reports')} className={`flex-1 py-2 rounded-lg font-bold text-sm transition ${activeTab === 'reports' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}>راستی‌آزمایی و بیلد</button>
            </div>

      {activeTab === 'monitoring' && (
        <div className="space-y-4">
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold text-white">استراتژی‌های مستقر شده</h2>
              <div className="flex gap-2">
                {loadingStrategies && <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>}
                <button onClick={handleSyncPositions} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-xs transition">همگام‌سازی با MT5</button>
              </div>
          </div>
            {loadingStrategies && deployedStrategies.length === 0 ? (
              <div className="text-center py-8 text-gray-500">در حال بارگذاری...</div>
            ) : deployedStrategies.length === 0 ? (
              <div className="text-center py-8 text-gray-500 border border-dashed border-gray-700 rounded-lg">استراتژی فعالی یافت نشد.</div>
            ) : (
              <div className="space-y-3">
                {deployedStrategies.map(s => (
                  <div key={s.id} className="bg-gray-900/50 p-4 rounded-xl border border-gray-700 flex flex-col md:flex-row justify-between items-center gap-4">
                    <div>
                      <div className="text-white font-bold">{s.strategy_name}</div>
                      <div className="flex gap-2 mt-1">
                        <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded">نماد: {s.symbol}</span>
                        <span className="text-[10px] bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded">تایم‌فریم: {s.timeframe}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-left md:text-right">
                        {s.is_enabled ? (
                          <div className="text-green-400 text-xs font-bold animate-pulse flex items-center gap-1">
                            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                            در حال پایش
                          </div>
                        ) : (
                          <div className="text-gray-400 text-xs font-bold flex items-center gap-1">
                            <span className="w-2 h-2 bg-gray-500 rounded-full"></span>
                            پایش متوقف شده
                          </div>
                        )}
                        <div className="text-[10px] text-gray-500 mt-1">
                          آخرین بررسی: {s.last_check_time ? new Date(s.last_check_time).toLocaleTimeString('fa-IR') : '---'}
                        </div>
                      </div>
                      <button
                        onClick={() => handleToggleMonitoring(s.id!)}
                        className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                          s.is_enabled
                            ? 'bg-red-600/20 hover:bg-red-600 text-red-400 hover:text-white border border-red-600/40'
                            : 'bg-green-600/20 hover:bg-green-600 text-green-400 hover:text-white border border-green-600/40'
                        }`}
                      >
                        {s.is_enabled ? 'توقف پایش' : 'شروع پایش'}
                      </button>
                      <button
                        onClick={() => handleDeleteMonitoring(s.id!)}
                        className="px-4 py-2 bg-red-700/20 hover:bg-red-700 text-red-400 hover:text-white border border-red-600/40 rounded-lg text-xs font-bold transition"
                      >
                        حذف از پایش
                      </button>
                      <button
                        onClick={() => handleBuildReport(s.strategy)}
                        className="px-4 py-2 bg-blue-600/20 hover:bg-blue-600 text-blue-400 hover:text-white border border-blue-600/30 rounded-lg text-xs font-bold transition"
                      >
                        بیلد گزارش عملکرد
                      </button>
                    </div>
                  </div>
                ))}
          </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'trades' && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden shadow-lg">
        {openTrades.length === 0 ? (
            <div className="p-8 text-center text-gray-500 italic">معامله باز فعالی وجود ندارد.</div>
        ) : (
          <div className="overflow-x-auto">
              <table className="w-full text-right">
                <thead className="bg-gray-900/50 text-gray-400 text-xs uppercase">
                  <tr>
                    <th className="px-4 py-3 font-medium">نماد / نوع</th>
                    <th className="px-4 py-3 font-medium">حجم</th>
                    <th className="px-4 py-3 font-medium">قیمت ورود</th>
                    <th className="px-4 py-3 font-medium">سود/زیان</th>
                    <th className="px-4 py-3 font-medium text-center">عملیات</th>
                </tr>
              </thead>
                <tbody className="divide-y divide-gray-700 text-sm">
                  {openTrades.map((t) => (
                    <tr key={t.id} className="hover:bg-gray-700/30 transition">
                      <td className="px-4 py-4">
                        <div className="text-white font-bold">{t.symbol}</div>
                        <div className={`text-[10px] font-bold ${t.trade_type === 'buy' ? 'text-green-500' : 'text-red-500'}`}>{t.trade_type.toUpperCase()}</div>
                    </td>
                      <td className="px-4 py-4 text-white font-mono">{t.volume}</td>
                      <td className="px-4 py-4 text-gray-300 font-mono">{t.open_price.toFixed(5)}</td>
                      <td className={`px-4 py-4 font-bold font-mono ${t.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>{t.profit > 0 ? '+' : ''}{t.profit.toFixed(2)}</td>
                      <td className="px-4 py-4 text-center">
                        <button onClick={() => handleCloseTrade(t.id)} className="px-3 py-1 bg-red-500/10 text-red-500 rounded-lg text-xs font-bold border border-red-500/30">بستن</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      )}

      {activeTab === 'reports' && (
        <div className="space-y-4">
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
            <h2 className="text-lg font-bold text-white mb-4">گزارشات راستی‌آزمایی (Verification Reports)</h2>
            {reports.length === 0 ? (
              <div className="text-center py-8 text-gray-500 border border-dashed border-gray-700 rounded-lg">هنوز گزارشی بیلد نشده است. برای بیلد گزارش، از تب پایش روی دکمه «بیلد گزارش عملکرد» کلیک کنید.</div>
            ) : (
              <div className="space-y-4">
                {reports.map(r => (
                  <div key={r.id} className="bg-gray-900 border border-gray-700 rounded-xl p-4 shadow-sm">
                    <div className="flex justify-between items-start mb-4 border-b border-gray-800 pb-3">
                      <div>
                        <div className="text-white font-bold">{r.strategy_name}</div>
                        <div className="text-[10px] text-gray-500 mt-1">دوره: {new Date(r.start_date).toLocaleDateString('fa-IR')} تا {new Date(r.end_date).toLocaleDateString('fa-IR')}</div>
                      </div>
                      <div className="text-right">
                        <div className={`px-3 py-1 rounded-full text-xs font-bold ${r.compliance_score > 80 ? 'bg-green-500/20 text-green-500' : 'bg-yellow-500/20 text-yellow-500'}`}>امتیاز تطابق: {r.compliance_score.toFixed(0)}%</div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-2 bg-gray-800/50 rounded-lg">
                        <div className="text-gray-500 text-[10px] mb-1">بازدهی واقعی</div>
                        <div className={`font-bold ${r.actual_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>{r.actual_return.toFixed(2)}</div>
                      </div>
                      <div className="text-center p-2 bg-gray-800/50 rounded-lg">
                        <div className="text-gray-500 text-[10px] mb-1">بازدهی مورد انتظار</div>
                        <div className="text-blue-400 font-bold">{r.expected_return.toFixed(2)}%</div>
                      </div>
                      <div className="text-center p-2 bg-gray-800/50 rounded-lg">
                        <div className="text-gray-500 text-[10px] mb-1">معاملات واقعی</div>
                        <div className="text-white font-bold">{r.actual_trades_count}</div>
                      </div>
                      <div className="text-center p-2 bg-gray-800/50 rounded-lg">
                        <div className="text-gray-500 text-[10px] mb-1">نرخ برد واقعی</div>
                        <div className="text-white font-bold">{r.performance_metrics?.win_rate?.toFixed(1)}%</div>
                      </div>
                    </div>
                    {r.verification_details?.anomalies?.length > 0 && (
                      <div className="mt-4 p-3 bg-red-900/10 border border-red-900/30 rounded-lg">
                        <div className="text-red-400 text-xs font-bold mb-2 flex items-center gap-1">⚠️ انحرافات شناسایی شده:</div>
                        <ul className="text-[10px] text-red-300/80 list-disc list-inside">
                          {r.verification_details.anomalies.map((a: string, i: number) => <li key={i}>{a}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  )
}
