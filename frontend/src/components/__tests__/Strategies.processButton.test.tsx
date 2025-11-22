import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import Strategies from '../Strategies'

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
}))

vi.mock('../ToastProvider', () => ({
  useToast: () => ({ showToast: toastMocks.showToast }),
}))

vi.mock('../../api/client', () => ({
  getStrategies: apiMocks.getStrategies,
  addStrategy: apiMocks.addStrategy,
  deleteStrategy: apiMocks.deleteStrategy,
  processStrategy: apiMocks.processStrategy,
  getAPIConfigurations: apiMocks.getAPIConfigurations,
  setPrimaryStrategy: apiMocks.setPrimaryStrategy,
}))

vi.mock('../../hooks/useRateLimit', () => ({
  useRateLimit: () => (fn: (...args: unknown[]) => unknown) => (...args: unknown[]) => fn(...args),
}))

const mockShowToast = toastMocks.showToast
const mockGetStrategies = apiMocks.getStrategies
const mockProcessStrategy = apiMocks.processStrategy
const mockGetAPIConfigurations = apiMocks.getAPIConfigurations

describe('Strategies process button', () => {
  const strategy = {
    id: 1,
    name: 'استراتژی تست',
    description: '',
    strategy_file: 'test.txt',
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
  })

  it('starts processing when user clicks the process button', async () => {
    render(<Strategies />)

    const processButton = await screen.findByRole('button', { name: 'پردازش' })

    await userEvent.click(processButton)

    await waitFor(() => expect(mockProcessStrategy).toHaveBeenCalledWith(strategy.id))

    expect(mockShowToast).toHaveBeenCalledWith('در حال پردازش استراتژی...', { type: 'info' })
    await waitFor(() =>
      expect(mockShowToast).toHaveBeenCalledWith(expect.stringContaining('پردازش شد'), expect.objectContaining({ type: 'success' })),
    )
  })
})

