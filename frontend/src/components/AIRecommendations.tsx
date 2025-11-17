import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  getAIRecommendations,
  generateAIRecommendations,
  purchaseRecommendation,
  getWalletBalance,
  AIRecommendation as AIRecommendationType
} from '../api/client'
import { useToast } from './ToastProvider'

interface AIRecommendationsProps {
  strategyId: number
  strategyName?: string
}

const RECOMMENDATION_PRICE = 150000 // 150,000 Toman

export default function AIRecommendations({ strategyId, strategyName }: AIRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<AIRecommendationType[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [purchasing, setPurchasing] = useState<number | null>(null)
  const [walletBalance, setWalletBalance] = useState<number | null>(null)
  const [loadingBalance, setLoadingBalance] = useState(true)
  const { showToast } = useToast()
  const navigate = useNavigate()

  useEffect(() => {
    loadRecommendations()
    loadWalletBalance()
  }, [strategyId])

  const loadRecommendations = async () => {
    try {
      setLoading(true)
      const response = await getAIRecommendations(strategyId)
      let recommendationsData: AIRecommendationType[] = []
      
      if (Array.isArray(response.data)) {
        recommendationsData = response.data
      } else if (response.data?.results) {
        recommendationsData = response.data.results
      } else if (response.data?.data) {
        recommendationsData = response.data.data
      }

      setRecommendations(recommendationsData)
    } catch (error: any) {
      console.error('Error loading recommendations:', error)
      showToast('خطا در بارگذاری پیشنهادات', 'error')
    } finally {
      setLoading(false)
    }
  }

  const loadWalletBalance = async () => {
    try {
      setLoadingBalance(true)
      const response = await getWalletBalance()
      setWalletBalance(response.data.balance)
    } catch (error: any) {
      console.error('Error loading wallet balance:', error)
      // If not authenticated, set to null
      setWalletBalance(null)
    } finally {
      setLoadingBalance(false)
    }
  }

  const handleGenerateRecommendations = async () => {
    try {
      setGenerating(true)
      const response = await generateAIRecommendations(strategyId)
      
      if (response.data.status === 'success') {
        showToast(`با موفقیت ${response.data.count} پیشنهاد تولید شد!`, 'success')
        await loadRecommendations()
      } else {
        showToast(response.data.error || 'خطا در تولید پیشنهادات', 'error')
      }
    } catch (error: any) {
      console.error('Error generating recommendations:', error)
      showToast(
        error.response?.data?.error || 'خطا در تولید پیشنهادات',
        'error'
      )
    } finally {
      setGenerating(false)
    }
  }

  const handlePurchase = async (recommendationId: number) => {
    // Check if user has enough balance
    if (walletBalance === null) {
      showToast('لطفاً ابتدا وارد حساب کاربری شوید', 'error')
      navigate('/login')
      return
    }

    const recommendation = recommendations.find(r => r.id === recommendationId)
    if (!recommendation) return

    // If balance is insufficient, redirect to profile for charging
    if (walletBalance < recommendation.price) {
      showToast('موجودی شما کافی نیست. لطفاً حساب خود را شارژ کنید', 'warning')
      navigate('/profile')
      return
    }

    try {
      setPurchasing(recommendationId)
      const response = await purchaseRecommendation(recommendationId)
      
      if (response.data.status === 'success') {
        showToast('پیشنهاد با موفقیت خریداری شد!', 'success')
        setWalletBalance(response.data.remaining_balance || 0)
        await loadRecommendations()
      } else if (response.data.status === 'payment_required') {
        // If backend still requires payment, redirect to profile
        showToast('موجودی شما کافی نیست. لطفاً حساب خود را شارژ کنید', 'warning')
        navigate('/profile')
      } else if (response.data.status === 'already_purchased') {
        showToast('این پیشنهاد قبلاً خریداری شده است', 'info')
      } else {
        showToast(response.data.error || 'خطا در خرید پیشنهاد', 'error')
      }
    } catch (error: any) {
      console.error('Error purchasing recommendation:', error)
      
      // If error is about insufficient balance, redirect to profile
      if (error.response?.data?.error?.includes('موجودی') || 
          error.response?.data?.error?.includes('کافی نیست') ||
          error.response?.status === 400) {
        showToast('موجودی شما کافی نیست. لطفاً حساب خود را شارژ کنید', 'warning')
        navigate('/profile')
      } else {
        showToast(
          error.response?.data?.error || 'خطا در خرید پیشنهاد',
          'error'
        )
      }
    } finally {
      setPurchasing(null)
    }
  }

  const getTypeText = (type: string) => {
    const typeMap: Record<string, string> = {
      'entry_condition': 'شرط ورود',
      'exit_condition': 'شرط خروج',
      'risk_management': 'مدیریت ریسک',
      'indicator': 'اندیکاتور',
      'parameter': 'پارامتر',
      'general': 'عمومی'
    }
    return typeMap[type] || type
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            💡 پیشنهادات و توصیه‌های هوش مصنوعی
          </h2>
          {strategyName && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              استراتژی: {strategyName}
            </p>
          )}
        </div>
        <div className="flex gap-3 items-center">
          {walletBalance !== null && (
            <div className="px-4 py-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <span className="text-sm text-gray-600 dark:text-gray-300">موجودی: </span>
              <span className="font-bold text-blue-600 dark:text-blue-400">
                {walletBalance.toLocaleString('fa-IR')} تومان
              </span>
            </div>
          )}
          <button
            onClick={handleGenerateRecommendations}
            disabled={generating}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? 'در حال تولید...' : '🎯 تولید پیشنهادات جدید'}
          </button>
        </div>
      </div>

      {recommendations.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            هنوز پیشنهادی تولید نشده است
          </p>
          <button
            onClick={handleGenerateRecommendations}
            disabled={generating}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {generating ? 'در حال تولید...' : 'تولید پیشنهادات'}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {recommendations.map((recommendation) => (
            <div
              key={recommendation.id}
              className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {recommendation.title}
                    </h3>
                    <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-xs">
                      {getTypeText(recommendation.recommendation_type)}
                    </span>
                    {recommendation.status === 'purchased' && (
                      <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded text-xs">
                        ✓ خریداری شده
                      </span>
                    )}
                  </div>
                  <p className="text-gray-600 dark:text-gray-300 text-sm leading-relaxed">
                    {recommendation.description}
                  </p>
                </div>
                <div className="text-left ml-4">
                  <div className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                    {recommendation.price.toLocaleString('fa-IR')} تومان
                  </div>
                  {recommendation.status !== 'purchased' && (
                    <button
                      onClick={() => handlePurchase(recommendation.id)}
                      disabled={purchasing === recommendation.id || walletBalance === null}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                    >
                      {purchasing === recommendation.id
                        ? 'در حال پردازش...'
                        : walletBalance !== null && walletBalance >= recommendation.price
                        ? '🛒 خرید'
                        : walletBalance === null
                        ? '⚠️ نیاز به ورود'
                        : '💳 شارژ حساب'}
                    </button>
                  )}
                </div>
              </div>

              {recommendation.recommendation_data && Object.keys(recommendation.recommendation_data).length > 0 && (
                <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600">
                  <p className="text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">جزئیات پیشنهاد:</p>
                  <pre className="text-xs overflow-x-auto text-gray-600 dark:text-gray-400">
                    {JSON.stringify(recommendation.recommendation_data, null, 2)}
                  </pre>
                </div>
              )}

              {recommendation.status === 'purchased' && recommendation.applied_to_strategy && (
                <div className="mt-4 p-3 bg-green-50 dark:bg-green-900 rounded border border-green-200 dark:border-green-700">
                  <p className="text-sm text-green-800 dark:text-green-200">
                    ✓ این پیشنهاد به استراتژی اعمال شده است
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

