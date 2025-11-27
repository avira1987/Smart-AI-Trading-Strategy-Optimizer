import { useState, useEffect } from 'react'
import { getResults, deleteResult, clearResults, getJobs, type Job, type Result as APIResult } from '../api/client'
import { Line } from 'react-chartjs-2'
import AIAnalysisDisplay from '../components/AIAnalysisDisplay'
import GamificationScore from '../components/GamificationScore'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

type Result = APIResult

export default function Results() {
  const [results, setResults] = useState<Result[]>([])
  const [selectedResult, setSelectedResult] = useState<Result | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [tradesExpanded, setTradesExpanded] = useState(false)

  useEffect(() => {
    loadResults()
  }, [])

  // Reset trades expanded state when selected result changes
  useEffect(() => {
    setTradesExpanded(false)
  }, [selectedResult?.id])

  const normalizeArrayResponse = <T = any>(data: any): T[] => {
    if (!data) return []
    if (Array.isArray(data)) return data
    if (Array.isArray(data?.results)) return data.results
    if (Array.isArray(data?.data)) return data.data
    if (Array.isArray(data?.data?.results)) return data.data.results
    if (Array.isArray(data?.results?.data)) return data.results.data
    return []
  }

  const loadResultsFromJobs = async (): Promise<Result[]> => {
    try {
      const jobsResponse = await getJobs()
      const jobsData = normalizeArrayResponse<Job>(jobsResponse.data)
      const jobResults = jobsData
        .map((job) => {
          if (!job.result) return null
          return { ...job.result, job: job.result.job ?? job.id }
        })
        .filter((item): item is Result => Boolean(item))

      const unique: Result[] = []
      const seen = new Set<number>()
      for (const result of jobResults) {
        if (!seen.has(result.id)) {
          seen.add(result.id)
          unique.push(result)
        }
      }
      return unique
    } catch (fallbackError) {
      console.error('Job fallback failed:', fallbackError)
      return []
    }
  }

  const loadResults = async () => {
    try {
      setLoading(true)
      const response = await getResults()
      console.log('Results response:', response) // Debug log
      
      // Handle possible response formats (array, paginated, nested data)
      let resultsData: Result[] = normalizeArrayResponse<Result>(response.data)

      if (resultsData.length === 0) {
        console.warn('Primary results endpoint returned no data. Trying job fallback.')
        resultsData = await loadResultsFromJobs()
      }
      
      console.log('Results data:', resultsData) // Debug log
      setResults(resultsData)
      setSelectedResult((current) => {
        if (current && resultsData.some(r => r.id === current.id)) {
          return current
        }
        return resultsData.length > 0 ? resultsData[0] : null
      })
      setError(null)
    } catch (err) {
      console.error('Error loading results:', err)
      setError('خطا در بارگذاری نتایج. لطفاً دوباره تلاش کنید.')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteSelected = async () => {
    if (!selectedResult) return
    try {
      setDeleting(true)
      await deleteResult(selectedResult.id)
      await loadResults()
      setSelectedResult(null)
    } catch (e) {
      console.error('Delete failed', e)
    } finally {
      setDeleting(false)
    }
  }

  const handleClearAll = async () => {
    try {
      setDeleting(true)
      await clearResults()
      await loadResults()
      setSelectedResult(null)
    } catch (e) {
      console.error('Clear failed', e)
    } finally {
      setDeleting(false)
    }
  }

  const equityData = selectedResult?.equity_curve_data ?? []
  const chartData = selectedResult && equityData.length > 0 ? {
    labels: equityData.map(d => d.date),
    datasets: [
      {
        label: 'Equity Curve',
        data: equityData.map(d => d.equity),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
      },
    ],
  } : null

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: true,
        labels: {
          color: '#9CA3AF',
        },
      },
      title: {
        display: true,
        text: 'روند تغییر سرمایه (Equity Curve)',
        color: '#FFFFFF',
      },
    },
    scales: {
      x: {
        ticks: { color: '#9CA3AF' },
        grid: { color: '#374151' },
      },
      y: {
        ticks: { color: '#9CA3AF' },
        grid: { color: '#374151' },
      },
    },
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center text-gray-400">Loading results...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-900/30 border border-red-700 text-red-200 rounded-lg p-6 text-center">
          {error}
          <div className="mt-4">
            <button
              onClick={loadResults}
              className="btn-primary"
            >
              تلاش مجدد
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 direction-rtl" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="mb-6 flex items-center justify-between text-right">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">نتایج تست‌ها</h1>
          <p className="text-gray-400">در این بخش می‌توانید نتایج تست و بهینه‌سازی استراتژی‌های خود را مشاهده کنید.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleClearAll}
            disabled={deleting || results.length === 0}
            className="btn-secondary"
          >
            حذف همه
          </button>
          <button
            onClick={handleDeleteSelected}
            disabled={deleting || !selectedResult}
            className="btn-danger"
          >
            حذف انتخاب شده
          </button>
        </div>
      </div>

      {results.length === 0 ? (
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <p className="text-gray-400 text-lg mb-4">هیچ نتیجه‌ای ثبت نشده است</p>
          <p className="text-gray-500">
            برای مشاهده نتیجه، ابتدا تست را در بخش تست استراتژی انجام دهید.
          </p>
          <a
            href="/testing"
            className="mt-4 inline-block btn-primary"
          >
            برو به تست استراتژی
          </a>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Results List */}
          <div className="lg:col-span-1">
            <div className="card-standard p-4">
              <h2 className="text-lg font-semibold text-white mb-4 text-right">کل نتایج</h2>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {results.map((result) => (
                  <div
                    key={result.id}
                    onClick={() => setSelectedResult(result)}
                    className={`p-3 rounded cursor-pointer transition ${
                      selectedResult?.id === result.id
                        ? 'bg-blue-600'
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-white text-sm">نتیجه شماره {result.id}</span>
                      <span
                        className={`text-sm font-medium ${
                          result.total_return >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}
                      >
                        {result.total_return > 0 ? '+' : ''}{result.total_return.toFixed(2)}%
                      </span>
                    </div>
                    <div className="text-gray-300 text-xs mt-1">
                      {new Date(result.created_at).toLocaleString('fa-IR')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Selected Result Details */}
          <div className="lg:col-span-2">
            {selectedResult && (
              <>
                {/* Gamification Score */}
                <GamificationScore />

                {/* Share Button */}
                <div className="mb-6 flex justify-end">
                  <button
                    onClick={() => {
                      const shareText = `نتایج بک‌تست من:\nبازدهی: ${selectedResult.total_return > 0 ? '+' : ''}${selectedResult.total_return.toFixed(2)}%\nنرخ برد: ${selectedResult.win_rate.toFixed(2)}%\nمعاملات: ${selectedResult.total_trades}\n\n`
                      const shareUrl = window.location.href
                      
                      if (navigator.share) {
                        navigator.share({
                          title: 'نتایج بک‌تست معاملاتی',
                          text: shareText,
                          url: shareUrl
                        }).catch(() => {
                          // Fallback to clipboard
                          navigator.clipboard.writeText(shareText + shareUrl)
                          alert('لینک کپی شد!')
                        })
                      } else {
                        navigator.clipboard.writeText(shareText + shareUrl)
                        alert('لینک کپی شد!')
                      }
                    }}
                    className="btn-primary flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                    </svg>
                    اشتراک‌گذاری نتایج
                  </button>
                </div>

                {/* Backtest Information */}
                {selectedResult.data_sources && (
                  <div className="card-standard mb-6">
                    <h2 className="text-xl font-semibold text-white mb-4 text-right">اطلاعات بک‌تست</h2>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {selectedResult.data_sources.symbol && (
                        <div className="bg-gray-700 rounded p-4">
                          <div className="text-gray-400 text-sm mb-1">نماد معاملاتی</div>
                          <div className="text-lg font-semibold text-white">
                            {selectedResult.data_sources.symbol}
                          </div>
                        </div>
                      )}
                      {selectedResult.data_sources.strategy_timeframe && (
                        <div className="bg-gray-700 rounded p-4">
                          <div className="text-gray-400 text-sm mb-1">تایم‌فریم استراتژی</div>
                          <div className="text-lg font-semibold text-blue-400">
                            {selectedResult.data_sources.strategy_timeframe}
                          </div>
                          {selectedResult.data_sources.provider === 'mt5' && (
                            <div className="text-gray-400 text-xs mt-1">
                              (تجمیع شده از کندل‌های M1)
                            </div>
                          )}
                        </div>
                      )}
                      {!selectedResult.data_sources.strategy_timeframe && selectedResult.data_sources.normalized_timeframe && (
                        <div className="bg-gray-700 rounded p-4">
                          <div className="text-gray-400 text-sm mb-1">تایم‌فریم استفاده شده</div>
                          <div className="text-lg font-semibold text-blue-400">
                            {selectedResult.data_sources.normalized_timeframe}
                          </div>
                        </div>
                      )}
                      {selectedResult.data_sources.provider && (
                        <div className="bg-gray-700 rounded p-4">
                          <div className="text-gray-400 text-sm mb-1">ارائه‌دهنده داده</div>
                          <div className="text-lg font-semibold text-white">
                            {selectedResult.data_sources.provider}
                          </div>
                        </div>
                      )}
                      {selectedResult.data_sources.data_points && (
                        <div className="bg-gray-700 rounded p-4">
                          <div className="text-gray-400 text-sm mb-1">تعداد نقاط داده</div>
                          <div className="text-lg font-semibold text-white">
                            {selectedResult.data_sources.data_points.toLocaleString('fa-IR')}
                          </div>
                        </div>
                      )}
                      {selectedResult.data_sources.start_date && selectedResult.data_sources.end_date && (
                        <div className="bg-gray-700 rounded p-4">
                          <div className="text-gray-400 text-sm mb-1">بازه زمانی</div>
                          <div className="text-lg font-semibold text-white text-sm">
                            {selectedResult.data_sources.start_date} تا {selectedResult.data_sources.end_date}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* AI Analysis Section - Using new component */}
                {selectedResult.description && selectedResult.description.includes('تحلیل هوش مصنوعی') && (() => {
                  // Extract AI analysis text - improved extraction to avoid data sources section
                  const markers = [
                    '📊 تحلیل هوش مصنوعی نتایج بک‌تست:',
                    'تحلیل هوش مصنوعی نتایج بک‌تست:',
                    'تحلیل هوش مصنوعی'
                  ]
                  
                  let analysisText = ''
                  let startIndex = -1
                  
                  // Find the start of AI analysis section
                  for (const marker of markers) {
                    const markerIndex = selectedResult.description.indexOf(marker)
                    if (markerIndex !== -1) {
                      startIndex = markerIndex + marker.length
                      break
                    }
                  }
                  
                  if (startIndex === -1) {
                    // Try to find after separator
                    const separatorIndex = selectedResult.description.lastIndexOf('='.repeat(80))
                    if (separatorIndex !== -1) {
                      const afterSeparator = selectedResult.description.substring(separatorIndex)
                      for (const marker of markers) {
                        const markerIndex = afterSeparator.indexOf(marker)
                        if (markerIndex !== -1) {
                          startIndex = separatorIndex + markerIndex + marker.length
                          break
                        }
                      }
                    }
                  }
                  
                  if (startIndex !== -1) {
                    // Extract text from start index until data sources section
                    let extracted = selectedResult.description.substring(startIndex).trim()
                    
                    // Remove data sources section markers (stop before this section)
                    const dataSourceMarkers = [
                      '\n\n' + '='.repeat(80) + '\n\n📊 منابع داده استفاده شده:',
                      '\n\n📊 منابع داده استفاده شده:',
                      '\n' + '='.repeat(80) + '\n\n📊 منابع داده استفاده شده:',
                      '='.repeat(80) + '\n\n📊 منابع داده استفاده شده:',
                    ]
                    
                    let cutIndex = extracted.length
                    for (const dsMarker of dataSourceMarkers) {
                      const dsIndex = extracted.indexOf(dsMarker)
                      if (dsIndex !== -1 && dsIndex < cutIndex) {
                        cutIndex = dsIndex
                      }
                    }
                    
                    // Also check for long separator lines that might indicate data sources section
                    const longSeparatorPattern = /\n={50,}\n/
                    const separatorMatch = extracted.match(longSeparatorPattern)
                    if (separatorMatch && separatorMatch.index !== undefined) {
                      const afterSeparator = extracted.substring(separatorMatch.index + separatorMatch[0].length)
                      if (afterSeparator.includes('منابع داده') || afterSeparator.includes('ارائه‌دهنده')) {
                        if (separatorMatch.index < cutIndex) {
                          cutIndex = separatorMatch.index
                        }
                      }
                    }
                    
                    extracted = extracted.substring(0, cutIndex).trim()
                    
                    // Clean up formatting artifacts
                    extracted = extracted
                      .replace(/^=+\s*$/gm, '') // Remove standalone separator lines
                      .replace(/\n{3,}/g, '\n\n') // Replace multiple newlines with double newline
                      .trim()
                    
                    analysisText = extracted
                  }
                  
                  // Fallback: if no clean extraction, use description but clean it
                  if (!analysisText) {
                    analysisText = selectedResult.description
                      .replace(/^=+\s*$/gm, '')
                      .replace(/\n{3,}/g, '\n\n')
                      .trim()
                  }
                  
                  return (
                    <AIAnalysisDisplay
                      analysisText={analysisText}
                      resultMetrics={{
                        total_return: selectedResult.total_return,
                        win_rate: selectedResult.win_rate,
                        total_trades: selectedResult.total_trades,
                        max_drawdown: selectedResult.max_drawdown
                      }}
                    />
                  )
                })()}

                {/* Key Metrics */}
                <div className="card-standard mb-6">
                  <h2 className="text-xl font-semibold text-white mb-4 text-right">شاخص‌های عملکرد</h2>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-700 rounded p-4">
                      <div className="text-gray-400 text-sm mb-1">بازده کل</div>
                      <div
                        className={`text-2xl font-bold ${
                          selectedResult.total_return >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}
                      >
                        {selectedResult.total_return > 0 ? '+' : ''}
                        {selectedResult.total_return.toFixed(2)}%
                      </div>
                    </div>

                    <div className="bg-gray-700 rounded p-4">
                      <div className="text-gray-400 text-sm mb-1">درصد معاملات موفق</div>
                      <div className="text-2xl font-bold text-blue-400">
                        {selectedResult.win_rate.toFixed(2)}%
                      </div>
                    </div>

                    <div className="bg-gray-700 rounded p-4">
                      <div className="text-gray-400 text-sm mb-1">تعداد کل معاملات</div>
                      <div className="text-2xl font-bold text-white">
                        {selectedResult.total_trades}
                      </div>
                    </div>

                    <div className="bg-gray-700 rounded p-4">
                      <div className="text-gray-400 text-sm mb-1">حداکثر افت سرمایه</div>
                      <div className="text-2xl font-bold text-orange-400">
                        {selectedResult.max_drawdown.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>

                {/* Trade Statistics */}
                <div className="card-standard mb-6">
                  <h2 className="text-xl font-semibold text-white mb-4 text-right">آمار معاملات</h2>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-400">
                        {selectedResult.winning_trades}
                      </div>
                      <div className="text-gray-400 text-sm mt-1">تعداد معاملات موفق</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-red-400">
                        {selectedResult.losing_trades}
                      </div>
                      <div className="text-gray-400 text-sm mt-1">تعداد معاملات ناموفق</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-white">
                        {selectedResult.winning_trades - selectedResult.losing_trades}
                      </div>
                      <div className="text-gray-400 text-sm mt-1">خالص معاملات (موفق - ناموفق)</div>
                    </div>
                  </div>
                </div>

                {/* Trade Details - Collapsible */}
                {selectedResult.trades_details && selectedResult.trades_details.length > 0 && (
                  <div className="card-standard mb-6">
                    <button
                      onClick={() => setTradesExpanded(!tradesExpanded)}
                      className="w-full flex items-center justify-between text-right mb-4 hover:bg-gray-700 rounded-lg p-2 transition"
                    >
                      <h2 className="text-xl font-semibold text-white">
                        📋 ریز معاملات ({selectedResult.trades_details.length} معامله)
                      </h2>
                      <svg
                        className={`w-5 h-5 text-gray-400 transition-transform ${tradesExpanded ? 'transform rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    
                    {tradesExpanded && (
                      <div className="bg-gray-700 rounded-lg p-4 max-h-96 overflow-y-auto">
                        <div className="space-y-4">
                          {selectedResult.trades_details.map((trade, index) => (
                            <div
                              key={index}
                              className={`border-r-4 p-4 rounded ${
                                trade.pnl >= 0
                                  ? 'bg-green-900/20 border-green-500'
                                  : 'bg-red-900/20 border-red-500'
                              }`}
                            >
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                <div>
                                  <div className="text-gray-400 text-xs mb-1">نوع</div>
                                  <div className="text-white font-medium">{trade.entry_reason_fa || 'خرید'}</div>
                                </div>
                                <div>
                                  <div className="text-gray-400 text-xs mb-1">ورود</div>
                                  <div className="text-white">{new Date(trade.entry_date).toLocaleDateString('fa-IR')}</div>
                                  <div className="text-gray-300 text-xs">{trade.entry_price.toFixed(4)}</div>
                                </div>
                                <div>
                                  <div className="text-gray-400 text-xs mb-1">خروج</div>
                                  <div className="text-white">{new Date(trade.exit_date).toLocaleDateString('fa-IR')}</div>
                                  <div className="text-gray-300 text-xs">{trade.exit_price.toFixed(4)}</div>
                                </div>
                                <div>
                                  <div className="text-gray-400 text-xs mb-1">سود/ضرر</div>
                                  <div
                                    className={`font-bold ${
                                      trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                                    }`}
                                  >
                                    {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)} ({trade.pnl_percent.toFixed(2)}%)
                                  </div>
                                  <div className="text-gray-300 text-xs mt-1">{trade.duration_days} روز</div>
                                </div>
                              </div>
                              {trade.exit_reason_fa && (
                                <div className="mt-2 pt-2 border-t border-gray-600">
                                  <div className="text-gray-400 text-xs mb-1">دلیل خروج</div>
                                  <div className="text-gray-300 text-xs">{trade.exit_reason_fa}</div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* General Description (if no AI analysis marker) */}
                {selectedResult.description && 
                 !selectedResult.description.includes('تحلیل هوش مصنوعی') && (
                  <div className="card-standard mb-6">
                    <h2 className="text-xl font-semibold text-white mb-4 text-right">اطلاعات تکمیلی</h2>
                    <div className="bg-gray-700 rounded-lg p-4">
                      <pre className="text-sm text-gray-200 whitespace-pre-wrap font-sans text-right leading-relaxed">
                        {selectedResult.description}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Equity Curve Chart */}
                {chartData && selectedResult.equity_curve_data.length > 0 && (
                  <div className="card-standard">
                    <Line data={chartData} options={chartOptions} />
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
