import { useState, useEffect } from 'react'
import { getJobs, Job } from '../api/client'
import { useNavigate } from 'react-router-dom'

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    try {
      setLoading(true)
      const response = await getJobs()
      // Handle both array and paginated response
      let jobsData: Job[] = []
      if (response.data && response.data.results) {
        jobsData = response.data.results
      } else if (Array.isArray(response.data)) {
        jobsData = response.data
      }
      // Sort by created_at descending (most recent first) and limit to 5
      jobsData = jobsData
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 5)
      setJobs(jobsData)
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

  if (jobs.length === 0) {
    return (
      <div>
        <div className="text-center text-gray-400 py-4">
          <p className="mb-2">تاکنون تستی انجام نشده است.</p>
          <p className="text-sm text-gray-500">ابتدا استراتژی جدید آپلود و تست را انجام دهید.</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="space-y-3">
        {jobs.map((job) => (
          <div key={job.id} className="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition">
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-gray-400 text-sm">{getJobTypeText(job.job_type)}</span>
                  {job.strategy_name && (
                    <>
                      <span className="text-gray-600">•</span>
                      <p className="text-white font-medium text-sm">{job.strategy_name}</p>
                    </>
                  )}
                </div>
                <div className="text-gray-400 text-xs mt-1">
                  {formatDate(job.created_at)}
                </div>
              </div>
              <span className={`px-3 py-1 ${getStatusColor(job.status)} text-white text-xs rounded font-medium`}>
                {getStatusText(job.status)}
              </span>
            </div>
            
            {job.error_message && (
              <div className="mt-2 p-2 bg-red-900/30 rounded text-red-300 text-xs">
                {job.error_message}
              </div>
            )}
            
            {job.result && (
              <div className="mt-3 flex items-center justify-between">
                <div className="text-xs text-gray-400">
                  <span className={job.result.total_return >= 0 ? 'text-green-400' : 'text-red-400'}>
                    بازده: {job.result.total_return > 0 ? '+' : ''}{job.result.total_return.toFixed(2)}%
                  </span>
                  <span className="mx-2">•</span>
                  <span>معاملات: {job.result.total_trades}</span>
                </div>
                <button
                  onClick={() => navigate('/results')}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition"
                >
                  مشاهده نتایج
                </button>
              </div>
            )}
            
            {job.status === 'running' || job.status === 'pending' ? (
              <div className="mt-3 text-xs text-gray-400">
                تست در حال اجرا است...
              </div>
            ) : job.status === 'completed' && !job.result ? (
              <div className="mt-3 text-xs text-gray-400">
                تست تکمیل شد اما نتیجه در دسترس نیست
              </div>
            ) : null}
          </div>
        ))}
      </div>
      
      {jobs.length >= 5 && (
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
