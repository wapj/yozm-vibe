import { useState, useEffect } from 'react'
import styles from './QuoteWidget.module.css'
import quotesData from './quotes.ko.json'
import { computeQuoteIndex } from './dateIndex'

type Quote = { text: string; author: string }
const quotes = quotesData as Quote[]

export default function QuoteWidget() {
  const [now, setNow] = useState<Date>(() => new Date())

  useEffect(() => {
    const id = setInterval(() => {
      const current = new Date()
      setNow(prev =>
        prev.getFullYear() === current.getFullYear() &&
        prev.getMonth() === current.getMonth() &&
        prev.getDate() === current.getDate()
          ? prev
          : current
      )
    }, 60_000)
    return () => clearInterval(id)
  }, [])

  const idx = computeQuoteIndex(now, quotes.length)
  const quote = quotes[idx]

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>명언</h2>
      <blockquote className={styles.text}>{quote.text}</blockquote>
      <div className={styles.author}>— {quote.author}</div>
    </div>
  )
}
