import { useState } from 'react'

export type StorageWarningVariant = 'corrupted' | 'writeFailure'

const MESSAGES: Record<StorageWarningVariant, string> = {
  corrupted: '저장된 데이터를 읽는 중 문제가 발생해 빈 상태로 시작합니다.',
  writeFailure: '저장에 실패했으나 현재 상태는 유지됩니다.',
}

interface StorageWarningBannerProps {
  variant: StorageWarningVariant
}

export function StorageWarningBanner({ variant }: StorageWarningBannerProps) {
  const [dismissed, setDismissed] = useState(false)

  if (dismissed) return null

  return (
    <div className="storage-warning-banner" role="alert">
      <span>{MESSAGES[variant]}</span>
      <button type="button" className="storage-warning-banner__dismiss" onClick={() => setDismissed(true)}>
        닫기
      </button>
    </div>
  )
}
