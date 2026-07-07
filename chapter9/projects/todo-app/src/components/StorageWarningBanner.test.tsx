import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StorageWarningBanner } from './StorageWarningBanner'

describe('StorageWarningBanner', () => {
  it('corrupted variant는 읽기 실패 문구를 표시한다', () => {
    render(<StorageWarningBanner variant="corrupted" />)

    expect(screen.getByRole('alert')).toHaveTextContent(
      '저장된 데이터를 읽는 중 문제가 발생해 빈 상태로 시작합니다.',
    )
  })

  it('writeFailure variant는 쓰기 실패 문구를 표시하며 corrupted 문구와 다르다', () => {
    render(<StorageWarningBanner variant="writeFailure" />)

    expect(screen.getByRole('alert')).toHaveTextContent('저장에 실패했으나 현재 상태는 유지됩니다.')
    expect(screen.getByRole('alert')).not.toHaveTextContent(
      '저장된 데이터를 읽는 중 문제가 발생해 빈 상태로 시작합니다.',
    )
  })

  it('닫기 버튼을 클릭하면 배너가 사라진다', () => {
    render(<StorageWarningBanner variant="corrupted" />)

    fireEvent.click(screen.getByRole('button', { name: '닫기' }))

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
