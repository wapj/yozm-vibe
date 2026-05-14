import styles from './StaleIndicator.module.css'

interface Props {
  failed: boolean
  lastUpdated: number | null
}

function formatHHMM(ts: number): string {
  const d = new Date(ts)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

export default function StaleIndicator({ failed, lastUpdated }: Props) {
  if (!failed) return null
  return (
    <span className={styles.indicator}>
      갱신 실패{lastUpdated !== null ? ` · 마지막 갱신 ${formatHHMM(lastUpdated)}` : ''}
    </span>
  )
}
