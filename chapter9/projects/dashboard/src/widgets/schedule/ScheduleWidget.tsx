import { useState, useEffect } from 'react'
import { useLocalStorage, storageKey } from '../../lib'
import { formatToday, filterToday, sortByTime } from './filter'
import type { ScheduleItem } from './types'
import styles from './ScheduleWidget.module.css'

const KEY = storageKey('schedule', 'items')

function newId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export default function ScheduleWidget() {
  const [items, setItems] = useLocalStorage<ScheduleItem[]>(KEY, [])
  const [now, setNow] = useState<Date>(() => new Date())
  const [title, setTitle] = useState('')
  const [time, setTime] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const id = setInterval(() => {
      setNow(new Date())
      try {
        const raw = window.localStorage.getItem(KEY)
        const ext = raw === null ? [] : JSON.parse(raw) as ScheduleItem[]
        setItems(ext)
      } catch {}
    }, 5 * 60 * 1000)
    return () => clearInterval(id)
  }, [])

  function handleAdd() {
    const trimmed = title.trim()
    if (trimmed === '') {
      setError('제목을 입력하세요.')
      return
    }
    setError(null)
    const newItem: ScheduleItem = {
      id: newId(),
      date: formatToday(now),
      time: time || null,
      title: trimmed,
      done: false,
    }
    setItems(prev => [...prev, newItem])
    setTitle('')
    setTime('')
  }

  function handleToggle(id: string) {
    setItems(prev => prev.map(i => i.id === id ? { ...i, done: !i.done } : i))
  }

  function handleDelete(id: string) {
    setItems(prev => prev.filter(i => i.id !== id))
  }

  const today = formatToday(now)
  const visible = sortByTime(filterToday(items, today))

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>일정</h2>
      <form className={styles.form} onSubmit={e => { e.preventDefault(); handleAdd() }}>
        <input
          className={`${styles.input} ${styles.timeInput}`}
          type="time"
          value={time}
          onChange={e => setTime(e.target.value)}
        />
        <input
          className={`${styles.input} ${styles.titleInput}`}
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="일정 제목"
        />
        <button type="submit">추가</button>
      </form>
      {error && <div className={styles.error}>{error}</div>}
      {visible.length === 0 ? (
        <div className={styles.empty}>오늘 일정이 없습니다.</div>
      ) : (
        <ul className={styles.list}>
          {visible.map(item => (
            <li
              key={item.id}
              className={`${styles.item} ${item.done ? styles.done : ''}`}
            >
              <input
                type="checkbox"
                checked={item.done}
                onChange={() => handleToggle(item.id)}
              />
              <span className={styles.time}>{item.time ?? ''}</span>
              <span className={styles.itemTitle}>{item.title}</span>
              <button
                className={styles.deleteBtn}
                onClick={() => handleDelete(item.id)}
                aria-label="삭제"
              >×</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
