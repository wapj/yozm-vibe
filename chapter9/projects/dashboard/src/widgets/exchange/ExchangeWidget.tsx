import { useState, useEffect, useRef } from 'react'
import { getExchange, type ExchangeSnapshot, type ExchangePairSnapshot } from '../../lib/api/exchangerateHost'
import { getCacheMeta } from '../../lib/fetchWithCache'
import StaleIndicator from '../../components/StaleIndicator'
import styles from './ExchangeWidget.module.css'

const META_KEY = 'exchange.USD.KRW'

function arrowFor(d: 'up' | 'down' | 'flat'): string {
  return d === 'up' ? '▲' : d === 'down' ? '▼' : '–'
}

function formatRate(rate: number): string {
  return rate.toFixed(2)
}

export default function ExchangeWidget() {
  const [snap, setSnap] = useState<ExchangeSnapshot | null>(null)
  const [failed, setFailed] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<number | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    async function loadOnce() {
      try {
        setSnap(await getExchange())
        setFailed(false)
        setLastUpdated(Date.now())
      } catch {
        setFailed(true)
        setLastUpdated(getCacheMeta(META_KEY).lastUpdated)
      }
    }

    loadOnce()
    timerRef.current = setInterval(loadOnce, 30 * 60 * 1000)
    return () => {
      if (timerRef.current !== null) clearInterval(timerRef.current)
    }
  }, [])

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h2 className={styles.title}>환율</h2>
        <StaleIndicator failed={failed} lastUpdated={lastUpdated} />
      </div>
      {snap === null ? (
        <div className={styles.empty}>데이터를 불러오는 중...</div>
      ) : (
        <ul className={styles.list}>
          {snap.pairs.map((pair: ExchangePairSnapshot) => (
            <li className={styles.row} key={pair.base}>
              <span className={styles.base}>{pair.base}</span>
              <span className={styles.rate}>{formatRate(pair.rateKRW)} 원</span>
              <span className={styles[`dir_${pair.direction}`]}>
                {arrowFor(pair.direction)} {Math.abs(pair.delta).toFixed(2)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
