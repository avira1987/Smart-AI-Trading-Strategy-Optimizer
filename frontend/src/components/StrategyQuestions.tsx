import { useState, useEffect } from 'react'
import { 
  getStrategyQuestions, 
  generateStrategyQuestions, 
  processStrategyWithAnswers,
  updateQuestionAnswer,
  StrategyQuestion 
} from '../api/client'
import { useToast } from './ToastProvider'

interface StrategyQuestionsProps {
  strategyId: number
  onComplete?: () => void
}

export default function StrategyQuestions({ strategyId, onComplete }: StrategyQuestionsProps) {
  const [questions, setQuestions] = useState<StrategyQuestion[]>([])
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(true) // Start with loading true
  const [generating, setGenerating] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [editingQuestionId, setEditingQuestionId] = useState<number | null>(null)
  const { showToast } = useToast()

  useEffect(() => {
    loadQuestions()
  }, [strategyId])

  const loadQuestions = async () => {
    try {
      setLoading(true)
      const response = await getStrategyQuestions(strategyId)
      // Handle different response formats
      let questionsData: StrategyQuestion[] = []
      if (Array.isArray(response.data)) {
        questionsData = response.data
      } else if (response.data && Array.isArray(response.data.results)) {
        questionsData = response.data.results
      } else if (response.data && response.data.data && Array.isArray(response.data.data)) {
        questionsData = response.data.data
      }
      
      setQuestions(questionsData || [])
      // Initialize answers from existing answers
      const existingAnswers: Record<number, string> = {}
      if (questionsData && questionsData.length > 0) {
        questionsData.forEach((q: StrategyQuestion) => {
        if (q.answer) {
          existingAnswers[q.id] = q.answer
        }
      })
      }
      setAnswers(existingAnswers)
    } catch (error: any) {
      console.error('Error loading questions:', error)
      showToast('خطا در بارگذاری سوالات', 'error')
      setQuestions([]) // Ensure questions is set to empty array on error
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateQuestions = async () => {
    try {
      setGenerating(true)
      const response = await generateStrategyQuestions(strategyId)
      if (response.data.status === 'success') {
        showToast(`${response.data.message}`, 'success')
        // Only reload questions after generating new ones
        await loadQuestions()
      } else {
        const errorMessage = response.data.message || 'خطا در تولید سوالات'
        // Show multi-line error messages properly
        showToast(errorMessage.replace(/\n/g, ' '), 'error')
        console.error('Error generating questions:', response.data)
      }
    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || 
                          error?.message || 
                          'خطا در تولید سوالات. لطفاً Gemini API را بررسی کنید.'
      showToast(errorMessage.replace(/\n/g, ' '), 'error')
      console.error('Error generating questions:', error)
      console.error('Error response:', error?.response?.data)
    } finally {
      setGenerating(false)
    }
  }

  const handleAnswerChange = (questionId: number, value: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }))
  }

  const handleSaveAnswer = async (question: StrategyQuestion) => {
    const answer = answers[question.id]
    if (!answer && question.question_type !== 'boolean') {
      showToast('لطفاً جواب را وارد کنید', 'warning')
      return
    }

    try {
      const response = await updateQuestionAnswer(question.id, answer || '', 'answered')
      showToast('جواب ذخیره شد', 'success')
      setEditingQuestionId(null) // Exit edit mode
      
      // Update the question in state instead of reloading all questions
      setQuestions(prevQuestions => 
        prevQuestions.map(q => 
          q.id === question.id 
            ? { ...q, answer: answer || '', status: 'answered' as const, answered_at: new Date().toISOString() }
            : q
        )
      )
    } catch (error: any) {
      showToast('خطا در ذخیره جواب', 'error')
      console.error('Error saving answer:', error)
    }
  }

  const handleEditAnswer = (question: StrategyQuestion) => {
    setEditingQuestionId(question.id)
    // Ensure the answer is loaded into the answers state
    if (question.answer) {
      setAnswers(prev => ({ ...prev, [question.id]: question.answer || '' }))
    }
  }

  const handleCancelEdit = () => {
    setEditingQuestionId(null)
  }

  const handleSkipQuestion = async (question: StrategyQuestion) => {
    try {
      await updateQuestionAnswer(question.id, '', 'skipped')
      showToast('سوال رد شد', 'info')
      
      // Update the question in state instead of reloading all questions
      setQuestions(prevQuestions => 
        prevQuestions.map(q => 
          q.id === question.id 
            ? { ...q, answer: null, status: 'skipped' as const }
            : q
        )
      )
      // Remove from answers state
      setAnswers(prev => {
        const newAnswers = { ...prev }
        delete newAnswers[question.id]
        return newAnswers
      })
    } catch (error: any) {
      showToast('خطا در رد سوال', 'error')
      console.error('Error skipping question:', error)
    }
  }

  const handleProcessWithAnswers = async () => {
    const unanswered = questions.filter(q => 
      q.status === 'pending' && !answers[q.id]
    )

    if (unanswered.length > 0) {
      showToast('لطفاً به همه سوالات پاسخ دهید یا آنها را رد کنید', 'warning')
      return
    }

    try {
      setProcessing(true)
      const response = await processStrategyWithAnswers(strategyId)
      if (response.data.status === 'success') {
        showToast('استراتژی با موفقیت پردازش شد!', 'success')
        if (onComplete) {
          onComplete()
        }
      } else {
        showToast(response.data.message || 'خطا در پردازش استراتژی', 'error')
      }
    } catch (error: any) {
      showToast('خطا در پردازش استراتژی', 'error')
      console.error('Error processing strategy:', error)
    } finally {
      setProcessing(false)
    }
  }

  const renderQuestionInput = (question: StrategyQuestion) => {
    const value = answers[question.id] || ''

    switch (question.question_type) {
      case 'boolean':
        return (
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name={`question-${question.id}`}
                value="true"
                checked={value === 'true'}
                onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                className="w-4 h-4"
              />
              <span className="text-gray-900">بله</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name={`question-${question.id}`}
                value="false"
                checked={value === 'false'}
                onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                className="w-4 h-4"
              />
              <span className="text-gray-900">خیر</span>
            </label>
          </div>
        )

      case 'choice':
      case 'multiple_choice':
        return (
          <div className="space-y-2">
            {question.options?.map((option, idx) => (
              <label key={idx} className="flex items-center gap-2 cursor-pointer">
                <input
                  type={question.question_type === 'multiple_choice' ? 'checkbox' : 'radio'}
                  name={`question-${question.id}`}
                  value={option}
                  checked={question.question_type === 'multiple_choice' 
                    ? value.split(',').includes(option)
                    : value === option}
                  onChange={(e) => {
                    if (question.question_type === 'multiple_choice') {
                      const current = value ? value.split(',') : []
                      const newValue = e.target.checked
                        ? [...current, option].join(',')
                        : current.filter(v => v !== option).join(',')
                      handleAnswerChange(question.id, newValue)
                    } else {
                      handleAnswerChange(question.id, e.target.value)
                    }
                  }}
                  className="w-4 h-4"
                />
                <span className="text-gray-900">{option}</span>
              </label>
            ))}
          </div>
        )

      case 'number':
        // Use text input instead of number input to allow decimals, fractions, and explanations
        return (
          <textarea
            value={value}
            onChange={(e) => handleAnswerChange(question.id, e.target.value)}
            className="w-full px-4 py-2 bg-white text-gray-900 placeholder:text-gray-500 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={2}
            placeholder="عدد را وارد کنید (مثلاً: 1، 1.5، 2.5، 10 یا توضیح)"
          />
        )

      default: // text
        return (
          <textarea
            value={value}
            onChange={(e) => handleAnswerChange(question.id, e.target.value)}
            className="w-full px-4 py-2 bg-white text-gray-900 placeholder:text-gray-500 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={3}
            placeholder="جواب خود را بنویسید..."
          />
        )
    }
  }

  const pendingQuestions = questions.filter(q => q.status === 'pending')
  const answeredQuestions = questions.filter(q => q.status === 'answered')

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8 min-h-[200px]">
        <div className="flex flex-col items-center gap-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="text-gray-400 text-sm">در حال بارگذاری سوالات...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 min-h-[200px]">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">
          💡 سوالات تعاملی برای تکمیل استراتژی
        </h3>
        <p className="text-blue-700 text-sm">
          برای تبدیل دقیق‌تر استراتژی به مدل قابل اجرا، لطفاً به سوالات زیر پاسخ دهید.
          سیستم از مدل‌های هوش مصنوعی (مانند OpenAI ChatGPT یا Gemini) برای تولید سوالات هوشمند استفاده می‌کند.
        </p>
      </div>

      {questions.length === 0 ? (
        <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-600 mb-4 text-base">هیچ سوالی تولید نشده است.</p>
          <p className="text-gray-500 text-sm mb-6">
            برای شروع، روی دکمه زیر کلیک کنید تا سوالات هوشمند تولید شوند.
          </p>
          <button
            onClick={handleGenerateQuestions}
            disabled={generating}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold text-base"
          >
            {generating ? 'در حال تولید...' : 'تولید سوالات هوشمند'}
          </button>
        </div>
      ) : (
        <>
          {pendingQuestions.length > 0 && (
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-gray-800">
                سوالات در انتظار پاسخ ({pendingQuestions.length})
              </h4>
              {pendingQuestions.map((question) => (
                <div
                  key={question.id}
                  className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-1 rounded">
                          سوال {question.order}
                        </span>
                        {question.context?.section && (
                          <span className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
                            {question.context.section === 'entry' && 'ورود'}
                            {question.context.section === 'exit' && 'خروج'}
                            {question.context.section === 'risk' && 'ریسک'}
                            {question.context.section === 'indicator' && 'اندیکاتور'}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-800 font-medium">{question.question_text}</p>
                      {question.context?.related_text && (
                        <p className="text-sm text-gray-500 mt-2 italic">
                          {question.context.related_text}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mb-4">
                    {renderQuestionInput(question)}
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSaveAnswer(question)}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                    >
                      ذخیره جواب
                    </button>
                    <button
                      onClick={() => handleSkipQuestion(question)}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 text-sm"
                    >
                      رد کردن
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {answeredQuestions.length > 0 && (
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-gray-800">
                سوالات پاسخ داده شده ({answeredQuestions.length})
              </h4>
              {answeredQuestions.map((question) => (
                <div
                  key={question.id}
                  className={`border rounded-lg p-4 ${
                    editingQuestionId === question.id 
                      ? 'bg-white border-blue-300' 
                      : 'bg-green-50 border-green-200'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-1 rounded">
                          سوال {question.order}
                        </span>
                        {question.context?.section && (
                          <span className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
                            {question.context.section === 'entry' && 'ورود'}
                            {question.context.section === 'exit' && 'خروج'}
                            {question.context.section === 'risk' && 'ریسک'}
                            {question.context.section === 'indicator' && 'اندیکاتور'}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-800 font-medium mb-2">{question.question_text}</p>
                      {question.context?.related_text && (
                        <p className="text-sm text-gray-500 mb-2 italic">
                          {question.context.related_text}
                        </p>
                      )}
                    </div>
                    {editingQuestionId !== question.id && (
                      <span className="bg-green-200 text-green-800 text-xs font-semibold px-2 py-1 rounded">
                        پاسخ داده شده
                      </span>
                    )}
                  </div>

                  {editingQuestionId === question.id ? (
                    <>
                      <div className="mb-4">
                        {renderQuestionInput(question)}
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleSaveAnswer(question)}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                        >
                          ذخیره تغییرات
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 text-sm"
                        >
                          لغو
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-green-700">
                          <span className="font-semibold">جواب:</span> {question.answer}
                        </p>
                      </div>
                      <button
                        onClick={() => handleEditAnswer(question)}
                        className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                      >
                        ویرایش
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {pendingQuestions.length === 0 && answeredQuestions.length > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-green-900 mb-2">
                ✅ همه سوالات پاسخ داده شدند
              </h4>
              <p className="text-green-700 mb-4">
                حالا می‌توانید استراتژی را با استفاده از جواب‌های شما پردازش کنید.
              </p>
              <button
                onClick={handleProcessWithAnswers}
                disabled={processing}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
              >
                {processing ? 'در حال پردازش...' : 'پردازش استراتژی با جواب‌ها'}
              </button>
            </div>
          )}

          {questions.length > 0 && (
            <div className="flex gap-2">
              <button
                onClick={handleGenerateQuestions}
                disabled={generating}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                {generating ? 'در حال تولید...' : 'تولید سوالات بیشتر'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

