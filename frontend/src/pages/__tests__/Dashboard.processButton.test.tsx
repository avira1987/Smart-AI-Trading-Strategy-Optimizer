import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import Dashboard from '../Dashboard'

const toastMocks = vi.hoisted(() => ({
  showToast: vi.fn(),
}))

const apiMocks = vi.hoisted(() => ({
  getStrategies: vi.fn(),
  addStrategy: vi.fn(),
  deleteStrategy: vi.fn(),
  processStrategy: vi.fn(),
  getAPIConfigurations: vi.fn(),
  setPrimaryStrategy: vi.fn(),
  getWalletBalance: vi.fn(),
  getJobs: vi.fn(),
  getResults: vi.fn(),
}))

vi.mock('../../components/ToastProvider', () => ({
  useToast: () => ({ showToast: toastMocks.showToast }),
}))

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ user: { id: 1, email: 'test@example.com' } }),
}))

vi.mock('../../context/FeatureFlagsContext', () => ({
  useFeatureFlags: () => ({ liveTradingEnabled: false }),
}))

vi.mock('../../components/Jobs', () => ({
  __esModule: true,
  default: () => <div data-testid="jobs-component" />,
}))

vi.mock('../../api/client', () => ({
  getStrategies: apiMocks.getStrategies,
  addStrategy: apiMocks.addStrategy,
  deleteStrategy: apiMocks.deleteStrategy,
  processStrategy: apiMocks.processStrategy,
  getAPIConfigurations: apiMocks.getAPIConfigurations,
  setPrimaryStrategy: apiMocks.setPrimaryStrategy,
  getWalletBalance: apiMocks.getWalletBalance,
  getJobs: apiMocks.getJobs,
  getResults: apiMocks.getResults,
}))

vi.mock('../../hooks/useRateLimit', () => ({
  useRateLimit: () => (fn: (...args: unknown[]) => unknown) => (...args: unknown[]) => fn(...args),
}))

const mockShowToast = toastMocks.showToast
const mockGetStrategies = apiMocks.getStrategies
const mockProcessStrategy = apiMocks.processStrategy
const mockGetAPIConfigurations = apiMocks.getAPIConfigurations
const mockGetWalletBalance = apiMocks.getWalletBalance
const mockGetJobs = apiMocks.getJobs
const mockGetResults = apiMocks.getResults

describe('Dashboard process button', () => {
  const strategy = {
    id: 1,
    name: 'استراتژی داشبورد',
    description: '',
    strategy_file: 'dashboard.txt',
    is_active: true,
    is_primary: false,
    uploaded_at: new Date().toISOString(),
    processing_status: 'not_processed',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetStrategies.mockResolvedValue({ data: [strategy] })
    mockGetAPIConfigurations.mockResolvedValue({ data: [] })
    mockProcessStrategy.mockResolvedValue({
      data: {
        status: 'success',
        analysis_sources_display: {
          processing_duration_display: '1 ثانیه',
        },
      },
    })
    mockGetWalletBalance.mockResolvedValue({ data: { balance: 0 } })
    mockGetJobs.mockResolvedValue({ data: [] })
    mockGetResults.mockResolvedValue({ data: [] })
  })

  it('processes a strategy when clicking the dashboard button', async () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Dashboard />
      </MemoryRouter>,
    )

    const processButton = await screen.findByRole('button', { name: 'پردازش' })

    await userEvent.click(processButton)

    await waitFor(() => expect(mockProcessStrategy).toHaveBeenCalledWith(strategy.id))
    expect(mockShowToast).toHaveBeenCalledWith('در حال پردازش استراتژی...', { type: 'info' })
    await waitFor(() =>
      expect(mockShowToast).toHaveBeenCalledWith(
        expect.stringContaining('پردازش شد'),
        expect.objectContaining({ type: 'success' }),
      ),
    )
  })
})

