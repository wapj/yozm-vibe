import { render, fireEvent } from '@testing-library/react'

// The module constant `available = isLocalStorageAvailable()` is evaluated once at import time.
// We must mock the module before the component is imported so the constant is initialised with false.
vi.mock('../lib/storage', () => ({ isLocalStorageAvailable: () => false }))

describe('StorageWarningBanner (unavailable branch)', () => {
  test('renders banner text and dismiss button when localStorage is unavailable', async () => {
    const { default: StorageWarningBanner } = await import('./StorageWarningBanner')
    const { container, getByLabelText } = render(<StorageWarningBanner />)
    expect(container.textContent).toContain('현재 브라우저에서 데이터 저장이 비활성화되어 있어')
    expect(getByLabelText('배너 닫기')).toBeTruthy()
  })

  test('hides banner after dismiss button is clicked', async () => {
    const { default: StorageWarningBanner } = await import('./StorageWarningBanner')
    const { container, getByLabelText } = render(<StorageWarningBanner />)
    fireEvent.click(getByLabelText('배너 닫기'))
    expect(container.firstChild).toBeNull()
  })
})
