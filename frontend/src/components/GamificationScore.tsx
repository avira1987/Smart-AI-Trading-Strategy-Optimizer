import { useState, useEffect } from 'react'
import { get } from '../api/client'

// Wrap in try-catch to prevent crashes

interface UserScore {
  total_points: number
  level: number
  rank?: number
  backtests_completed: number
  best_return: number
}

export default function GamificationScore() {
  const [score, setScore] = useState<UserScore | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let mounted = true
    loadScore(mounted)
    return () => {
      mounted = false
    }
  }, [])

  const loadScore = async (mounted: boolean) => {
    try {
      const response = await get('/api/gamification/scores/me/')
      if (mounted && response && response.data) {
        setScore(response.data)
      }
    } catch (error) {
      console.error('Error loading score:', error)
      if (mounted) {
        setError(true)
      }
    } finally {
      if (mounted) {
        setLoading(false)
      }
    }
  }

  // Don't render anything if there's an error (API might not be ready yet)
  if (error) {
    return null
  }

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 animate-pulse">
        <div className="h-20 bg-gray-700 rounded"></div>
      </div>
    )
  }

  if (!score) return null

  const getLevelColor = (level: number) => {
    if (level >= 8) return 'from-purple-600 to-pink-600'
    if (level >= 5) return 'from-blue-600 to-purple-600'
    if (level >= 3) return 'from-green-600 to-blue-600'
    return 'from-yellow-600 to-green-600'
  }

  const getNextLevelPoints = (level: number) => {
    const thresholds = [100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]
    return thresholds[level - 1] || 100000
  }

  const progress = score.total_points / getNextLevelPoints(score.level)
  const nextLevelPoints = getNextLevelPoints(score.level)

  return (
    <div className={`bg-gradient-to-br ${getLevelColor(score.level)} rounded-lg p-4 mb-4 shadow-lg`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-white/80 text-sm mb-1">سطح {score.level}</div>
          <div className="text-2xl font-bold text-white">
            {score.total_points.toLocaleString('fa-IR')} امتیاز
          </div>
        </div>
        {score.rank && (
          <div className="text-right">
            <div className="text-white/80 text-sm mb-1">رتبه</div>
            <div className="text-2xl font-bold text-white">#{score.rank}</div>
          </div>
        )}
      </div>
      
      <div className="mb-2">
        <div className="flex justify-between text-xs text-white/80 mb-1">
          <span>پیشرفت به سطح {score.level + 1}</span>
          <span>{score.total_points.toLocaleString('fa-IR')} / {nextLevelPoints.toLocaleString('fa-IR')}</span>
        </div>
        <div className="w-full bg-white/20 rounded-full h-2">
          <div
            className="bg-white rounded-full h-2 transition-all duration-500"
            style={{ width: `${Math.min(progress * 100, 100)}%` }}
          ></div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
        <div className="bg-white/10 rounded p-2">
          <div className="text-white/80">بک‌تست‌ها</div>
          <div className="text-white font-bold">{score.backtests_completed}</div>
        </div>
        <div className="bg-white/10 rounded p-2">
          <div className="text-white/80">بهترین بازدهی</div>
          <div className={`font-bold ${score.best_return >= 0 ? 'text-green-200' : 'text-red-200'}`}>
            {score.best_return > 0 ? '+' : ''}{score.best_return.toFixed(2)}%
          </div>
        </div>
      </div>
    </div>
  )
}

