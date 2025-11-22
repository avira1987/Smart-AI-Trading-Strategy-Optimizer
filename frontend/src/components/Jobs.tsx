import { useState, useEffect } from 'react'
import { getJobs, getResults, Job, Result } from '../api/client'
import { useNavigate } from 'react-router-dom'

const normalizeArrayResponse = <T = any>(data: any): T[] => {
  if (!data) return []
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.data)) return data.data
  if (Array.isArray(data?.data?.results)) return data.data.results
  if (Array.isArray(data?.results?.data)) return data.results.data
  return []
}

type RecentResultEntry = {
  result: Result
  job: Job | null
}

export default function Jobs() {
  const [entries, setEntries] = useState<RecentResultEntry[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    try {
      setLoading(true)
      const [jobsRes, resultsRes] = await Promise.allSettled([getJobs(), getResults()])

      let jobsData: Job[] = []
      if (jobsRes.status === 'fulfilled') {
        jobsData = normalizeArrayResponse<Job>(jobsRes.value.data)
      }

      const resultsMap = new Map<number, Result>()
      if (resultsRes.status === 'fulfilled') {
        const resultsData = normalizeArrayResponse<Result>(resultsRes.value.data)
        for (const result of resultsData) {
          const jobId = result.job ?? result.id
          if (typeof jobId === 'number' && !resultsMap.has(jobId)) {
            resultsMap.set(jobId, result)
          }
        }
      }

      const jobMap = new Map<number, Job>()
      for (const job of jobsData) {
        jobMap.set(job.id, job)
      }

      const combinedEntries: RecentResultEntry[] = []
      for (const result of resultsMap.values()) {
        const job = jobMap.get(result.job)
        combinedEntries.push({ result, job: job ?? null })
      }

      combinedEntries.sort((a, b) => {
        const dateA = new Date(a.result.created_at).getTime()
        const dateB = new Date(b.result.created_at).getTime()
        return dateB - dateA
      })

      setEntries(combinedEntries.slice(0, 5))
    } catch (error) {
      console.error('Error loading jobs:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-600'
      case 'running':
        return 'bg-blue-600'
      case 'pending':
        return 'bg-yellow-600'
      case 'failed':
        return 'bg-red-600'
      default:
        return 'bg-gray-600'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'تکمیل شده'
      case 'running':
        return 'در حال اجرا'
      case 'pending':
        return 'در انتظار'
      case 'failed':
        return 'ناموفق'
      default:
        return status
    }
  }

  const getJobTypeText = (jobType: string) => {
    switch (jobType) {
      case 'backtest':
        return 'بک‌تست'
      case 'demo_trade':
        return 'معامله دمو'
      default:
        return jobType
    }
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('fa-IR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateString
    }
  }

  if (loading) {
    return (
      <div>
        <div className="text-center text-gray-400 py-4">در حال بارگذاری...</div>
      </div>
    )
  }

  if (entries.length === 0) {
    return (
      <div>
        <div className="text-center text-gray-400 py-4">
          <p className="mb-2">هیچ نتیجه‌ای در صفحه نتایج ثبت نشده است.</p>
          <p className="text-sm text-gray-500">برای مشاهده نتیجه، ابتدا تست را در بخش تست استراتژی انجام دهید.</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="space-y-3">
        {entries.map(({ result, job }) => (
          <div key={result.id} className="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition">
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-gray-400 text-sm">{job ? getJobTypeText(job.job_type) : 'نتیجه ثبت‌شده'}</span>
                  {job?.strategy_name && (
                    <>
                      <span className="text-gray-600">•</span>
                      <p className="text-white font-medium text-sm">{job.strategy_name}</p>
                    </>
                  )}
                  {!job?.strategy_name && (
                    <p className="text-white font-medium text-sm">نتیجه شماره {result.id}</p>
                  )}
                </div>
                <div className="text-gray-400 text-xs mt-1">
                  {formatDate(result.created_at)}
                </div>
              </div>
              {job && (
                <span className={`px-3 py-1 ${getStatusColor(job.status)} text-white text-xs rounded font-medium`}>
                  {getStatusText(job.status)}
                </span>
              )}
            </div>

            {job?.error_message && (
              <div className="mt-2 p-2 bg-red-900/30 rounded text-red-300 text-xs">
                {job.error_message}
              </div>
            )}

            <div className="mt-3 flex items-center justify-between">
              <div className="text-xs text-gray-400">
                <span className={result.total_return >= 0 ? 'text-green-400' : 'text-red-400'}>
                  بازده: {result.total_return > 0 ? '+' : ''}{result.total_return.toFixed(2)}%
                </span>
                <span className="mx-2">•</span>
                <span>معاملات: {result.total_trades}</span>
                {job && (
                  <>
                    <span className="mx-2">•</span>
                    <span>شناسه بک‌تست: {job.id}</span>
                  </>
                )}
              </div>
              <button
                onClick={() => navigate('/results')}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition"
              >
                مشاهده نتایج
              </button>
            </div>
          </div>
        ))}
      </div>

      {entries.length >= 5 && (
        <div className="mt-4 text-center">
          <button
            onClick={() => navigate('/results')}
            className="text-blue-400 hover:text-blue-300 text-sm transition"
          >
            مشاهده همه تست‌ها
          </button>
        </div>
      )}
    </div>
  )
}
