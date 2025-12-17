import { useState } from 'react'

interface AIAnalysisDisplayProps {
  analysisText: string
  resultMetrics?: {
    total_return: number
    win_rate: number
    total_trades: number
    max_drawdown: number
  }
}

export default function AIAnalysisDisplay({ analysisText, resultMetrics }: AIAnalysisDisplayProps) {
  const [expanded, setExpanded] = useState(true)

  // Parse analysis text into structured sections
  const parseAnalysis = (text: string): Array<{ title: string; content: string; icon: string }> => {
    if (!text || typeof text !== 'string') {
      return [{ title: 'تحلیل هوش مصنوعی', content: 'تحلیلی برای نمایش وجود ندارد.', icon: '🤖' }]
    }
    
    // Clean up the text first - remove excessive formatting
    let cleanedText = text
      .replace(/^=+\s*$/gm, '') // Remove standalone separator lines
      .replace(/\n{3,}/g, '\n\n') // Replace 3+ newlines with double newline
      .replace(/^[\s\-•\*]+\s*/gm, (match) => match.trim() ? match : '') // Clean up bullet points
      .trim()
    
    let sections: Array<{ title: string; content: string; icon: string }> = []
    
    // Split by common section markers - more comprehensive matching
    const lines = cleanedText.split('\n')
    let currentSection: { title: string; content: string; icon: string } | null = null
    
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i].trim()
      
      // Skip empty lines at the start
      if (!line && !currentSection) continue
      
      // Detect section headers - improved patterns
      const isHeader = (patterns: string[]): boolean => {
        return patterns.some(pattern => line.includes(pattern))
      }
      
      if (isHeader(['تحلیل عملکرد کلی', 'عملکرد کلی', '📊 تحلیل عملکرد'])) {
        if (currentSection && currentSection.content.trim()) sections.push(currentSection)
        currentSection = { title: 'تحلیل عملکرد کلی', content: '', icon: '📊' }
        continue
      } else if (isHeader(['تحلیل معاملات', 'نتایج معاملات', '💹 تحلیل معاملات'])) {
        if (currentSection && currentSection.content.trim()) sections.push(currentSection)
        currentSection = { title: 'تحلیل معاملات', content: '', icon: '💹' }
        continue
      } else if (isHeader(['نقاط قوت', 'قوت', '✅ نقاط قوت'])) {
        if (currentSection && currentSection.content.trim()) sections.push(currentSection)
        currentSection = { title: 'نقاط قوت', content: '', icon: '✅' }
        continue
      } else if (isHeader(['نقاط ضعف', 'ضعف', '⚠️ نقاط ضعف'])) {
        if (currentSection && currentSection.content.trim()) sections.push(currentSection)
        currentSection = { title: 'نقاط ضعف', content: '', icon: '⚠️' }
        continue
      } else if (isHeader(['پیشنهادات', 'پیشنهادات بهبود', '💡 پیشنهادات', 'بهبود'])) {
        if (currentSection && currentSection.content.trim()) sections.push(currentSection)
        currentSection = { title: 'پیشنهادات بهبود', content: '', icon: '💡' }
        continue
      } else if (isHeader(['شرایط ورود', 'تحلیل ورود', '🚪 شرایط ورود'])) {
        if (currentSection && currentSection.content.trim()) sections.push(currentSection)
        currentSection = { title: 'تحلیل شرایط ورود', content: '', icon: '🚪' }
        continue
      } else if (isHeader(['شرایط خروج', 'تحلیل خروج', '🚶 شرایط خروج'])) {
        if (currentSection && currentSection.content.trim()) sections.push(currentSection)
        currentSection = { title: 'تحلیل شرایط خروج', content: '', icon: '🚶' }
        continue
      }
      
      // Skip separator lines and formatting artifacts
      if (line.match(/^[=\-_]{3,}$/)) continue
      
      // Add content to current section
      if (currentSection) {
        if (line) {
          // Clean up bullet points and formatting
          line = line.replace(/^[\s\-•\*▪▫]\s*/, '').trim()
          if (line) {
            currentSection.content += (currentSection.content ? '\n' : '') + line
          }
        }
      } else {
        // If no section detected yet, create a default one
        line = line.replace(/^[\s\-•\*▪▫]\s*/, '').trim()
        if (line && !line.match(/^[=\-_]{3,}$/)) {
          currentSection = { title: 'تحلیل کلی', content: line, icon: '📋' }
        }
      }
    }
    
    if (currentSection && currentSection.content.trim()) sections.push(currentSection)
    
    // Clean up section contents - remove excessive whitespace
    sections.forEach(section => {
      section.content = section.content
        .split('\n')
        .map(l => l.trim())
        .filter(l => l)
        .join('\n')
        .replace(/\n{3,}/g, '\n\n')
        .trim()
    })
    
    // Filter out weaknesses section if it's empty or has no meaningful content
    sections = sections.filter(section => {
      if (section.title === 'نقاط ضعف' || section.title.includes('نقاط ضعف')) {
        const content = section.content.trim()
        // Check if content is empty or just contains placeholder text
        if (!content || 
            content.length === 0 || 
            content === 'محتوایی برای نمایش وجود ندارد.' ||
            content.toLowerCase().includes('هیچ') ||
            content.toLowerCase().includes('ندارد')) {
          return false
        }
      }
      return true
    })
    
    // If no sections found or all sections are empty, return the whole text as one section
    if (sections.length === 0 || sections.every(s => !s.content.trim())) {
      return [{ title: 'تحلیل هوش مصنوعی', content: cleanedText, icon: '🤖' }]
    }
    
    return sections
  }

  const sections = parseAnalysis(analysisText)

  const getPerformanceColor = (value: number, type: 'return' | 'win_rate' | 'drawdown') => {
    if (type === 'return') {
      if (value >= 20) return 'text-green-400'
      if (value >= 10) return 'text-green-300'
      if (value >= 0) return 'text-yellow-400'
      return 'text-red-400'
    } else if (type === 'win_rate') {
      if (value >= 60) return 'text-green-400'
      if (value >= 50) return 'text-yellow-400'
      return 'text-red-400'
    } else {
      if (value <= 10) return 'text-green-400'
      if (value <= 20) return 'text-yellow-400'
      return 'text-red-400'
    }
  }

  const getPerformanceMessage = () => {
    if (!resultMetrics) return null
    
    const { total_return, win_rate } = resultMetrics
    
    if (total_return >= 30 && win_rate >= 60) {
      return {
        text: '🎉 عملکرد استثنایی! استراتژی شما بسیار موفق بوده است.',
        color: 'text-green-400',
        bg: 'bg-green-900/20',
        border: 'border-green-500'
      }
    } else if (total_return >= 10 && win_rate >= 50) {
      return {
        text: '✅ عملکرد خوب! استراتژی شما سودآور بوده است.',
        color: 'text-green-300',
        bg: 'bg-green-900/20',
        border: 'border-green-400'
      }
    } else if (total_return >= 0) {
      return {
        text: '📊 عملکرد متوسط. با بهینه‌سازی می‌توانید نتایج بهتری بگیرید.',
        color: 'text-yellow-400',
        bg: 'bg-yellow-900/20',
        border: 'border-yellow-500'
      }
    } else {
      return {
        text: '⚠️ نیاز به بهبود. پیشنهادات زیر را بررسی کنید.',
        color: 'text-orange-400',
        bg: 'bg-orange-900/20',
        border: 'border-orange-500'
      }
    }
  }

  const performanceMessage = getPerformanceMessage()

  return (
    <div className="bg-gradient-to-br from-blue-900/50 to-purple-900/50 border border-blue-700/50 rounded-lg p-6 mb-6 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <span>🤖 تحلیل هوش مصنوعی نتایج بک‌تست</span>
          <span className="text-xs bg-blue-600 px-2 py-1 rounded font-medium">AI</span>
        </h2>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-400 hover:text-white transition"
        >
          <svg
            className={`w-5 h-5 transition-transform ${expanded ? 'transform rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {resultMetrics && performanceMessage && (
        <div className={`mb-4 p-4 rounded-lg border ${performanceMessage.bg} ${performanceMessage.border} border-r-4`}>
          <p className={`${performanceMessage.color} font-medium`}>{performanceMessage.text}</p>
        </div>
      )}

      {resultMetrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="bg-gray-800/50 rounded p-3">
            <div className="text-gray-400 text-xs mb-1">بازدهی</div>
            <div className={`text-lg font-bold ${getPerformanceColor(resultMetrics.total_return, 'return')}`}>
              {resultMetrics.total_return > 0 ? '+' : ''}{resultMetrics.total_return.toFixed(2)}%
            </div>
          </div>
          <div className="bg-gray-800/50 rounded p-3">
            <div className="text-gray-400 text-xs mb-1">نرخ برد</div>
            <div className={`text-lg font-bold ${getPerformanceColor(resultMetrics.win_rate, 'win_rate')}`}>
              {resultMetrics.win_rate.toFixed(1)}%
            </div>
          </div>
          <div className="bg-gray-800/50 rounded p-3">
            <div className="text-gray-400 text-xs mb-1">معاملات</div>
            <div className="text-lg font-bold text-white">{resultMetrics.total_trades}</div>
          </div>
          <div className="bg-gray-800/50 rounded p-3">
            <div className="text-gray-400 text-xs mb-1">حداکثر افت</div>
            <div className={`text-lg font-bold ${getPerformanceColor(resultMetrics.max_drawdown, 'drawdown')}`}>
              {resultMetrics.max_drawdown.toFixed(2)}%
            </div>
          </div>
        </div>
      )}

      {expanded && (
        <div className="space-y-4">
          {sections.map((section, index) => (
            <div
              key={index}
              className="bg-gray-900/50 rounded-lg p-4 border border-blue-800/30"
            >
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">{section.icon}</span>
                <h3 className="text-lg font-semibold text-white">{section.title}</h3>
              </div>
              <div className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed text-right">
                {section.content || 'محتوایی برای نمایش وجود ندارد.'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

