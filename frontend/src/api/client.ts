import axios, { AxiosResponse } from 'axios'
import { navigateTo } from '../utils/navigation'

// Auto-detect API URL based on current hostname
// This allows access from local network IPs
function getApiBaseUrl(): string {
  // Check for environment variable first (for production builds with custom backend)
  const envBackendUrl = import.meta.env.VITE_BACKEND_URL
  if (envBackendUrl) {
    // Ensure it ends with /api
    return envBackendUrl.endsWith('/api') ? envBackendUrl : `${envBackendUrl}/api`
  }
  
  // In both development and production, use relative URL
  // This works with:
  // - Vite dev server proxy (development)
  // - Nginx reverse proxy (production with Docker)
  // The proxy will forward requests to backend
  return '/api'
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

// Client with longer timeout for GapGPT operations (can take 30-60 seconds)
const gapGPTClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 120000, // 120 seconds (2 minutes) timeout for GapGPT API calls
})

// Add request interceptor to gapGPTClient for CSRF token
gapGPTClient.interceptors.request.use(
  (config) => {
    const csrfToken = getCsrfToken()
    if (csrfToken) {
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

// Add response interceptor to gapGPTClient (same as client)
gapGPTClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log network errors for debugging
    if (!error.response) {
      console.error('GapGPT Network error:', {
        message: error.message,
        code: error.code,
        url: error.config?.url,
      })
    }
    return Promise.reject(error)
  }
)

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
  user?: number | null
  owner_username?: string | null
  is_owner?: boolean
}

export interface GoldAPIAccessInfo {
  provider: string
  api_key: string
  source?: string | null
  assigned_by_admin: boolean
  allow_mt5_access?: boolean
  is_active: boolean
  assigned_at?: string | null
  updated_at?: string | null
  notes?: string
  has_credentials: boolean
}

export interface GoldAPIAccessRequest {
  id: number
  status: string
  status_display: string
  preferred_provider: string
  user_notes: string
  admin_notes: string
  price_amount: number
  transaction_id: number | null
  payment_confirmed_at: string | null
  assigned_provider: string
  assigned_api_key: string
  assigned_at: string | null
  assigned_by: number | null
  assigned_by_username: string | null
  created_at: string
  updated_at: string
  user_id?: number
  username?: string
  user_email?: string
  user_phone?: string
  user_has_gold_access?: boolean
  user_allow_mt5_access?: boolean
}

export interface TradingStrategy {
  id: number
  name: string
  description: string
  strategy_file: string
  is_active: boolean
  is_primary: boolean
  uploaded_at: string
  parsed_strategy_data?: any
  processing_status?: 'not_processed' | 'processing' | 'processed' | 'failed'
  processed_at?: string | null
  processing_error?: string
  marketplace_listing_id?: number | null
  marketplace_listing_status?: 'published' | 'draft' | null
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
  origin?: 'direct' | 'marketplace_trial' | 'marketplace_active'
  marketplace_access?: StrategyListingAccess | null
}

export interface Result {
  id: number
  job: number
  strategy_name?: string | null
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
  data_sources?: {
    provider?: string
    symbol?: string
    start_date?: string
    end_date?: string
    data_points?: number
    timeframe_days?: number
    strategy_timeframe?: string
    normalized_timeframe?: string
    execution_details?: {
      backtest_duration_seconds?: number
      total_duration_seconds?: number
      initial_capital?: number
      data_retrieval_method?: string
    }
    strategy_details?: {
      entry_conditions_count?: number
      exit_conditions_count?: number
      indicators_used?: string[]
      selected_indicators?: string[]
      confidence_score?: number
    }
    results_summary?: {
      total_trades?: number
      winning_trades?: number
      losing_trades?: number
      win_rate?: number
      total_return?: number
      max_drawdown?: number
      sharpe_ratio?: number
      profit_factor?: number
    }
  }
  created_at: string
}

export interface StrategyListingAccess {
  id: number
  listing_id: number
  listing_title: string
  user_id: number
  username: string
  owner_display_name: string
  status: 'trial' | 'active' | 'expired' | 'cancelled'
  status_display: string
  trial_started_at: string | null
  trial_expires_at: string | null
  activated_at: string | null
  expires_at: string | null
  total_backtests_run: number
  last_backtest_at: string | null
  is_trial_active: boolean
  has_active_access: boolean
  remaining_trial_seconds: number
  remaining_active_seconds: number
  owner_username: string
  trial_backtest_limit: number
  price: string
  last_price: string
  platform_fee_percent: string
  platform_fee_amount: string
  owner_amount: string
}

export interface StrategyMarketplaceListing {
  id: number
  strategy_id: number
  strategy_name: string
  owner_id: number
  owner_username: string
  owner_display_name: string
  title: string
  headline: string
  description: string
  shared_text: string
  price: string
  billing_cycle_days: number
  trial_days: number
  trial_backtest_limit: number
  performance_snapshot: Record<string, any>
  sample_results: any[]
  supported_symbols: string[]
  tags: string[]
  is_published: boolean
  published_at: string | null
  created_at: string
  updated_at: string
  current_user_access?: StrategyListingAccess | null
  is_owner: boolean
  can_start_trial: boolean
  can_purchase: boolean
  source_result_id?: number | null
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
export const processStrategy = (id: number) => client.post(`/strategies/${id}/process/`, {}, {
  timeout: 60000, // 60 seconds timeout for strategy processing (can take longer due to AI analysis)
})
export const getStrategyProgress = (id: number) => client.get(`/strategies/${id}/progress/`)
export const generateStrategyQuestions = (id: number) => client.post(`/strategies/${id}/generate_questions/`)
export const processStrategyWithAnswers = (id: number) => client.post(`/strategies/${id}/process_with_answers/`)
export const setPrimaryStrategy = (id: number) => client.post(`/strategies/${id}/set-primary/`)
export const downloadStrategy = (id: number) => client.get(`/strategies/${id}/download/`, {
  responseType: 'blob',
})
export const getStrategyFileContent = (id: number) => 
  client.get<{status: string, content: string, file_name: string, file_size: number}>(`/strategies/${id}/file-content/`)
export const saveGapGPTConversion = (id: number, data: { converted_strategy: any, model_used?: string, tokens_used?: number }) => 
  client.post(`/strategies/${id}/save-gapgpt-conversion/`, data)

// Jobs
export const getJobs = () => client.get('/jobs/')
export const createJob = (data: { strategy: number, job_type: string, timeframe_days?: number, symbol?: string, initial_capital?: number, selected_indicators?: string[], ai_provider?: string }) => 
  client.post(
    '/jobs/',
    data,
    data.job_type === 'backtest'
      ? {
          timeout: 60000, // 60 seconds - job creation should be fast (async execution), but allow more time for sync fallback
        }
      : undefined
  )
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

// MT5 Symbols
export interface MT5Symbol {
  name: string
  is_available: boolean
  description?: string
  currency_base?: string
  currency_profit?: string
  currency_margin?: string
}

export const getMT5Symbols = (onlyAvailable: boolean = true) => 
  client.get<{
    status: string
    symbols: MT5Symbol[]
    total_count: number
    available_count: number
  }>('/market/mt5_candles/', {
    params: {
      source: 'mt5_symbols',
      only_available: onlyAvailable ? 'true' : 'false'
    }
  })
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

// System Settings
export interface SystemSettingsResponse {
  live_trading_enabled: boolean
  use_ai_cache: boolean
  google_auth_enabled?: boolean
  token_cost_per_1000?: number
  backtest_cost?: number
  strategy_processing_cost?: number
  registration_bonus?: number
}

export const getSystemSettings = () =>
  client.get<SystemSettingsResponse>('/system-settings/')

export const updateSystemSettings = (payload: Partial<SystemSettingsResponse>) =>
  client.patch<SystemSettingsResponse>('/system-settings/', payload)

export const clearAICache = () =>
  client.post<{ status: string; message: string; deleted_count: number }>('/admin/clear-ai-cache/')

// Security Management (Admin Only)
export interface BlockedIP {
  ip: string
  blocked_until: string
  remaining_seconds: number
  remaining_minutes: number
}

export interface RateLimitStat {
  ip: string
  requests_count: number
  last_request: string
  first_request: string
}

export interface SecurityManagementData {
  success: boolean
  blocked_ips: BlockedIP[]
  rate_limit_stats: Record<string, RateLimitStat>
  rate_limit_config: {
    limits: Record<string, [number, number]>
    protected_paths: string[]
  }
  total_blocked: number
  total_tracked_ips: number
}

export const getSecurityManagement = () =>
  client.get<SecurityManagementData>('/admin/security/')

export const unblockIP = (ip: string) =>
  client.post<{ success: boolean; message: string }>('/admin/security/', {
    action: 'unblock_ip',
    ip,
  })

export const clearRateLimitHistory = (ip?: string) =>
  client.post<{ success: boolean; message: string }>('/admin/security/', {
    action: 'clear_rate_limit_history',
    ip,
  })

export const unblockAllIPs = () =>
  client.post<{ success: boolean; message: string }>('/admin/security/', {
    action: 'unblock_all',
  })

export interface SecurityLog {
  timestamp: string
  level: string
  message: string
  ip?: string
  path?: string
}

export const getSecurityLogs = () =>
  client.get<{ success: boolean; logs: SecurityLog[]; note?: string }>('/admin/security-logs/')

// User Management (Admin Only)
export interface AdminUser {
  id: number
  username: string
  email: string
  phone_number: string | null
  first_name?: string
  last_name?: string
  nickname?: string
  balance: number
  balance_formatted: string
  date_joined: string
  is_staff: boolean
  is_superuser: boolean
}

export interface AdminUsersResponse {
  users: AdminUser[]
  total: number
}

export const getAdminUsers = () =>
  client.get<AdminUsersResponse>('/admin/users/')

export const allocateUserCredit = (user_id: number, amount: number, description?: string) =>
  client.post<{
    success: boolean
    message: string
    new_balance: number
    new_balance_formatted: string
  }>('/admin/users/', { user_id, amount, description })

export const updateUser = (user_id: number, data: {
  email?: string
  first_name?: string
  last_name?: string
  phone_number?: string
  nickname?: string
  is_staff?: boolean
  is_superuser?: boolean
}) =>
  client.patch<{
    success: boolean
    message: string
    user: AdminUser
  }>('/admin/users/', { user_id, ...data })

export const deleteUser = (user_id: number) =>
  client.delete<{
    success: boolean
    message: string
  }>('/admin/users/', { 
    data: { user_id },
    params: { user_id: user_id.toString() }
  })

// Gold API Access
export const getUserGoldAPIAccess = () =>
  client.get<GoldAPIAccessInfo>('/gold-access/self/')

export const updateUserGoldAPIAccess = (data: Partial<Pick<GoldAPIAccessInfo, 'provider' | 'api_key' | 'notes'>>) =>
  client.put<GoldAPIAccessInfo>('/gold-access/self/', data)

export const createGoldAPIAccessRequest = (data: { preferred_provider?: string; user_notes?: string }) =>
  client.post<GoldAPIAccessRequest & { payment_url?: string }>('/gold-access/requests/', data)

export const listGoldAPIAccessRequests = (params?: Record<string, any>) =>
  client.get<GoldAPIAccessRequest[] | { results: GoldAPIAccessRequest[] }>('/gold-access/requests/', { params })

export const cancelGoldAPIAccessRequest = (id: number) =>
  client.post<{ detail: string }>(`/gold-access/requests/${id}/cancel/`)

export const assignGoldAPIAccessRequest = (
  id: number,
  data: { provider: string; api_key: string; admin_notes?: string; is_active?: boolean; allow_mt5_access?: boolean }
) => client.post<GoldAPIAccessRequest>(`/gold-access/requests/${id}/assign/`, data)

// User Activity Logs
export interface UserActivityLog {
  id: number
  action_type: string
  action_type_display: string
  action_description: string
  metadata: Record<string, any>
  created_at: string
}

export interface UserActivityLogsResponse {
  success: boolean
  logs: UserActivityLog[]
  total_count: number
  limit: number
  offset: number
}

// Export a simple get function for general API calls
export const get = (url: string, config?: any) => client.get(url, config)

export async function getUserActivityLogs(limit: number = 50, offset: number = 0): Promise<AxiosResponse<UserActivityLogsResponse>> {
  return client.get('/auth/activity-logs/', {
    params: { limit, offset }
  })
}

export default client

// ==================== GapGPT API Functions ====================

export interface GapGPTModel {
  id: string
  name: string
  description: string
  owned_by: string
  endpoint_types: string[]
}

export interface GapGPTConvertRequest {
  strategy_text: string
  model_id?: string
  temperature?: number
  max_tokens?: number
}

export interface GapGPTConvertResponse {
  status: 'success' | 'error'
  data?: {
    success: boolean
    converted_strategy: any
    model_used: string
    tokens_used: number
    latency_ms: number
    raw_response?: string
    error?: string
  }
  message?: string
}

export interface GapGPTCompareResponse {
  status: 'success' | 'error'
  data?: {
    all_results: Record<string, any>
    best_result: {
      model_id: string
      result: any
      score: number
    }
    models_tested: string[]
    summary: {
      total_models: number
      successful_models: number
      failed_models: number
      best_model_id: string | null
      best_score: number
    }
  }
  message?: string
}

export const getGapGPTModels = () => 
  gapGPTClient.get<{status: string, models: GapGPTModel[], count: number}>('/gapgpt/models/')

export const convertStrategyWithGapGPT = (data: GapGPTConvertRequest) => 
  gapGPTClient.post<GapGPTConvertResponse>('/gapgpt/convert/', data)

export const compareModelsWithGapGPT = (data: { strategy_text: string, models?: string[], temperature?: number, max_tokens?: number }) => 
  gapGPTClient.post<GapGPTCompareResponse>('/gapgpt/compare-models/', data)

