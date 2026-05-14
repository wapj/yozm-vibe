import { useState } from 'react'
import { isLocalStorageAvailable } from '../lib/storage'
import styles from './StorageWarningBanner.module.css'

const available = isLocalStorageAvailable()

export default function StorageWarningBanner() {
  const [visible, setVisible] = useState<boolean>(true)

  if (available || !visible) return null

  return (
    <div className={styles.banner} role="alert">
      <span className={styles.text}>현재 브라우저에서 데이터 저장이 비활성화되어 있어, 메모/일정/링크가 새로고침 후 사라집니다.</span>
      <button type="button" className={styles.dismiss} onClick={() => setVisible(false)} aria-label="배너 닫기">×</button>
    </div>
  )
}
