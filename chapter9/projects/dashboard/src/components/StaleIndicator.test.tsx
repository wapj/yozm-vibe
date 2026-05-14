import { render } from '@testing-library/react'
import StaleIndicator from './StaleIndicator'

describe('StaleIndicator', () => {
  test('returns null when failed=false', () => {
    const { container } = render(<StaleIndicator failed={false} lastUpdated={null} />)
    expect(container.firstChild).toBeNull()
  })

  test('shows 갱신 실패 with no time suffix when failed=true and lastUpdated=null', () => {
    const { container } = render(<StaleIndicator failed={true} lastUpdated={null} />)
    expect(container.textContent).toBe('갱신 실패')
  })

  test('shows 갱신 실패 · 마지막 갱신 HH:MM when failed=true and lastUpdated is a timestamp', () => {
    const ts = 1700000000000
    const d = new Date(ts)
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    const { container } = render(<StaleIndicator failed={true} lastUpdated={ts} />)
    expect(container.textContent).toBe(`갱신 실패 · 마지막 갱신 ${hh}:${mm}`)
  })

  test('zero-pads single-digit hours and minutes', () => {
    // Find a timestamp where both hours and minutes are single digit (e.g. 09:05)
    const base = new Date()
    base.setHours(9, 5, 0, 0)
    const ts = base.getTime()
    const { container } = render(<StaleIndicator failed={true} lastUpdated={ts} />)
    expect(container.textContent).toContain('09:05')
  })
})
