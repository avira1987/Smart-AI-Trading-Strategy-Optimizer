import client, { StrategyMarketplaceListing, StrategyListingAccess } from './client'

export interface MarketplaceListingPayload {
  strategy: number
  title: string
  headline?: string
  description?: string
  shared_text?: string
  price: number | string
  billing_cycle_days?: number
  trial_days?: number
  trial_backtest_limit?: number
  supported_symbols?: string[]
  tags?: string[]
}

export interface StrategySummaryResponse {
  has_result: boolean
  strategy_id: number
  strategy_name: string
  result_id?: number
  metrics?: Record<string, any>
  sample_trades?: any[]
  message?: string
}

export const getMarketplaceListings = () =>
  client.get<StrategyMarketplaceListing[]>('/marketplace/listings/')

export const getMarketplaceListing = (id: number) =>
  client.get<StrategyMarketplaceListing>(`/marketplace/listings/${id}/`)

export const createMarketplaceListing = (payload: MarketplaceListingPayload) =>
  client.post<StrategyMarketplaceListing>('/marketplace/listings/', payload)

export const updateMarketplaceListing = (id: number, payload: Partial<MarketplaceListingPayload>) =>
  client.patch<StrategyMarketplaceListing>(`/marketplace/listings/${id}/`, payload)

export const deleteMarketplaceListing = (id: number) =>
  client.delete(`/marketplace/listings/${id}/`)

export const publishMarketplaceListing = (id: number) =>
  client.post<StrategyMarketplaceListing>(`/marketplace/listings/${id}/publish/`)

export const unpublishMarketplaceListing = (id: number) =>
  client.post<StrategyMarketplaceListing>(`/marketplace/listings/${id}/unpublish/`)

export const startMarketplaceTrial = (id: number) =>
  client.post<{ access: StrategyListingAccess }>(`/marketplace/listings/${id}/start-trial/`)

export const purchaseMarketplaceListing = (id: number) =>
  client.post<{ access: StrategyListingAccess }>(`/marketplace/listings/${id}/purchase/`)

export const getMarketplaceAccess = (id: number) =>
  client.get<{ access: StrategyListingAccess | null }>(`/marketplace/listings/${id}/access/`)

export const getMarketplaceListingAccesses = (id: number) =>
  client.get<{ results: StrategyListingAccess[] }>(`/marketplace/listings/${id}/accesses/`)

export const getMyMarketplaceListings = () =>
  client.get<{ results: StrategyMarketplaceListing[] }>('/marketplace/listings/my-listings/')

export const getMyMarketplaceAccesses = () =>
  client.get<{ results: StrategyListingAccess[] }>('/marketplace/listings/my-accesses/')

export const getStrategyMarketplaceSummary = (strategyId: number) =>
  client.get<StrategySummaryResponse>('/marketplace/listings/strategy-summary/', {
    params: { strategy: strategyId },
  })

