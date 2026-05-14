import { useState, useEffect } from 'react'
import styles from './ClockWidget.module.css'
import { formatDateLine, formatTimeLine } from './format'

export default function ClockWidget() {
  const [now, setNow] = useState<Date>(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>시계</h2>
      <div className={styles.date}>{formatDateLine(now)}</div>
      <div className={styles.time}>{formatTimeLine(now)}</div>
    </div>
  )
}
