import { useState } from 'react'
import { useLocalStorage, storageKey } from '../../lib'
import { sortMemos } from './sort'
import type { MemoItem } from './types'
import styles from './MemoWidget.module.css'

const KEY = storageKey('memo', 'items')

function newId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export default function MemoWidget() {
  const [items, setItems] = useLocalStorage<MemoItem[]>(KEY, [])
  const [text, setText] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleAdd() {
    const trimmed = text.trim()
    if (trimmed === '') {
      setError('내용을 입력하세요.')
      return
    }
    setError(null)
    const newItem: MemoItem = {
      id: newId(),
      text: trimmed,
      done: false,
      createdAt: Date.now(),
    }
    setItems(prev => sortMemos([...prev, newItem]))
    setText('')
  }

  function handleToggle(id: string) {
    setItems(prev => sortMemos(prev.map(i => i.id === id ? { ...i, done: !i.done } : i)))
  }

  function handleDelete(id: string) {
    setItems(prev => prev.filter(i => i.id !== id))
  }

  const sorted = sortMemos(items)

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>메모</h2>
      <form className={styles.form} onSubmit={e => { e.preventDefault(); handleAdd() }}>
        <input
          className={styles.input}
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="할 일을 입력"
        />
        <button type="submit">추가</button>
      </form>
      {error && <div className={styles.error}>{error}</div>}
      <ul className={styles.list}>
        {sorted.map(item => (
          <li
            className={`${styles.item} ${item.done ? styles.done : ''}`}
            key={item.id}
          >
            <input
              type="checkbox"
              checked={item.done}
              onChange={() => handleToggle(item.id)}
            />
            <span>{item.text}</span>
            <button
              className={styles.deleteBtn}
              onClick={() => handleDelete(item.id)}
              aria-label="삭제"
            >×</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
