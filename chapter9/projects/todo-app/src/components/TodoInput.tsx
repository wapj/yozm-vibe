import { useState } from 'react'
import type { FormEvent } from 'react'

interface TodoInputProps {
  onAdd: (title: string) => void
}

export function TodoInput({ onAdd }: TodoInputProps) {
  const [value, setValue] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = value.trim()
    if (trimmed.length === 0) return
    onAdd(trimmed)
    setValue('')
  }

  return (
    <form className="todo-input" onSubmit={handleSubmit}>
      <input
        type="text"
        className="todo-input__field"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="새 할일을 입력하세요"
        aria-label="새 할일"
      />
      <button type="submit" className="todo-input__submit">
        추가
      </button>
    </form>
  )
}
