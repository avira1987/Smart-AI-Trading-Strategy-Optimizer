import axios from 'axios'
import { navigateTo } from '../utils/navigation'

// Auto-detect API URL based on current hostname
// This allows access from local network IPs
function getApiBaseUrl(): string {
  // In development, use Vite proxy which automatically handles local network IPs
  // The proxy will forward requests to backend on localhost:8000
  if (import.meta.env.DEV) {
    // Use relative URL to leverage Vite proxy
    // This works for both localhost and local network IPs
    return '/api'
  }
  
  // In production, use the actual API URL
  const hostname = window.location.hostname
  const protocol = window.location.protocol
  
  // If accessing via localhost or 127.0.0.1, use localhost
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000/api'
  }
  
  // Otherwise, use the same hostname with port 8000
  return `${protocol}//${hostname}:8000/api`
}

const API_BASE_URL = getApiBaseUrl()

// Log API base URL for debugging (only in development)
if (import.meta.env.DEV) {
  console.log('API Base URL:', API_BASE_URL)
  console.log('Current hostname:', window.location.hostname)
  console.log('Using Vite proxy:', API_BASE_URL === '/api')
}

// Function to get CSRF token from cookies
function getCsrfToken(): string | null {
  const name = 'csrftoken'
  let cookieValue = null
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for session cookies
  timeout: 10000, // 10 second timeout to prevent hanging
})

// Add request interceptor to include CSRF token
client.interceptors.request.use(
  (config) => {
    // Get CSRF token from cookie
    const csrfToken = getCsrfToken()
    if (csrfToken) {
      // Set X-CSRFToken header for state-changing operations
      if (config.method && ['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
        config.headers['X-CSRFToken'] = csrfToken
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor to handle authentication errors
let isRedirectingToLogin = false // Flag to prevent multiple redirects

client.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log network errors for debugging
    if (!error.response) {
      // Network error (timeout, connection refused, etc.)
      console.error('Network error:', {
        message: error.message,
        code: error.code,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
      })
      
      // If it's a timeout or network error on auth check, don't block the page
      const requestUrl = error.config?.url || ''
      const isAuthCheckEndpoint = requestUrl.includes('/auth/check/')
      
      if (isAuthCheckEndpoint) {
        // For auth check, return a response that indicates not authenticated
        // This allows the page to continue loading
        return Promise.resolve({
          data: {
            success: false,
            authenticated: false,
          },
          status: 200,
          statusText: 'OK',
          headers: {},
          config: error.config,
        })
      }
    }
    
    if (error.response?.status === 403) {
      // 403 Forbidden - authentication failed or CSRF token missing
      console.error('403 Forbidden - Authentication required or CSRF token missing')
      
      // Don't redirect if this is an authentication check endpoint (periodic background check)
      // This prevents page refreshes during periodic authentication checks
      const requestUrl = error.config?.url || ''
      const isAuthCheckEndpoint = requestUrl.includes('/auth/check/')
      
      // Only redirect for user-initiated requests, not background checks
      if (!isAuthCheckEndpoint && !isRedirectingToLogin && window.location.pathname !== '/login') {
        isRedirectingToLogin = true
        
        // Clear local storage
        localStorage.removeItem('user')
        localStorage.removeItem('device_id')
        
        // Redirect to login using React Router (no page refresh)
        navigateTo('/login')
        
        // Reset flag after navigation completes
        setTimeout(() => {
          isRedirectingToLogin = false
        }, 1000)
      }
    }
    return Promise.reject(error)
  }
)

export interface APIConfiguration {
  id: number
  provider: string
  api_key: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TradingStrategy {
  id: number
  name: string
  description: string
  strategy_file: string
  is_active: boolean
  uploaded_at: string
  parsed_strategy_data?: any
  processing_status?: 'not_processed' | 'processing' | 'processed' | 'failed'
  processed_at?: string | null
  processing_error?: string
}

export interface Job {
  id: number
  strategy: number
  strategy_name?: string
  job_type: string
  status: string
  created_at: string
  started_at?: string
  completed_at?: string
  result?: Result
  error_message?: string
}

export interface Result {
  id: number
  job: number
  total_return: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  max_drawdown: number
  equity_curve_data: Array<{date: string, equity: number}>
  description?: string
  trades_details?: Array<{
    entry_date: string
    exit_date: string
    entry_price: number
    exit_price: number
    pnl: number
    pnl_percent: number
    duration_days: number
    entry_reason_fa?: string
    exit_reason_fa?: string
  }>
  created_at: string
}

// API Configuration
export const getAPIConfigurations = () => client.get('/apis/')
export const addAPIConfiguration = (data: Partial<APIConfiguration>) => client.post('/apis/', data)
export const updateAPIConfiguration = (id: number, data: Partial<APIConfiguration>) => client.put(`/apis/${id}/`, data)
export const deleteAPIConfiguration = (id: number) => client.delete(`/apis/${id}/`)

// Strategies
export const getStrategies = () => client.get('/strategies/')
export const addStrategy = (formData: FormData) => client.post('/strategies/', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
export const deleteStrategy = (id: number) => client.delete(`/strategies/${id}/`)
export const processStrategy = (id: number) => client.post(`/strategies/${id}/process/`)
export const generateStrategyQuestions = (id: number) => client.post(`/strategies/${id}/generate_questions/`)
export const processStrategyWithAnswers = (id: number) => client.post(`/strategies/${id}/process_with_answers/`)

// Jobs
export const getJobs = () => client.get('/jobs/')
export const createJob = (data: { strategy: number, job_type: string, timeframe_days?: number, symbol?: string, initial_capital?: number, selected_indicators?: string[] }) => client.post('/jobs/', data)
export const getJobStatus = (id: number) => client.get(`/jobs/${id}/status/`)

// Precheck
export const precheckBacktest = (strategyId: number) => client.post('/precheck/backtest/', { strategy: strategyId })

// Results
export const getResults = () => client.get('/results/')
export const deleteResult = (id: number) => client.delete(`/results/${id}/`)
export const clearResults = (jobId?: number) =>
  client.delete(`/results/clear/`, { params: jobId ? { job: jobId } : {} })

// Strategy Management
export const toggleStrategyActive = (id: number) => client.post(`/strategies/${id}/toggle_active/`)

// Data Provider APIs
export const testAPIConfiguration = (id: number) => client.post(`/apis/${id}/test/`)
export const getAvailableProviders = () => client.get('/apis/available_providers/')
export const testMT5Connection = () => client.post('/apis/test_mt5/')

// Market Data
export const getMT5Candles = (symbol: string, count: number = 500) =>
  client.get(`/market/mt5_candles/`, {
    params: {
      source: 'mt5_candles',
      symbol,
      count,
    },
  })

// Live Trading
export interface LiveTrade {
  id: number
  strategy: number | null
  strategy_name?: string
  mt5_ticket: number
  symbol: string
  trade_type: 'buy' | 'sell'
  volume: number
  open_price: number
  current_price: number | null
  stop_loss: number | null
  take_profit: number | null
  profit: number
  swap: number
  commission: number
  status: 'open' | 'closed' | 'pending'
  opened_at: string
  closed_at: string | null
  close_price: number | null
  close_reason: string
}

export interface AccountInfo {
  balance: number
  equity: number
  margin: number
  free_margin: number
  margin_level: number
  currency: string
  server: string
  login: number
  name: string
  leverage: number
  is_demo?: boolean
  trade_mode?: number
}

export const getLiveTrades = () => client.get<LiveTrade[]>('/trades/')
export const getLiveTrade = (id: number) => client.get<LiveTrade>(`/trades/${id}/`)
export const getAccountInfo = () => client.get<{status: string, account: AccountInfo}>('/trades/account_info/')
export const getMT5Positions = (symbol?: string) => client.get<{status: string, positions: any[]}>('/trades/mt5_positions/', { params: symbol ? { symbol } : {} })
export const getMarketStatus = () => client.get<{status: string, market_open: boolean, message: string}>('/trades/market_status/')
export const openTrade = (data: {
  strategy_id: number
  symbol?: string
  trade_type: 'buy' | 'sell'
  volume: number
  stop_loss?: number
  take_profit?: number
}) => client.post<{status: string, message: string, trade: LiveTrade}>('/trades/open_trade/', data)
export const closeTrade = (id: number, volume?: number) => client.post<{status: string, message: string, trade: LiveTrade}>(`/trades/${id}/close_trade/`, volume ? { volume } : {})
export const syncPositions = () => client.post<{status: string, synced: number, updated: number, closed: number, total_positions: number}>('/trades/sync_positions/')

// Auto Trading Settings
export interface AutoTradingSettings {
  id?: number
  strategy: number
  strategy_name?: string
  is_enabled: boolean
  symbol: string
  volume: number
  max_open_trades: number
  check_interval_minutes: number
  use_stop_loss: boolean
  use_take_profit: boolean
  stop_loss_pips: number
  take_profit_pips: number
  risk_per_trade_percent: number
  last_check_time?: string
  created_at?: string
  updated_at?: string
}

export const getAutoTradingSettings = (strategyId?: number) => 
  client.get<AutoTradingSettings[]>('/auto-trading-settings/', { 
    params: strategyId ? { strategy: strategyId } : {} 
  })

export const getAutoTradingSetting = (id: number) => 
  client.get<AutoTradingSettings>(`/auto-trading-settings/${id}/`)

export const createOrUpdateAutoTradingSettings = (data: {
  strategy_id: number
  is_enabled?: boolean
  symbol?: string
  volume?: number
  max_open_trades?: number
  check_interval_minutes?: number
  use_stop_loss?: boolean
  use_take_profit?: boolean
  stop_loss_pips?: number
  take_profit_pips?: number
  risk_per_trade_percent?: number
}) => client.post<{status: string, message: string, settings: AutoTradingSettings}>('/auto-trading-settings/create_or_update_for_strategy/', data)

export const toggleAutoTrading = (id: number) => 
  client.post<{status: string, is_enabled: boolean, message: string}>(`/auto-trading-settings/${id}/toggle_enabled/`)

export const testAutoTradeSignal = (strategyId: number, symbol?: string) => 
  client.post<{status: string, signal: {signal: string, confidence: number, reason: string}}>('/auto-trading-settings/test_auto_trade/', {
    strategy_id: strategyId,
    symbol: symbol || 'XAUUSD'
  })

export const triggerAutoTrading = () => 
  client.post<{status: string, message: string, result: any}>('/auto-trading-settings/trigger_auto_trading/')

// Strategy Questions
export interface StrategyQuestion {
  id: number
  strategy: number
  question_text: string
  question_type: 'text' | 'number' | 'choice' | 'multiple_choice' | 'boolean'
  options?: string[]
  answer?: string | null
  status: 'pending' | 'answered' | 'skipped'
  order: number
  created_at: string
  answered_at?: string | null
  context?: {
    section?: 'entry' | 'exit' | 'risk' | 'indicator'
    related_text?: string
  }
}

export const getStrategyQuestions = (strategyId?: number) => 
  client.get<StrategyQuestion[]>('/strategy-questions/', {
    params: strategyId ? { strategy: strategyId } : {}
  })

export const updateQuestionAnswer = (id: number, answer: string, status: 'answered' | 'skipped' = 'answered') =>
  client.patch<StrategyQuestion>(`/strategy-questions/${id}/`, { answer, status })

// Strategy Optimization
export interface StrategyOptimization {
  id: number
  strategy: number
  strategy_name?: string
  method: 'ml' | 'dl' | 'hybrid' | 'auto'
  optimizer_type: 'ml' | 'dl'
  objective: 'sharpe_ratio' | 'total_return' | 'win_rate' | 'profit_factor' | 'combined'
  status: 'pending' | 'running' | 'completed' | 'failed'
  original_params?: any
  optimized_params?: any
  best_score?: number
  optimization_history?: any[]
  original_score?: number
  improvement_percent?: number
  optimization_settings?: any
  created_at: string
  started_at?: string | null
  completed_at?: string | null
  error_message?: string
}

export interface OptimizationCreateRequest {
  strategy: number
  method?: 'ml' | 'dl' | 'hybrid' | 'auto'
  optimizer_type?: 'ml' | 'dl'
  objective?: 'sharpe_ratio' | 'total_return' | 'win_rate' | 'profit_factor' | 'combined'
  n_trials?: number
  n_episodes?: number
  ml_method?: 'bayesian' | 'random_search' | 'grid_search'
  dl_method?: 'reinforcement_learning' | 'neural_evolution' | 'gan'
  timeframe_days?: number
  symbol?: string
}

export const getStrategyOptimizations = (strategyId?: number) =>
  client.get<StrategyOptimization[]>('/strategy-optimizations/', {
    params: strategyId ? { strategy: strategyId } : {}
  })

export const createStrategyOptimization = (data: OptimizationCreateRequest) =>
  client.post<StrategyOptimization>('/strategy-optimizations/', data)

export const getOptimizationStatus = (id: number) =>
  client.get<{ id: number; status: string; best_score?: number; improvement_percent?: number; progress: number }>(
    `/strategy-optimizations/${id}/status/`
  )

export const updateStrategyOptimization = (id: number, data: Partial<OptimizationCreateRequest>) =>
  client.patch<StrategyOptimization>(`/strategy-optimizations/${id}/`, data)

export const deleteStrategyOptimization = (id: number) =>
  client.delete(`/strategy-optimizations/${id}/`)

export const cancelStrategyOptimization = (id: number) =>
  client.post<{ status: string; message: string; optimization: StrategyOptimization }>(
    `/strategy-optimizations/${id}/cancel/`
  )

// AI Recommendations
export interface AIRecommendation {
  id: number
  strategy: number
  strategy_name?: string
  recommendation_type: 'entry_condition' | 'exit_condition' | 'risk_management' | 'indicator' | 'parameter' | 'general'
  title: string
  description: string
  recommendation_data?: any
  price: number
  status: 'generated' | 'purchased' | 'applied'
  purchased_by?: number
  purchased_at?: string | null
  applied_to_strategy?: boolean
  applied_at?: string | null
  created_at: string
  is_purchased?: boolean
}

export const getAIRecommendations = (strategyId: number) =>
  client.get<AIRecommendation[]>('/ai-recommendations/', {
    params: { strategy: strategyId }
  })

export const generateAIRecommendations = (strategyId: number) =>
  client.post<{ status: string; count: number; recommendations: AIRecommendation[] }>(
    `/ai-recommendations/${strategyId}/generate/`
  )

export const purchaseRecommendation = (recommendationId: number) =>
  client.post<{
    status: string
    message?: string
    payment_url?: string
    transaction_id?: number
    remaining_balance?: number
    error?: string
  }>(`/ai-recommendations/${recommendationId}/purchase/`)

// Wallet
export const getWalletBalance = () =>
  client.get<{ balance: number; balance_formatted: string }>('/wallets/balance/')

export const chargeWallet = (amount: number) =>
  client.post<{
    status: string
    payment_url: string
    message: string
    transaction_id: number
    error?: string
  }>('/wallets/charge/', { amount })

export default client

