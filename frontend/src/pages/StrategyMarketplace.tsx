import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  StrategyMarketplaceListing,
  StrategyListingAccess,
  TradingStrategy,
  createJob,
  getStrategies,
} from '../api/client'
import {
  createMarketplaceListing,
  deleteMarketplaceListing,
  getMarketplaceListings,
  getMarketplaceListing,
  getMarketplaceListingAccesses,
  getMyMarketplaceAccesses,
  getMyMarketplaceListings,
  getStrategyMarketplaceSummary,
  publishMarketplaceListing,
  purchaseMarketplaceListing,
  startMarketplaceTrial,
  unpublishMarketplaceListing,
  updateMarketplaceListing,
  StrategySummaryResponse,
} from '../api/marketplace'
import { useToast } from '../components/ToastProvider'
import { AxiosError } from 'axios'

type MarketplaceTab = 'explore' | 'myListings' | 'myAccess' | 'create'

interface ListingFormState {
  strategy: string
  title: string
  headline: string
  description: string
  sharedText: string
  price: string
  billingCycleDays: string
  trialDays: string
  trialBacktestLimit: string
  supportedSymbolsText: string
  tagsText: string
}

const emptyForm: ListingFormState = {
  strategy: '',
  title: '',
  headline: '',
  description: '',
  sharedText: '',
  price: '',
  billingCycleDays: '30',
  trialDays: '9',
  trialBacktestLimit: '3',
  supportedSymbolsText: '',
  tagsText: '',
}

function splitCommaSeparated(input: string): string[] {
  return input
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function formatRemaining(seconds: number): string {
  if (!seconds || seconds <= 0) {
    return 'انقضا شده'
  }
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (days > 0) {
    return `${days} روز و ${hours} ساعت`
  }
  if (hours > 0) {
    return `${hours} ساعت و ${minutes} دقیقه`
  }
  return `${minutes} دقیقه`
}

function formatPrice(price: string | number): string {
  const numeric = Number(price || 0)
  if (Number.isNaN(numeric)) {
    return `${price}`
  }
  return `${new Intl.NumberFormat('fa-IR').format(Math.round(numeric))} تومان`
}

function buildPayload(form: ListingFormState, includeStrategy: boolean) {
  const payload: any = {
    title: form.title.trim(),
    headline: form.headline.trim(),
    description: form.description.trim(),
    shared_text: form.sharedText.trim(),
    price: Number(form.price || 0),
    billing_cycle_days: Number(form.billingCycleDays || 30),
    trial_days: Number(form.trialDays || 9),
    trial_backtest_limit: Number(form.trialBacktestLimit || 3),
  }

  const supportedSymbols = splitCommaSeparated(form.supportedSymbolsText)
  const tags = splitCommaSeparated(form.tagsText)
  if (supportedSymbols.length > 0) {
    payload.supported_symbols = supportedSymbols
  }
  if (tags.length > 0) {
    payload.tags = tags
  }

  if (includeStrategy) {
    payload.strategy = Number(form.strategy)
  }

  return payload
}

const StrategyMarketplace = () => {
  const { showToast } = useToast()
  const [activeTab, setActiveTab] = useState<MarketplaceTab>('explore')
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({})
  const [listings, setListings] = useState<StrategyMarketplaceListing[]>([])
  const [myListings, setMyListings] = useState<StrategyMarketplaceListing[]>([])
  const [myAccesses, setMyAccesses] = useState<StrategyListingAccess[]>([])
  const [strategies, setStrategies] = useState<TradingStrategy[]>([])
  const [formState, setFormState] = useState<ListingFormState>(emptyForm)
  const [editingListing, setEditingListing] = useState<StrategyMarketplaceListing | null>(null)
  const [editForm, setEditForm] = useState<ListingFormState | null>(null)
  const [accessesMap, setAccessesMap] = useState<Record<number, StrategyListingAccess[]>>({})
  const [strategySummary, setStrategySummary] = useState<StrategySummaryResponse | null>(null)
  const [summaryLoading, setSummaryLoading] = useState<boolean>(false)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  const toggleActionLoading = (key: string, value: boolean) => {
    setActionLoading((prev) => ({ ...prev, [key]: value }))
  }

  const extractErrorMessage = (error: any): string => {
    if (!error) return 'خطای ناشناخته'
    const axiosError = error as AxiosError<any>
    const data = axiosError.response?.data
    if (typeof data === 'string') {
      return data
    }
    if (data?.error) return data.error
    if (data?.message) return data.message
    if (data?.detail) return data.detail
    if (Array.isArray(data) && data.length > 0) return data[0]
    return axiosError.message || 'خطای ناشناخته'
  }

  const metricLabels: Record<string, string> = {
    total_return_percent: 'بازده کل (%)',
    win_rate_percent: 'نرخ برد (%)',
    max_drawdown_percent: 'بزرگ‌ترین افت سرمایه (%)',
    total_trades: 'تعداد معاملات',
    winning_trades: 'تعداد معاملات موفق',
    losing_trades: 'تعداد معاملات ناموفق',
    generated_at: 'تاریخ ثبت نتیجه',
    job_id: 'شناسه بک‌تست',
  }

  const renderPerformanceSnapshotView = (snapshot?: Record<string, any>) => {
    if (!snapshot || Object.keys(snapshot).length === 0) {
      return <p className="text-sm text-gray-500">اطلاعات بک‌تست یافت نشد.</p>
    }
    const entries = Object.entries(snapshot).filter(([key]) => key !== 'equity_curve_preview')
    const formatValue = (key: string, value: any) => {
      if (value === null || value === undefined || value === '') {
        return '-'
      }
      if (key === 'generated_at') {
        try {
          return new Date(value).toLocaleString('fa-IR')
        } catch (e) {
          return String(value)
        }
      }
      if (typeof value === 'number') {
        const absValue = Math.abs(value)
        const formatted = absValue >= 1000 ? value.toLocaleString('fa-IR', { maximumFractionDigits: 2 }) : value.toFixed(2)
        return formatted
      }
      return String(value)
    }

    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
        {entries.map(([key, value]) => (
          <div key={key} className="flex justify-between gap-4 bg-gray-900/40 rounded-md px-3 py-2 border border-gray-800">
            <span className="text-gray-400">{metricLabels[key] || key}</span>
            <span className="text-gray-200 text-left">{formatValue(key, value)}</span>
          </div>
        ))}
      </div>
    )
  }

  const renderSampleTradesView = (trades?: any[]) => {
    if (!trades || trades.length === 0) {
      return <p className="text-sm text-gray-500">نمونه‌ای از معاملات ثبت نشده است.</p>
    }

    const limitedTrades = trades.slice(0, 5)

    const formatNumber = (value: any) => {
      if (typeof value !== 'number') {
        const parsed = Number(value)
        if (!Number.isNaN(parsed)) {
          value = parsed
        }
      }
      if (typeof value === 'number' && !Number.isNaN(value)) {
        return value.toFixed(2)
      }
      return value ?? '-'
    }

    return (
      <div className="mt-4">
        <h4 className="text-sm font-semibold text-blue-300 mb-2">نمونه معاملات</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full text-xs text-right text-gray-300 border border-gray-800">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="px-3 py-2">ورود</th>
                <th className="px-3 py-2">خروج</th>
                <th className="px-3 py-2">سود/زیان (%)</th>
                <th className="px-3 py-2">مدت (روز)</th>
              </tr>
            </thead>
            <tbody>
              {limitedTrades.map((trade, index) => (
                <tr key={index} className="border-t border-gray-800">
                  <td className="px-3 py-2">{trade.entry_date || '-'}</td>
                  <td className="px-3 py-2">{trade.exit_date || '-'}</td>
                  <td className="px-3 py-2 text-left">{formatNumber(trade.pnl_percent)}</td>
                  <td className="px-3 py-2 text-left">{formatNumber(trade.duration_days)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {trades.length > limitedTrades.length && (
          <p className="text-xs text-gray-500 mt-2">نمایش {limitedTrades.length} مورد از {trades.length} معامله ثبت شده</p>
        )}
      </div>
    )
  }

  const normalizeStrategies = (data: any): TradingStrategy[] => {
    if (!data) return []
    if (Array.isArray(data)) return data
    if (data.results && Array.isArray(data.results)) return data.results
    return []
  }

  const normalizeListings = (data: any): StrategyMarketplaceListing[] => {
    if (!data) return []
    if (Array.isArray(data)) return data
    if (data.results && Array.isArray(data.results)) return data.results
    return []
  }

  const normalizeAccesses = (data: any): StrategyListingAccess[] => {
    if (!data) return []
    if (Array.isArray(data)) return data
    if (data.results && Array.isArray(data.results)) return data.results
    return []
  }

  const loadStrategySummary = useCallback(async (strategyId: number) => {
    try {
      setSummaryLoading(true)
      setSummaryError(null)
      const response = await getStrategyMarketplaceSummary(strategyId)
      setStrategySummary(response.data)
    } catch (error) {
      console.error('Error loading strategy summary:', error)
      const message = extractErrorMessage(error)
      setStrategySummary(null)
      setSummaryError(message)
    } finally {
      setSummaryLoading(false)
    }
  }, [])

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true)
      const [listingsRes, myListingsRes, myAccessRes, strategiesRes] = await Promise.all([
        getMarketplaceListings(),
        getMyMarketplaceListings(),
        getMyMarketplaceAccesses(),
        getStrategies(),
      ])

      setListings(normalizeListings(listingsRes.data))
      setMyListings(normalizeListings(myListingsRes.data))
      setMyAccesses(normalizeAccesses(myAccessRes.data))
      setStrategies(normalizeStrategies(strategiesRes.data))
    } catch (error) {
      console.error('Error loading marketplace data:', error)
      showToast('خطا در بارگذاری اطلاعات مارکت‌پلیس', { type: 'error' })
    } finally {
      setIsLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    if (!formState.strategy) {
      setStrategySummary(null)
      setSummaryError(null)
      return
    }

    const strategyId = Number(formState.strategy)
    if (Number.isNaN(strategyId)) {
      setStrategySummary(null)
      setSummaryError('شناسه استراتژی نامعتبر است')
      return
    }

    loadStrategySummary(strategyId)
  }, [formState.strategy, loadStrategySummary])

  const availableStrategies = useMemo(() => {
    return strategies.filter((strategy) => !strategy.marketplace_listing_id)
  }, [strategies])

  const handleFormChange = (field: keyof ListingFormState, value: string) => {
    if (field === 'strategy') {
      setStrategySummary(null)
      setSummaryError(null)
    }
    setFormState((prev) => ({ ...prev, [field]: value }))
  }

  const handleCreateListing = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!formState.strategy) {
      showToast('لطفاً یک استراتژی را انتخاب کنید', { type: 'warning' })
      return
    }
    if (!formState.title.trim()) {
      showToast('عنوان نمی‌تواند خالی باشد', { type: 'warning' })
      return
    }

    if (summaryLoading) {
      showToast('لطفاً تا تکمیل بارگذاری نتایج بک‌تست صبر کنید', { type: 'warning' })
      return
    }

    if (!strategySummary || !strategySummary.has_result) {
      showToast(strategySummary?.message || 'برای این استراتژی بک‌تست معتبری یافت نشد. ابتدا بک‌تست انجام دهید.', { type: 'error' })
      return
    }

    const payload = buildPayload(formState, true)

    try {
      toggleActionLoading('create', true)
      await createMarketplaceListing(payload)
      showToast('استراتژی با موفقیت به مارکت‌پلیس اضافه شد', { type: 'success' })
      setFormState(emptyForm)
      setStrategySummary(null)
      setSummaryError(null)
      loadData()
    } catch (error) {
      console.error('Error creating marketplace listing:', error)
      showToast(extractErrorMessage(error), { type: 'error' })
    } finally {
      toggleActionLoading('create', false)
    }
  }

  const handleStartTrial = async (listingId: number) => {
    const key = `startTrial-${listingId}`
    try {
      toggleActionLoading(key, true)
      await startMarketplaceTrial(listingId)
      showToast('دوره آزمایشی فعال شد', { type: 'success' })
      await loadData()
    } catch (error) {
      console.error('Error starting trial:', error)
      showToast(extractErrorMessage(error), { type: 'error' })
    } finally {
      toggleActionLoading(key, false)
    }
  }

  const handlePurchase = async (listingId: number) => {
    const key = `purchase-${listingId}`
    try {
      toggleActionLoading(key, true)
      await purchaseMarketplaceListing(listingId)
      showToast('اشتراک استراتژی با موفقیت فعال شد', { type: 'success' })
      await loadData()
    } catch (error) {
      console.error('Error purchasing listing:', error)
      showToast(extractErrorMessage(error), { type: 'error' })
    } finally {
      toggleActionLoading(key, false)
    }
  }

  const handleRunBacktest = async (listing: StrategyMarketplaceListing) => {
    const key = `backtest-${listing.id}`
    try {
      toggleActionLoading(key, true)
      await createJob({ strategy: listing.strategy_id, job_type: 'backtest', timeframe_days: 365 })
      showToast('بک‌تست با موفقیت آغاز شد. لطفاً نتایج را در بخش نتایج بررسی کنید.', { type: 'success' })
    } catch (error) {
      console.error('Error running backtest:', error)
      showToast(extractErrorMessage(error), { type: 'error' })
    } finally {
      toggleActionLoading(key, false)
    }
  }

  const handlePublishToggle = async (listing: StrategyMarketplaceListing) => {
    const key = `publish-${listing.id}`
    try {
      toggleActionLoading(key, true)
      if (listing.is_published) {
        await unpublishMarketplaceListing(listing.id)
        showToast('استراتژی از مارکت‌پلیس خارج شد', { type: 'info' })
      } else {
        await publishMarketplaceListing(listing.id)
        showToast('استراتژی منتشر شد', { type: 'success' })
      }
      await loadData()
    } catch (error) {
      console.error('Error toggling publish state:', error)
      showToast(extractErrorMessage(error), { type: 'error' })
    } finally {
      toggleActionLoading(key, false)
    }
  }

  const handleDeleteListing = async (listingId: number) => {
    const confirmDelete = window.confirm('آیا از حذف این استراتژی از مارکت‌پلیس مطمئن هستید؟')
    if (!confirmDelete) return
    const key = `delete-${listingId}`
    try {
      toggleActionLoading(key, true)
      await deleteMarketplaceListing(listingId)
      showToast('استراتژی حذف شد', { type: 'success' })
      await loadData()
    } catch (error) {
      console.error('Error deleting listing:', error)
      showToast(extractErrorMessage(error), { type: 'error' })
    } finally {
      toggleActionLoading(key, false)
    }
  }

  const openEditModal = async (listingId: number) => {
    const key = `edit-${listingId}`
    try {
      toggleActionLoading(key, true)
      const response = await getMarketplaceListing(listingId)
      const listing = response.data
      setEditingListing(listing)
      setEditForm({
        strategy: listing.strategy_id.toString(),
        title: listing.title || '',
        headline: listing.headline || '',
        description: listing.description || '',
        sharedText: listing.shared_text || '',
        price: listing.price?.toString() || '',
        billingCycleDays: listing.billing_cycle_days?.toString() || '30',
        trialDays: listing.trial_days?.toString() || '9',
        trialBacktestLimit: listing.trial_backtest_limit?.toString() || '3',
        supportedSymbolsText: (listing.supported_symbols || []).join(', '),
        tagsText: (listing.tags || []).join(', '),
      })
    } catch (error) {
      console.error('Error loading listing for edit:', error)
      showToast('خطا در بارگذاری اطلاعات استراتژی', { type: 'error' })
    } finally {
      toggleActionLoading(key, false)
    }
  }

  const handleEditFormChange = (field: keyof ListingFormState, value: string) => {
    setEditForm((prev) => (prev ? { ...prev, [field]: value } : prev))
  }

  const submitEdit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!editingListing || !editForm) return
    if (!editForm.title.trim()) {
      showToast('عنوان نمی‌تواند خالی باشد', { type: 'warning' })
      return
    }

    const payload = buildPayload(editForm, false)

    const key = `submitEdit-${editingListing.id}`
    try {
      toggleActionLoading(key, true)
      await updateMarketplaceListing(editingListing.id, payload)
      showToast('اطلاعات استراتژی به‌روزرسانی شد', { type: 'success' })
      setEditingListing(null)
      setEditForm(null)
      await loadData()
    } catch (error) {
      console.error('Error updating listing:', error)
      showToast(extractErrorMessage(error), { type: 'error' })
    } finally {
      toggleActionLoading(key, false)
    }
  }

  const closeEditModal = () => {
    setEditingListing(null)
    setEditForm(null)
  }

  const loadListingAccesses = async (listingId: number) => {
    const key = `accesses-${listingId}`
    try {
      toggleActionLoading(key, true)
      const response = await getMarketplaceListingAccesses(listingId)
      setAccessesMap((prev) => ({ ...prev, [listingId]: response.data.results || [] }))
    } catch (error) {
      console.error('Error loading listing accesses:', error)
      showToast('خطا در بارگذاری کاربران این استراتژی', { type: 'error' })
    } finally {
      toggleActionLoading(key, false)
    }
  }

  const renderAccessStatus = (access?: StrategyListingAccess | null) => {
    if (!access) return <span className="text-gray-400">دسترسی فعال ندارید</span>
    const remaining = access.is_trial_active
      ? formatRemaining(access.remaining_trial_seconds)
      : formatRemaining(access.remaining_active_seconds)
    return (
      <div className="space-y-1 text-sm">
        <div>وضعیت: {access.status_display}</div>
        {access.is_trial_active ? (
          <div>باقی‌مانده دوره آزمایشی: {remaining}</div>
        ) : access.has_active_access ? (
          <div>باقی‌مانده اشتراک: {remaining}</div>
        ) : (
          <div>دسترسی منقضی شده</div>
        )}
        <div>تعداد بک‌تست‌های اجرا شده: {access.total_backtests_run}</div>
      </div>
    )
  }

  const renderMarketplaceCard = (listing: StrategyMarketplaceListing) => {
    const actionKey = (suffix: string) => `${suffix}-${listing.id}`
    return (
      <div key={listing.id} className="bg-gray-800 rounded-xl p-6 shadow border border-gray-700" style={{ direction: 'rtl', textAlign: 'right' }}>
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-lg font-semibold text-white">{listing.title}</h3>
              <p className="text-sm text-blue-300">مالک: {listing.owner_username}</p>
            </div>
            <div className="text-right">
              <div className="text-xl font-bold text-green-400">{formatPrice(listing.price)}</div>
              <div className="text-xs text-gray-400">دوره اشتراک: {listing.billing_cycle_days} روز</div>
            </div>
          </div>
          {listing.headline && <p className="text-sm text-gray-300">{listing.headline}</p>}
          {listing.description && <p className="text-sm text-gray-400 whitespace-pre-line">{listing.description}</p>}

          {listing.performance_snapshot && Object.keys(listing.performance_snapshot).length > 0 && (
            <div className="bg-gray-900 rounded-lg p-4 text-sm text-gray-200">
              <div className="font-semibold mb-2 text-blue-300">خلاصه عملکرد</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {Object.entries(listing.performance_snapshot).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-400">{key}</span>
                    <span className="text-gray-100">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {listing.supported_symbols && listing.supported_symbols.length > 0 && (
            <div className="text-xs text-gray-400">
              نمادهای پیشنهادی: {listing.supported_symbols.join('، ')}
            </div>
          )}
          {listing.tags && listing.tags.length > 0 && (
            <div className="text-xs text-gray-500">
              برچسب‌ها: {listing.tags.map((tag) => `#${tag}`).join(' ')}
            </div>
          )}

          <div className="mt-4 border-t border-gray-700 pt-4">
            {renderAccessStatus(listing.current_user_access || null)}
          </div>

          <div className="flex flex-wrap gap-2 mt-4">
            {listing.current_user_access?.has_active_access && (
              <button
                disabled={actionLoading[actionKey('backtest')]}
                onClick={() => handleRunBacktest(listing)}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition disabled:opacity-50"
              >
                {actionLoading[actionKey('backtest')] ? 'در حال اجرا...' : 'اجرای بک‌تست'}
              </button>
            )}
            {!listing.current_user_access?.has_active_access && listing.can_start_trial && (
              <button
                disabled={actionLoading[actionKey('startTrial')]}
                onClick={() => handleStartTrial(listing.id)}
                className="px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 transition disabled:opacity-50"
              >
                {actionLoading[actionKey('startTrial')] ? 'در حال فعال‌سازی...' : `شروع دوره آزمایشی ${listing.trial_days} روزه`}
              </button>
            )}
            {!listing.current_user_access?.has_active_access && listing.can_purchase && (
              <button
                disabled={actionLoading[actionKey('purchase')]}
                onClick={() => handlePurchase(listing.id)}
                className="px-4 py-2 rounded-lg bg-yellow-600 text-white hover:bg-yellow-500 transition disabled:opacity-50"
              >
                {actionLoading[actionKey('purchase')] ? 'در حال ثبت خرید...' : 'خرید اشتراک استراتژی'}
              </button>
            )}
            {!listing.can_start_trial && !listing.can_purchase && !listing.current_user_access?.has_active_access && (
              <span className="text-sm text-gray-500">برای دسترسی دوباره، با مالک استراتژی هماهنگ کنید.</span>
            )}
          </div>
        </div>
      </div>
    )
  }

  const renderMyListingCard = (listing: StrategyMarketplaceListing) => {
    const actionKey = (suffix: string) => `${suffix}-${listing.id}`
    const accesses = accessesMap[listing.id]
    return (
      <div key={listing.id} className="bg-gray-800 rounded-xl p-6 border border-gray-700" style={{ direction: 'rtl', textAlign: 'right' }}>
        <div className="flex flex-col gap-3">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">{listing.title}</h3>
              <div className="text-sm text-gray-300">وضعیت: {listing.is_published ? 'منتشر شده' : 'پیش‌نویس'}</div>
              <div className="text-sm text-gray-400">قیمت: {formatPrice(listing.price)}</div>
            </div>
            <div className="flex flex-col gap-2">
              <button
                onClick={() => handlePublishToggle(listing)}
                disabled={actionLoading[actionKey('publish')]}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  listing.is_published ? 'bg-red-600 hover:bg-red-500' : 'bg-green-600 hover:bg-green-500'
                } text-white disabled:opacity-50`}
              >
                {actionLoading[actionKey('publish')]
                  ? 'در حال بروزرسانی...'
                  : listing.is_published
                    ? 'لغو انتشار'
                    : 'انتشار در مارکت‌پلیس'}
              </button>
              <button
                onClick={() => openEditModal(listing.id)}
                disabled={actionLoading[actionKey('edit')]}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white transition disabled:opacity-50"
              >
                ویرایش
              </button>
              <button
                onClick={() => handleDeleteListing(listing.id)}
                disabled={actionLoading[actionKey('delete')]}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-gray-700 hover:bg-gray-600 text-white transition disabled:opacity-50"
              >
                حذف
              </button>
            </div>
          </div>

          <div className="text-sm text-gray-400">
            استراتژی: {listing.strategy_name} | شناسه: {listing.strategy_id}
          </div>

          <div className="flex flex-wrap gap-2 mt-2">
            <button
              onClick={() => loadListingAccesses(listing.id)}
              disabled={actionLoading[actionKey('accesses')]}
              className="px-4 py-2 rounded-lg text-xs bg-gray-700 hover:bg-gray-600 text-white transition disabled:opacity-50"
            >
              {actionLoading[actionKey('accesses')] ? 'در حال بروزرسانی...' : 'مشاهده کاربران'}
            </button>
          </div>

          {accesses && accesses.length > 0 && (
            <div className="mt-4 bg-gray-900 rounded-lg p-4 text-sm text-gray-200">
              <div className="font-semibold text-blue-300 mb-2">کاربران این استراتژی</div>
              <div className="space-y-2">
                {accesses.map((access) => (
                  <div key={access.id} className="border border-gray-700 rounded-lg p-3">
                    <div className="flex flex-wrap justify-between text-xs text-gray-400">
                      <span>کاربر: {access.username}</span>
                      <span>وضعیت: {access.status_display}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      مجموع بک‌تست: {access.total_backtests_run}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderMyAccessCard = (access: StrategyListingAccess) => {
    const listing = listings.find((item) => item.id === access.listing_id)
    return (
      <div key={access.id} className="bg-gray-800 rounded-xl p-6 border border-gray-700" style={{ direction: 'rtl', textAlign: 'right' }}>
        <div className="flex flex-col gap-3">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-lg font-semibold text-white">{access.listing_title}</h3>
              <div className="text-sm text-gray-400">مالک: {access.owner_username}</div>
            </div>
            {listing && <div className="text-sm text-blue-400">قیمت: {formatPrice(listing.price)}</div>}
          </div>
          <div className="text-sm text-gray-300">وضعیت دسترسی: {access.status_display}</div>
          <div className="text-sm text-gray-400">
            {access.is_trial_active
              ? `باقی‌مانده دوره آزمایشی: ${formatRemaining(access.remaining_trial_seconds)}`
              : access.has_active_access
                ? `باقی‌مانده اشتراک: ${formatRemaining(access.remaining_active_seconds)}`
                : 'جهت فعال‌سازی مجدد، اشتراک را تمدید کنید'}
          </div>
          <div className="flex flex-wrap gap-2">
            {listing && access.has_active_access && (
              <button
                onClick={() => handleRunBacktest(listing)}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition"
              >
                اجرای بک‌تست
              </button>
            )}
            {listing && listing.can_purchase && !access.has_active_access && (
              <button
                onClick={() => handlePurchase(listing.id)}
                className="px-4 py-2 rounded-lg bg-yellow-600 hover:bg-yellow-500 text-white transition"
              >
                تمدید اشتراک
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6" style={{ direction: 'rtl', textAlign: 'right' }}>
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold text-white">مارکت‌پلیس استراتژی‌ها</h1>
        <p className="text-gray-300 text-sm">
          استراتژی‌های منتشرشده توسط کاربران را مرور کنید، دوره آزمایشی ۹ روزه را فعال کنید، نتایج را مشاهده نمایید و در صورت رضایت اشتراک را تمدید کنید.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setActiveTab('explore')}
          className={`px-4 py-2 rounded-lg text-sm font-medium ${
            activeTab === 'explore' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-200'
          }`}
        >
          مرور مارکت‌پلیس
        </button>
        <button
          onClick={() => setActiveTab('myListings')}
          className={`px-4 py-2 rounded-lg text-sm font-medium ${
            activeTab === 'myListings' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-200'
          }`}
        >
          استراتژی‌های من
        </button>
        <button
          onClick={() => setActiveTab('myAccess')}
          className={`px-4 py-2 rounded-lg text-sm font-medium ${
            activeTab === 'myAccess' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-200'
          }`}
        >
          دسترسی‌های من
        </button>
        <button
          onClick={() => setActiveTab('create')}
          className={`px-4 py-2 rounded-lg text-sm font-medium ${
            activeTab === 'create' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-200'
          }`}
        >
          اشتراک‌گذاری استراتژی جدید
        </button>
      </div>

      {isLoading ? (
        <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 text-center text-white">در حال بارگذاری...</div>
      ) : (
        <>
          {activeTab === 'explore' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {listings.length === 0 && (
                <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 text-center text-gray-300">
                  هنوز استراتژی‌ای در مارکت‌پلیس منتشر نشده است.
                </div>
              )}
              {listings.map(renderMarketplaceCard)}
            </div>
          )}

          {activeTab === 'myListings' && (
            <div className="space-y-4">
              {myListings.length === 0 && (
                <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 text-center text-gray-300">
                  هنوز استراتژی‌ای را در مارکت‌پلیس منتشر نکرده‌اید.
                </div>
              )}
              {myListings.map(renderMyListingCard)}
            </div>
          )}

          {activeTab === 'myAccess' && (
            <div className="space-y-4">
              {myAccesses.length === 0 && (
                <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 text-center text-gray-300">
                  هنوز هیچ استراتژی را برای تست یا اشتراک انتخاب نکرده‌اید.
                </div>
              )}
              {myAccesses.map(renderMyAccessCard)}
            </div>
          )}

          {activeTab === 'create' && (
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700" style={{ direction: 'rtl', textAlign: 'right' }}>
              <h2 className="text-xl font-semibold text-white mb-4">اشتراک‌گذاری استراتژی جدید</h2>
              {availableStrategies.length === 0 ? (
                <div className="text-gray-300">
                  تمام استراتژی‌های شما در مارکت‌پلیس ثبت شده‌اند یا استراتژی فعالی ندارید. برای اشتراک‌گذاری، ابتدا استراتژی جدیدی بسازید.
                </div>
              ) : (
                <form onSubmit={handleCreateListing} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">انتخاب استراتژی</label>
                      <select
                        value={formState.strategy}
                        onChange={(e) => handleFormChange('strategy', e.target.value)}
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">-- انتخاب استراتژی --</option>
                        {availableStrategies.map((strategy) => (
                          <option key={strategy.id} value={strategy.id.toString()}>
                            {strategy.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">عنوان نمایشی</label>
                      <input
                        value={formState.title}
                        onChange={(e) => handleFormChange('title', e.target.value)}
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="مثال: استراتژی روندی طلا (H4)"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">هدلاین کوتاه</label>
                      <input
                        value={formState.headline}
                        onChange={(e) => handleFormChange('headline', e.target.value)}
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="مثال: بازده ۱۸٪ میانگین در ۱۲ ماه"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">قیمت (تومان)</label>
                      <input
                        value={formState.price}
                        onChange={(e) => handleFormChange('price', e.target.value)}
                        type="number"
                        min="0"
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="مثال: 750000"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">طول اشتراک (روز)</label>
                      <input
                        value={formState.billingCycleDays}
                        onChange={(e) => handleFormChange('billingCycleDays', e.target.value)}
                        type="number"
                        min="1"
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">روزهای دوره آزمایشی</label>
                      <input
                        value={formState.trialDays}
                        onChange={(e) => handleFormChange('trialDays', e.target.value)}
                        type="number"
                        min="0"
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">تعداد بک‌تست مجاز در دوره آزمایشی</label>
                      <input
                        value={formState.trialBacktestLimit}
                        onChange={(e) => handleFormChange('trialBacktestLimit', e.target.value)}
                        type="number"
                        min="1"
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-gray-300 mb-1">توضیحات کامل</label>
                    <textarea
                      value={formState.description}
                      onChange={(e) => handleFormChange('description', e.target.value)}
                      rows={4}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="جزئیات استراتژی، منطق ورود و خروج، شرایط بازار مناسب و ..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-gray-300 mb-1">نسخه متنی استراتژی جهت مطالعه کاربران</label>
                    <textarea
                      value={formState.sharedText}
                      onChange={(e) => handleFormChange('sharedText', e.target.value)}
                      rows={4}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="مراحل دقیق اجرای استراتژی را اینجا بنویسید"
                    />
                  </div>

                <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-4 space-y-4">
                  <div className="flex items-center justify-between gap-4">
                    <h3 className="text-sm font-semibold text-blue-300">خلاصه نتایج بک‌تست</h3>
                    {summaryLoading && <span className="text-xs text-gray-400">در حال بارگذاری...</span>}
                  </div>
                  {!formState.strategy && (
                    <p className="text-sm text-gray-500">برای مشاهده نتایج، ابتدا استراتژی مورد نظر را انتخاب کنید.</p>
                  )}
                  {formState.strategy && summaryError && (
                    <div className="bg-red-900/30 border border-red-700 text-red-300 text-sm rounded-lg px-3 py-2">
                      {summaryError}
                    </div>
                  )}
                  {formState.strategy && !summaryLoading && !summaryError && strategySummary && (
                    <>
                      {!strategySummary.has_result ? (
                        <p className="text-sm text-yellow-300">
                          {strategySummary.message || 'برای این استراتژی بک‌تست قابل استفاده یافت نشد. ابتدا یک بک‌تست موفق ایجاد کنید.'}
                        </p>
                      ) : (
                        <>
                          {renderPerformanceSnapshotView(strategySummary.metrics)}
                          {renderSampleTradesView(strategySummary.sample_trades)}
                        </>
                      )}
                    </>
                  )}
                </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">نمادهای پیشنهادی (با کاما جدا شود)</label>
                      <input
                        value={formState.supportedSymbolsText}
                        onChange={(e) => handleFormChange('supportedSymbolsText', e.target.value)}
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">برچسب‌ها (با کاما جدا شود)</label>
                      <input
                        value={formState.tagsText}
                        onChange={(e) => handleFormChange('tagsText', e.target.value)}
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="مثال: روندی، طلا، swing"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                    disabled={actionLoading['create'] || summaryLoading || !strategySummary || !strategySummary.has_result}
                      className="px-6 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition disabled:opacity-50"
                    >
                      {actionLoading['create'] ? 'در حال ثبت...' : 'ایجاد استراتژی در مارکت‌پلیس'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
        </>
      )}

      {editingListing && editForm && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50" style={{ direction: 'rtl', textAlign: 'right' }}>
          <div className="bg-gray-900 rounded-xl p-6 w-full max-w-3xl border border-gray-700 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-semibold text-white mb-4">ویرایش استراتژی: {editingListing.title}</h2>
            <form onSubmit={submitEdit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-300 mb-1">استراتژی</label>
                  <input
                    value={editForm.strategy}
                    disabled
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-400"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-300 mb-1">عنوان</label>
                  <input
                    value={editForm.title}
                    onChange={(e) => handleEditFormChange('title', e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-300 mb-1">هدلاین</label>
                  <input
                    value={editForm.headline}
                    onChange={(e) => handleEditFormChange('headline', e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-300 mb-1">قیمت (تومان)</label>
                  <input
                    value={editForm.price}
                    onChange={(e) => handleEditFormChange('price', e.target.value)}
                    type="number"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-300 mb-1">طول اشتراک (روز)</label>
                  <input
                    value={editForm.billingCycleDays}
                    onChange={(e) => handleEditFormChange('billingCycleDays', e.target.value)}
                    type="number"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-300 mb-1">روزهای دوره آزمایشی</label>
                  <input
                    value={editForm.trialDays}
                    onChange={(e) => handleEditFormChange('trialDays', e.target.value)}
                    type="number"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-300 mb-1">حداکثر بک‌تست دوره آزمایشی</label>
                  <input
                    value={editForm.trialBacktestLimit}
                    onChange={(e) => handleEditFormChange('trialBacktestLimit', e.target.value)}
                    type="number"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-300 mb-1">توضیحات</label>
                <textarea
                  value={editForm.description}
                  onChange={(e) => handleEditFormChange('description', e.target.value)}
                  rows={4}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-300 mb-1">نسخه متنی اشتراک‌گذاری شده</label>
                <textarea
                  value={editForm.sharedText}
                  onChange={(e) => handleEditFormChange('sharedText', e.target.value)}
                  rows={4}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                />
              </div>

              <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-4 space-y-4">
                <h3 className="text-sm font-semibold text-blue-300">نتایج بک‌تست منتشر شده</h3>
                {renderPerformanceSnapshotView(editingListing.performance_snapshot)}
                {renderSampleTradesView(editingListing.sample_results)}
                {editingListing.source_result_id && (
                  <p className="text-xs text-gray-500">شناسه بک‌تست منبع: {editingListing.source_result_id}</p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-300 mb-1">نمادهای پیشنهادی</label>
                  <input
                    value={editForm.supportedSymbolsText}
                    onChange={(e) => handleEditFormChange('supportedSymbolsText', e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-300 mb-1">برچسب‌ها</label>
                  <input
                    value={editForm.tagsText}
                    onChange={(e) => handleEditFormChange('tagsText', e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={closeEditModal}
                  className="px-4 py-2 rounded-lg bg-gray-700 text-white hover:bg-gray-600 transition"
                >
                  انصراف
                </button>
                <button
                  type="submit"
                  disabled={actionLoading[`submitEdit-${editingListing.id}`]}
                  className="px-6 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition disabled:opacity-50"
                >
                  {actionLoading[`submitEdit-${editingListing.id}`] ? 'در حال ذخیره...' : 'ذخیره تغییرات'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default StrategyMarketplace

