import { useState, useEffect, useRef } from 'react'
import { getWeather, SEONGNAM, type WeatherSnapshot } from '../../lib/api/openMeteo'
import { getCacheMeta } from '../../lib/fetchWithCache'
import { describeWeather } from './weatherCode'
import StaleIndicator from '../../components/StaleIndicator'
import styles from './WeatherWidget.module.css'

const CACHE_KEY = `weather.${SEONGNAM.latitude}.${SEONGNAM.longitude}`

export default function WeatherWidget() {
  const [snap, setSnap] = useState<WeatherSnapshot | null>(null)
  const [failed, setFailed] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<number | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    async function loadOnce() {
      try {
        const data = await getWeather()
        setSnap(data)
        setFailed(false)
        setLastUpdated(Date.now())
      } catch {
        setFailed(true)
        setLastUpdated(getCacheMeta(CACHE_KEY).lastUpdated)
      }
    }

    loadOnce()
    timerRef.current = setInterval(loadOnce, 10 * 60 * 1000)
    return () => {
      if (timerRef.current !== null) clearInterval(timerRef.current)
    }
  }, [])

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h2 className={styles.title}>날씨</h2>
        <StaleIndicator failed={failed} lastUpdated={lastUpdated} />
      </div>
      {snap === null ? (
        <div className={styles.empty}>데이터를 불러오는 중...</div>
      ) : (
        <>
          <div className={styles.main}>
            {describeWeather(snap.weatherCode).emoji} {Math.round(snap.tempC)}°C
            <span className={styles.feelsLike}>(체감 {Math.round(snap.feelsLikeC)}°C)</span>
          </div>
          <div className={styles.description}>{describeWeather(snap.weatherCode).description}</div>
          <div className={styles.meta}>
            최고 {Math.round(snap.highC)}° · 최저 {Math.round(snap.lowC)}° · 강수 {snap.precipitationProb}%
          </div>
        </>
      )}
    </div>
  )
}
