import { useEffect, useState } from 'react'
import { useTodos } from './hooks/useTodos'
import { useTimer } from './hooks/useTimer'
import { TodoInput } from './components/TodoInput'
import { TodoList } from './components/TodoList'
import { TagFilter } from './components/TagFilter'
import { TimerAlert } from './components/TimerAlert'
import { BreakSuggestion } from './components/BreakSuggestion'
import { Timeline } from './components/Timeline'
import { StorageWarningBanner } from './components/StorageWarningBanner'
import { collectTags, filterByTags } from './lib/todos'
import { durationForType, formatRemaining, nextBreakType, remainingMs } from './lib/timer'
import type { Session } from './types'
import './App.css'

const DEFAULT_TITLE = 'todo-app'

function App() {
  const { todos, corrupted, saveFailed: todosSaveFailed, add, update, remove, toggleDone, addTag, removeTag } =
    useTodos()
  const { timerState, sessions, lastCompletedSession, saveFailed: timerSaveFailed, start, stop } = useTimer()
  const writeFailed = todosSaveFailed || timerSaveFailed
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [now, setNow] = useState(() => new Date().toISOString())
  const [alertSession, setAlertSession] = useState<Session | null>(null)

  useEffect(() => {
    if (timerState === null) return
    const interval = setInterval(() => setNow(new Date().toISOString()), 1000)
    return () => clearInterval(interval)
  }, [timerState])

  useEffect(() => {
    if (lastCompletedSession === null) return
    setAlertSession(lastCompletedSession)
  }, [lastCompletedSession])

  const remainingLabel =
    timerState === null
      ? null
      : formatRemaining(remainingMs(timerState.startedAt, durationForType(timerState.type), now))

  useEffect(() => {
    if (remainingLabel === null) {
      document.title = DEFAULT_TITLE
      return undefined
    }
    document.title = `(${remainingLabel}) ${DEFAULT_TITLE}`
    return () => {
      document.title = DEFAULT_TITLE
    }
  }, [remainingLabel])

  const toggleTagFilter = (tag: string) => {
    setSelectedTags((prev) => (prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]))
  }

  const visibleTodos = filterByTags(todos, selectedTags)

  const completedFocusCount = sessions.filter((s) => s.type === 'focus' && s.result === 'completed').length
  const suggestedBreakType = alertSession !== null && alertSession.type === 'focus' ? nextBreakType(completedFocusCount) : null

  const handleStartBreak = () => {
    if (alertSession === null || suggestedBreakType === null) return
    start(alertSession.todoId, suggestedBreakType)
    setAlertSession(null)
  }

  const handleSkipBreak = () => {
    setAlertSession(null)
  }

  return (
    <div className="app">
      <h1>Todo App</h1>
      {corrupted && <StorageWarningBanner variant="corrupted" />}
      {writeFailed && <StorageWarningBanner variant="writeFailure" />}
      {alertSession !== null && <TimerAlert session={alertSession} onDismiss={() => setAlertSession(null)} />}
      {suggestedBreakType !== null && (
        <BreakSuggestion breakType={suggestedBreakType} onStart={handleStartBreak} onSkip={handleSkipBreak} />
      )}
      <TodoInput onAdd={add} />
      <TagFilter tags={collectTags(todos)} selectedTags={selectedTags} onToggle={toggleTagFilter} />
      <TodoList
        todos={visibleTodos}
        onToggle={toggleDone}
        onRemove={remove}
        onUpdateTitle={update}
        onAddTag={addTag}
        onRemoveTag={removeTag}
        activeTodoId={timerState?.todoId ?? null}
        remainingLabel={remainingLabel}
        onStartFocus={start}
        onStopFocus={stop}
        sessions={sessions}
      />
      <h2 className="app__section-title">타임라인</h2>
      <Timeline sessions={sessions} todos={todos} />
    </div>
  )
}

export default App
