import { useCallback, useEffect, useRef, useState } from 'react'
import { loadData, saveData } from '../storage'
import {
  addTag as addTagPure,
  addTodo,
  createTodo,
  removeTag as removeTagPure,
  removeTodo,
  toggleDone,
  updateTodoTitle,
} from '../lib/todos'
import type { StorageData } from '../types'

export function useTodos() {
  const [initialLoad] = useState(() => loadData())
  const [data, setData] = useState<StorageData>(() => initialLoad.data)
  const [saveFailed, setSaveFailed] = useState(false)
  const initialized = useRef(false)

  useEffect(() => {
    if (!initialized.current) {
      initialized.current = true
      return
    }
    const result = saveData(data)
    setSaveFailed(!result.ok)
  }, [data])

  const persist = useCallback((updateTodos: (todos: StorageData['todos']) => StorageData['todos']) => {
    setData((prev) => {
      const latest = loadData().data
      return { ...latest, todos: updateTodos(prev.todos) }
    })
  }, [])

  const add = useCallback(
    (title: string) => {
      const todo = createTodo(crypto.randomUUID(), title, new Date().toISOString())
      persist((todos) => addTodo(todos, todo))
    },
    [persist],
  )

  const update = useCallback(
    (id: string, title: string) => {
      persist((todos) => updateTodoTitle(todos, id, title))
    },
    [persist],
  )

  const remove = useCallback(
    (id: string) => {
      persist((todos) => removeTodo(todos, id))
    },
    [persist],
  )

  const toggle = useCallback(
    (id: string) => {
      persist((todos) => toggleDone(todos, id))
    },
    [persist],
  )

  const addTag = useCallback(
    (id: string, tag: string) => {
      persist((todos) => addTagPure(todos, id, tag))
    },
    [persist],
  )

  const removeTag = useCallback(
    (id: string, tag: string) => {
      persist((todos) => removeTagPure(todos, id, tag))
    },
    [persist],
  )

  return {
    todos: data.todos,
    corrupted: initialLoad.corrupted,
    saveFailed,
    add,
    update,
    remove,
    toggleDone: toggle,
    addTag,
    removeTag,
  }
}
