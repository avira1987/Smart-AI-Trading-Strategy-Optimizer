import { useState, useEffect } from 'react'
import { getGapGPTModels, convertStrategyWithGapGPT, compareModelsWithGapGPT, GapGPTModel, saveGapGPTConversion, getSystemSettings } from '../api/client'
import { useToast } from './ToastProvider'

interface GapGPTConverterProps {
  strategyText?: string
  strategyId?: number  // ID استراتژی برای ذخیره
  onConverted?: (convertedStrategy: any) => void
  onClose?: () => void
  onSave?: () => void  // Callback بعد از ذخیره موفق
}

// Mapping برای توضیحات و کاربردهای مدل‌ها (بدون هزینه hardcoded)
const getModelInfo = (model: GapGPTModel, costPerWord: number = 0.001) => {
  const nameLower = model.name.toLowerCase()
  const ownedByLower = model.owned_by?.toLowerCase() || ''
  
  const costDisplay = `~${costPerWord.toFixed(4)} تومان/کلمه`
  
  // تشخیص نوع مدل بر اساس نام یا provider
  if (ownedByLower.includes('openai') || nameLower.includes('gpt')) {
    if (nameLower.includes('gpt-5') || nameLower.includes('gpt5')) {
      return {
        description: 'مدل پیشرفته و قدرتمند OpenAI با قابلیت‌های استدلال پیشرفته',
        cost: costDisplay,
        suitableFor: 'تحلیل‌های پیچیده، استدلال پیشرفته، کدنویسی و ریاضیات'
      }
    } else if (nameLower.includes('gpt-4.5') || nameLower.includes('gpt4.5')) {
      return {
        description: 'مدل خلاقانه و پیشرفته OpenAI برای وظایف پیچیده',
        cost: costDisplay,
        suitableFor: 'تولید محتوای خلاقانه، برنامه‌ریزی پیچیده، تحلیل‌های حرفه‌ای'
      }
    } else if (nameLower.includes('gpt-4o') || nameLower.includes('gpt4o') || nameLower.includes('gpt-40')) {
      if (nameLower.includes('mini')) {
        return {
          description: 'مدل سریع و مقرون‌به‌صرفه OpenAI با عملکرد عالی',
          cost: costDisplay,
          suitableFor: 'تحلیل‌های روزمره، تبدیل استراتژی‌ها، کارهای سریع'
        }
      } else {
        return {
          description: 'مدل قدرتمند و همه‌کاره OpenAI با دقت بالا',
          cost: costDisplay,
          suitableFor: 'تحلیل‌های دقیق، تبدیل استراتژی‌های پیچیده، تولید محتوای باکیفیت'
        }
      }
    } else if (nameLower.includes('gpt-4.1') || nameLower.includes('gpt4.1')) {
      if (nameLower.includes('mini')) {
        return {
          description: 'نسخه کوچک و سریع GPT-4.1 برای کارهای سریع',
          cost: costDisplay,
          suitableFor: 'کارهای سریع، تحلیل‌های ساده، تبدیل استراتژی‌های کوتاه'
        }
      } else {
        return {
          description: 'مدل پیشرفته GPT-4.1 با قابلیت‌های بهبود یافته',
          cost: costDisplay,
          suitableFor: 'تحلیل‌های متوسط تا پیچیده، تبدیل استراتژی‌ها'
        }
      }
    } else if (nameLower.includes('chatgpt')) {
      return {
        description: 'مدل ChatGPT برای مکالمات و تحلیل‌های تعاملی',
        cost: costDisplay,
        suitableFor: 'مکالمات تعاملی، تحلیل‌های سریع، تبدیل استراتژی‌ها'
      }
    }
    // پیش‌فرض برای مدل‌های OpenAI دیگر
    return {
      description: 'مدل OpenAI با عملکرد متعادل',
      cost: costDisplay,
      suitableFor: 'تحلیل و تبدیل استراتژی‌های معاملاتی'
    }
  } else if (ownedByLower.includes('anthropic') || ownedByLower.includes('vertex') || nameLower.includes('claude')) {
    if (nameLower.includes('haiku')) {
      return {
        description: 'مدل سریع و مقرون‌به‌صرفه Anthropic برای کارهای سریع',
        cost: costDisplay,
        suitableFor: 'تحلیل‌های سریع، تبدیل استراتژی‌های ساده، کارهای روزمره'
      }
    } else if (nameLower.includes('sonnet')) {
      return {
        description: 'مدل متعادل Anthropic با تعادل خوب بین سرعت و کیفیت',
        cost: costDisplay,
        suitableFor: 'تحلیل‌های متوسط، تبدیل استراتژی‌های پیچیده، تولید محتوا'
      }
    } else if (nameLower.includes('opus')) {
      return {
        description: 'قدرتمندترین مدل Anthropic با بالاترین دقت',
        cost: costDisplay,
        suitableFor: 'تحلیل‌های پیچیده و حرفه‌ای، تبدیل استراتژی‌های پیشرفته'
      }
    }
    // پیش‌فرض برای مدل‌های Anthropic
    return {
      description: 'مدل Anthropic با تمرکز بر ایمنی و دقت',
      cost: costDisplay,
      suitableFor: 'تحلیل و تبدیل استراتژی‌های معاملاتی با دقت بالا'
    }
  }
  
  // پیش‌فرض برای سایر مدل‌ها
  return {
    description: model.description || 'مدل هوش مصنوعی برای تبدیل استراتژی',
    cost: costDisplay,
    suitableFor: 'تحلیل و تبدیل استراتژی‌های معاملاتی'
  }
}

export default function GapGPTConverter({ strategyText = '', strategyId, onConverted, onClose, onSave }: GapGPTConverterProps) {
  const [models, setModels] = useState<GapGPTModel[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingModels, setLoadingModels] = useState(true)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [text, setText] = useState(strategyText)
  const [showGuide, setShowGuide] = useState(!strategyText.trim())
  const [textareaRef, setTextareaRef] = useState<HTMLTextAreaElement | null>(null)
  const [temperature, setTemperature] = useState(0.3)
  const [maxTokens, setMaxTokens] = useState(4000)
  const [mode, setMode] = useState<'single' | 'compare'>('single')
  const [selectedModels, setSelectedModels] = useState<string[]>([])
  const [result, setResult] = useState<any>(null)
  const [compareResults, setCompareResults] = useState<any>(null)
  const [saving, setSaving] = useState(false)
  const [modelCosts, setModelCosts] = useState<{ [key: string]: number }>({})
  const defaultCost = 0.001
  const { showToast } = useToast()

  useEffect(() => {
    loadModels()
    loadModelCosts()
  }, [])

  const loadModelCosts = async () => {
    try {
      const response = await getSystemSettings()
      if (response.data.model_costs) {
        setModelCosts(response.data.model_costs)
      }
    } catch (error) {
      console.error('Error loading model costs:', error)
    }
  }

  useEffect(() => {
    if (strategyText) {
      setText(strategyText)
      setShowGuide(false)
    }
  }, [strategyText])

  useEffect(() => {
    if (!showGuide && textareaRef) {
      textareaRef.focus()
    }
  }, [showGuide, textareaRef])

  const loadModels = async () => {
    try {
      setLoadingModels(true)
      const response = await getGapGPTModels()
      if (response.data.status === 'success') {
        const modelsList = response.data.models || []
        setModels(modelsList)
        if (modelsList.length > 0) {
          // پیش‌فرض: اولین مدل
          setSelectedModel(modelsList[0].id)
        }
      }
    } catch (error: any) {
      console.error('Error loading GapGPT models:', error)
      showToast('خطا در دریافت لیست مدل‌ها', { type: 'error' })
    } finally {
      setLoadingModels(false)
    }
  }

  const handleConvert = async () => {
    if (!text.trim()) {
      showToast('لطفاً متن استراتژی را وارد کنید', { type: 'warning' })
      return
    }

    if (mode === 'single' && !selectedModel) {
      showToast('لطفاً یک مدل انتخاب کنید', { type: 'warning' })
      return
    }

    try {
      setLoading(true)
      setResult(null)
      setCompareResults(null)

      if (mode === 'single') {
        const response = await convertStrategyWithGapGPT({
          strategy_text: text,
          model_id: selectedModel,
          temperature,
          max_tokens: maxTokens
        })

        if (response.data.status === 'success' && response.data.data?.success) {
          setResult(response.data.data)
          showToast('استراتژی با موفقیت تبدیل شد!', { type: 'success' })
          if (onConverted) {
            onConverted(response.data.data.converted_strategy)
          }
        } else {
          showToast(response.data.message || response.data.data?.error || 'خطا در تبدیل استراتژی', { type: 'error' })
        }
      } else {
        // مقایسه چند مدل
        const modelsToCompare = selectedModels.length > 0 ? selectedModels : models.slice(0, 3).map(m => m.id)
        if (modelsToCompare.length === 0) {
          showToast('لطفاً حداقل یک مدل انتخاب کنید', { type: 'warning' })
          setLoading(false)
          return
        }

        const response = await compareModelsWithGapGPT({
          strategy_text: text,
          models: modelsToCompare,
          temperature,
          max_tokens: maxTokens
        })

        if (response.data.status === 'success' && response.data.data) {
          setCompareResults(response.data.data)
          showToast('مقایسه مدل‌ها با موفقیت انجام شد!', { type: 'success' })
          if (response.data.data.best_result && onConverted) {
            onConverted(response.data.data.best_result.result.converted_strategy)
          }
        } else {
          showToast(response.data.message || 'خطا در مقایسه مدل‌ها', { type: 'error' })
        }
      }
    } catch (error: any) {
      console.error('Error converting strategy:', error)
      showToast(error.response?.data?.message || error.message || 'خطا در تبدیل استراتژی', { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">پردازش استراتژی با هوش مصنوعی</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl font-bold"
            title="بستن"
          >
            ×
          </button>
        )}
      </div>

      {/* Mode Selection */}
      <div className="flex gap-4">
        <button
          onClick={() => {
            setMode('single')
            setCompareResults(null)
          }}
          className={`px-4 py-2 rounded transition-colors ${
            mode === 'single' 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          تبدیل با یک مدل
        </button>
        <button
          onClick={() => {
            setMode('compare')
            setResult(null)
          }}
          className={`px-4 py-2 rounded transition-colors ${
            mode === 'compare' 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          مقایسه چند مدل
        </button>
      </div>

      {/* Strategy Text Input */}
      <div>
        <label className="block text-white mb-2 font-semibold">متن استراتژی</label>
        {showGuide && !text.trim() ? (
          <div 
            onClick={() => setShowGuide(false)}
            className="w-full bg-gray-700 rounded p-4 min-h-[200px] border border-gray-600 text-gray-400 text-sm leading-relaxed cursor-text hover:border-blue-500 transition-colors"
          >
            <p className="mb-3"><strong className="text-white">📝 راهنمای آپلود استراتژی برای بهترین نتایج بک‌تست:</strong></p>
            <ul className="space-y-2 mr-4 list-disc">
              <li><strong className="text-white">استراتژی کامل و واضح:</strong> شامل تمام قوانین معاملاتی، شرایط ورود و خروج، مدیریت ریسک و پارامترهای قابل تنظیم</li>
              <li><strong className="text-white">کد تمیز و ساختاریافته:</strong> از کدهای تمیز و خوش‌خوان استفاده کنید. کامنت‌های واضح و نام‌گذاری مناسب متغیرها</li>
              <li><strong className="text-white">توضیحات کامل:</strong> در ابتدای فایل، توضیح دهید که استراتژی چه کاری انجام می‌دهد، برای چه بازه زمانی مناسب است</li>
              <li><strong className="text-white">پارامترهای قابل تنظیم:</strong> تمام پارامترهای مهم (stop loss، take profit، دوره‌های اندیکاتورها) را به صورت متغیر تعریف کنید</li>
              <li><strong className="text-white">منطق معاملاتی واضح:</strong> شرایط ورود و خروج باید به صورت واضح و منطقی تعریف شده باشند</li>
            </ul>
            <p className="mt-4 text-yellow-300 text-xs">
              💡 <strong>نکته مهم:</strong> هرچه استراتژی شما کامل‌تر و واضح‌تر باشد، هوش مصنوعی می‌تواند آن را بهتر پردازش کند و در نتیجه بک‌تست‌های دقیق‌تر و بازدهی بالاتری دریافت خواهید کرد.
            </p>
            <p className="mt-3 text-center text-gray-500">
              👆 برای شروع، روی این باکس کلیک کنید و متن استراتژی خود را وارد کنید یا فایل را کپی کنید
            </p>
          </div>
        ) : (
          <textarea
            ref={(el) => setTextareaRef(el)}
            value={text}
            onChange={(e) => {
              setText(e.target.value)
              if (e.target.value.trim()) {
                setShowGuide(false)
              }
            }}
            onFocus={() => setShowGuide(false)}
            placeholder="متن استراتژی معاملاتی خود را اینجا وارد کنید..."
            className="w-full bg-gray-700 text-white rounded p-3 min-h-[200px] border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        )}
        {text.trim() && <p className="text-gray-400 text-sm mt-1">{text.length} کاراکتر</p>}
      </div>

      {/* Model Selection */}
      {loadingModels ? (
        <div className="text-gray-400 text-center py-4">در حال بارگذاری مدل‌ها...</div>
      ) : models.length === 0 ? (
        <div className="text-yellow-400 text-center py-4">هیچ مدلی یافت نشد. لطفاً کلید API GapGPT را در تنظیمات اضافه کنید.</div>
      ) : (
        <>
          {mode === 'single' ? (
            <div>
              <label className="block text-white mb-2 font-semibold">انتخاب مدل</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-gray-700 text-white rounded p-3 border border-gray-600 focus:border-blue-500 focus:outline-none"
              >
                {models.map((model) => {
                  const costPerWord = modelCosts[model.id] || defaultCost
                  const modelInfo = getModelInfo(model, costPerWord)
                  return (
                    <option key={model.id} value={model.id}>
                      {model.name} - {modelInfo.description} (هزینه: {modelInfo.cost})
                    </option>
                  )
                })}
              </select>
              {selectedModel && (() => {
                const selectedModelData = models.find(m => m.id === selectedModel)
                if (!selectedModelData) return null
                const costPerWord = modelCosts[selectedModelData.id] || defaultCost
                const modelInfo = getModelInfo(selectedModelData, costPerWord)
                return (
                  <div className="mt-3 p-3 bg-gray-900 rounded-lg border border-gray-700">
                    <p className="text-sm text-gray-300 mb-2">
                      <strong className="text-white">{selectedModelData.name}:</strong> {modelInfo.description}
                    </p>
                    <p className="text-xs text-gray-400">
                      <strong>💰 هزینه:</strong> {modelInfo.cost}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      <strong>✅ مناسب برای:</strong> {modelInfo.suitableFor}
                    </p>
                    {selectedModelData.owned_by && (
                      <p className="text-xs text-gray-500 mt-1">
                        ارائه‌دهنده: {selectedModelData.owned_by}
                      </p>
                    )}
                  </div>
                )
              })()}
            </div>
          ) : (
            <div>
              <label className="block text-white mb-2 font-semibold">انتخاب مدل‌ها برای مقایسه</label>
              <div className="grid grid-cols-1 gap-2 max-h-[300px] overflow-y-auto bg-gray-700 p-3 rounded border border-gray-600">
                {models.map((model) => {
                  const costPerWord = modelCosts[model.id] || defaultCost
                  const modelInfo = getModelInfo(model, costPerWord)
                  return (
                    <label key={model.id} className="flex items-start space-x-2 space-x-reverse text-white cursor-pointer hover:bg-gray-600 p-2 rounded">
                      <input
                        type="checkbox"
                        checked={selectedModels.includes(model.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedModels([...selectedModels, model.id])
                          } else {
                            setSelectedModels(selectedModels.filter(id => id !== model.id))
                          }
                        }}
                        className="w-4 h-4 mt-1"
                      />
                      <div className="flex-1">
                        <span className="text-sm font-semibold block">{model.name}</span>
                        <span className="text-xs text-gray-400 block mt-1">{modelInfo.description}</span>
                        <div className="flex gap-3 mt-1 text-xs text-gray-500">
                          <span>💰 {modelInfo.cost}</span>
                          <span>✅ {modelInfo.suitableFor}</span>
                        </div>
                      </div>
                    </label>
                  )
                })}
              </div>
              {selectedModels.length === 0 && (
                <p className="text-yellow-400 text-sm mt-2">
                  ⚠ اگر مدلی انتخاب نکنید، 3 مدل اول به طور خودکار انتخاب می‌شوند
                </p>
              )}
              {selectedModels.length > 0 && (
                <p className="text-green-400 text-sm mt-2">
                  ✓ {selectedModels.length} مدل انتخاب شده
                </p>
              )}
            </div>
          )}
        </>
      )}

      {/* Advanced Options */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-white font-semibold">Temperature (0.0 - 2.0)</label>
            <button
              type="button"
              onClick={(e) => {
                const details = e.currentTarget.nextElementSibling as HTMLDetailsElement
                details.open = !details.open
              }}
              className="text-blue-400 hover:text-blue-300 text-xs underline"
            >
              📖 راهنما
            </button>
          </div>
          <input
            type="number"
            min="0"
            max="2"
            step="0.1"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
          <div className="mt-2 space-y-2">
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-700 rounded-full h-2 relative">
                <div 
                  className="absolute left-0 top-0 h-full bg-gradient-to-r from-blue-500 via-green-500 to-yellow-500 rounded-full"
                  style={{ width: `${(temperature / 2) * 100}%` }}
                ></div>
              </div>
              <span className="text-gray-400 text-xs min-w-[50px] text-left">
                {temperature.toFixed(1)}
              </span>
            </div>
            <p className="text-gray-400 text-xs">
              {temperature <= 0.3 
                ? '🎯 دقت بالا - مناسب برای تحلیل‌های دقیق'
                : temperature <= 0.7
                ? '⚖️ متعادل - تعادل بین دقت و خلاقیت'
                : '✨ خلاقانه - مناسب برای تولید محتوای متنوع'
              }
            </p>
          </div>
          
          {/* راهنمای کامل Temperature */}
          <details className="mt-3 bg-gray-900 rounded-lg p-3 border border-gray-700">
            <summary className="text-blue-400 hover:text-blue-300 cursor-pointer text-sm font-semibold mb-2">
              💡 راهنمای تنظیم Temperature
            </summary>
            <div className="text-xs text-gray-300 space-y-3 mt-2">
              <div>
                <p className="text-white font-semibold mb-1">Temperature چیست؟</p>
                <p className="text-gray-400 leading-relaxed">
                  Temperature میزان تصادفی بودن و خلاقیت خروجی مدل هوش مصنوعی را کنترل می‌کند. 
                  این پارامتر تعیین می‌کند که مدل چقدر از پاسخ‌های محتمل‌تر فاصله بگیرد.
                </p>
              </div>
              
              <div className="space-y-2">
                <p className="text-white font-semibold mb-1">مقادیر پیشنهادی:</p>
                
                <div className="bg-gray-800 p-2 rounded border-r-4 border-blue-500">
                  <p className="text-blue-300 font-semibold mb-1">0.0 - 0.3: دقت بالا 🎯</p>
                  <ul className="text-gray-400 space-y-1 mr-4 list-disc">
                    <li>پاسخ‌های قابل پیش‌بینی و یکنواخت</li>
                    <li>مناسب برای: پارس استراتژی‌های معاملاتی، تحلیل‌های فنی، استخراج داده‌های ساختاریافته</li>
                    <li>پیشنهاد می‌شود برای: تبدیل استراتژی‌های معاملاتی</li>
                  </ul>
                </div>
                
                <div className="bg-gray-800 p-2 rounded border-r-4 border-green-500">
                  <p className="text-green-300 font-semibold mb-1">0.4 - 0.7: متعادل ⚖️</p>
                  <ul className="text-gray-400 space-y-1 mr-4 list-disc">
                    <li>تعادل بین دقت و تنوع</li>
                    <li>مناسب برای: تحلیل‌های عمومی، توضیحات استراتژی، پیشنهادات بهبود</li>
                    <li>پیشنهاد می‌شود برای: تحلیل نتایج بک‌تست</li>
                  </ul>
                </div>
                
                <div className="bg-gray-800 p-2 rounded border-r-4 border-yellow-500">
                  <p className="text-yellow-300 font-semibold mb-1">0.8 - 2.0: خلاقانه ✨</p>
                  <ul className="text-gray-400 space-y-1 mr-4 list-disc">
                    <li>پاسخ‌های متنوع و غیرقابل پیش‌بینی</li>
                    <li>مناسب برای: تولید ایده‌های جدید، استراتژی‌های خلاقانه، محتوای متنوع</li>
                    <li>هشدار: ممکن است پاسخ‌های نامرتبط یا غیردقیق تولید کند</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-blue-900 bg-opacity-30 p-2 rounded border border-blue-700">
                <p className="text-blue-300 font-semibold mb-1">💡 نکات مهم:</p>
                <ul className="text-gray-300 space-y-1 mr-4 list-disc text-xs">
                  <li>مقدار پیش‌فرض (0.3) برای اکثر کارهای تحلیلی مناسب است</li>
                  <li>برای استراتژی‌های پیچیده، از 0.2-0.4 استفاده کنید</li>
                  <li>اگر پاسخ‌ها خیلی تکراری شدند، مقدار را کمی افزایش دهید (0.1-0.2)</li>
                  <li>اگر پاسخ‌ها نامرتبط شدند، مقدار را کاهش دهید</li>
                  <li>مقادیر بالای 1.0 معمولاً برای تحلیل استراتژی توصیه نمی‌شود</li>
                </ul>
              </div>
              
              <div className="bg-green-900 bg-opacity-20 p-2 rounded border border-green-700">
                <p className="text-green-300 font-semibold mb-1">✅ پیشنهاد برای این پروژه:</p>
                <p className="text-gray-300 text-xs">
                  برای تبدیل استراتژی‌های معاملاتی، مقدار <strong className="text-white">0.2 تا 0.4</strong> را امتحان کنید. 
                  این بازه بهترین تعادل بین دقت و انعطاف‌پذیری را ارائه می‌دهد.
                </p>
              </div>
            </div>
          </details>
        </div>
        <div>
          <label className="block text-white mb-2 font-semibold">Max Tokens</label>
          <input
            type="number"
            min="100"
            max="8000"
            step="100"
            value={maxTokens}
            onChange={(e) => setMaxTokens(parseInt(e.target.value))}
            className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
          <p className="text-gray-400 text-xs mt-1">حداکثر طول پاسخ</p>
        </div>
      </div>

      {/* Convert Button */}
      <button
        onClick={handleConvert}
        disabled={loading || loadingModels || !text.trim()}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white py-3 rounded font-semibold transition-colors"
      >
        {loading ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            در حال تبدیل...
          </span>
        ) : (
          mode === 'single' ? '🔮 تبدیل استراتژی' : '📊 مقایسه مدل‌ها'
        )}
      </button>

      {/* Results - Single Model */}
      {result && result.converted_strategy && (
        <div className="mt-6 bg-gray-900 rounded p-4 border border-gray-700">
          <h3 className="text-white font-bold mb-3 text-lg">✓ نتیجه تبدیل</h3>
          <div className="text-sm text-gray-400 mb-3 flex gap-4">
            <span>مدل: <span className="text-green-400">{result.model_used}</span></span>
            <span>توکن‌ها: <span className="text-green-400">{result.tokens_used}</span></span>
            <span>زمان: <span className="text-green-400">{result.latency_ms.toFixed(0)}ms</span></span>
          </div>
          <pre className="bg-black text-green-400 p-4 rounded overflow-auto max-h-[400px] text-xs border border-gray-800 mb-4">
            {JSON.stringify(result.converted_strategy, null, 2)}
          </pre>
          {strategyId && (
            <button
              onClick={async () => {
                if (!strategyId) return
                try {
                  setSaving(true)
                  await saveGapGPTConversion(strategyId, {
                    converted_strategy: result.converted_strategy,
                    model_used: result.model_used,
                    tokens_used: result.tokens_used
                  })
                  showToast('استراتژی تبدیل شده با موفقیت ذخیره شد!', { type: 'success' })
                  if (onSave) {
                    onSave()
                  }
                } catch (error: any) {
                  console.error('Error saving GapGPT conversion:', error)
                  showToast(error.response?.data?.message || 'خطا در ذخیره استراتژی', { type: 'error' })
                } finally {
                  setSaving(false)
                }
              }}
              disabled={saving}
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white py-3 rounded font-semibold transition-colors flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  در حال ذخیره...
                </>
              ) : (
                <>
                  <span>💾</span>
                  <span>ذخیره استراتژی تبدیل شده</span>
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* Results - Compare Models */}
      {compareResults && (
        <div className="mt-6 space-y-4">
          <h3 className="text-white font-bold text-lg">📊 نتایج مقایسه</h3>
          
          {/* Summary */}
          {compareResults.summary && (
            <div className="bg-gray-900 rounded p-4 border border-gray-700">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">کل مدل‌ها:</span>
                  <span className="text-white ml-2">{compareResults.summary.total_models}</span>
                </div>
                <div>
                  <span className="text-gray-400">موفق:</span>
                  <span className="text-green-400 ml-2">{compareResults.summary.successful_models}</span>
                </div>
                <div>
                  <span className="text-gray-400">ناموفق:</span>
                  <span className="text-red-400 ml-2">{compareResults.summary.failed_models}</span>
                </div>
                <div>
                  <span className="text-gray-400">بهترین امتیاز:</span>
                  <span className="text-yellow-400 ml-2">{compareResults.summary.best_score}/7</span>
                </div>
              </div>
            </div>
          )}
          
          {/* Best Result */}
          {compareResults.best_result && compareResults.best_result.result?.converted_strategy && (
            <div className="bg-green-900 bg-opacity-30 rounded p-4 border-2 border-green-500">
              <h4 className="text-white font-bold mb-2">
                🏆 بهترین مدل: <span className="text-green-400">{compareResults.best_result.model_id}</span>
                {' '}(امتیاز: <span className="text-yellow-400">{compareResults.best_result.score}/7</span>)
              </h4>
              <pre className="bg-black text-green-400 p-4 rounded overflow-auto max-h-[300px] text-xs border border-gray-800 mb-4">
                {JSON.stringify(compareResults.best_result.result.converted_strategy, null, 2)}
              </pre>
              {strategyId && (
                <button
                  onClick={async () => {
                    if (!strategyId || !compareResults.best_result) return
                    try {
                      setSaving(true)
                      await saveGapGPTConversion(strategyId, {
                        converted_strategy: compareResults.best_result.result.converted_strategy,
                        model_used: compareResults.best_result.model_id,
                        tokens_used: compareResults.best_result.result.tokens_used || 0
                      })
                      showToast('استراتژی تبدیل شده با موفقیت ذخیره شد!', { type: 'success' })
                      if (onSave) {
                        onSave()
                      }
                    } catch (error: any) {
                      console.error('Error saving GapGPT conversion:', error)
                      showToast(error.response?.data?.message || 'خطا در ذخیره استراتژی', { type: 'error' })
                    } finally {
                      setSaving(false)
                    }
                  }}
                  disabled={saving}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white py-3 rounded font-semibold transition-colors flex items-center justify-center gap-2"
                >
                  {saving ? (
                    <>
                      <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      در حال ذخیره...
                    </>
                  ) : (
                    <>
                      <span>💾</span>
                      <span>ذخیره بهترین استراتژی</span>
                    </>
                  )}
                </button>
              )}
            </div>
          )}

          {/* All Results */}
          {compareResults.all_results && (
            <div className="space-y-2">
              <h4 className="text-white font-bold">همه نتایج:</h4>
              {Object.entries(compareResults.all_results).map(([modelId, result]: [string, any]) => (
                <details key={modelId} className="bg-gray-900 rounded p-3 border border-gray-700">
                  <summary className="text-white cursor-pointer hover:text-blue-400">
                    {result.success ? (
                      <span>
                        ✓ <span className="font-semibold">{modelId}</span> - موفق 
                        {result.score !== undefined && <span className="text-yellow-400 ml-2">(امتیاز: {result.score}/7)</span>}
                      </span>
                    ) : (
                      <span>
                        ✗ <span className="font-semibold">{modelId}</span> - ناموفق: 
                        <span className="text-red-400 ml-2">{result.error || 'خطای نامشخص'}</span>
                      </span>
                    )}
                  </summary>
                  {result.success && result.converted_strategy && (
                    <pre className="text-xs text-gray-400 mt-3 overflow-auto max-h-[200px] bg-black p-3 rounded border border-gray-800">
                      {JSON.stringify(result.converted_strategy, null, 2)}
                    </pre>
                  )}
                </details>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

