import { act, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { SCHEMA_VERSION, STORAGE_KEY } from './constants'
import type { Session, StorageData, Todo } from './types'

function readStorage(): StorageData {
  return JSON.parse(localStorage.getItem(STORAGE_KEY)!) as StorageData
}

class MemoryStorage {
  private store = new Map<string, string>()
  getItem(key: string): string | null {
    return this.store.has(key) ? this.store.get(key)! : null
  }
  setItem(key: string, value: string): void {
    this.store.set(key, value)
  }
  removeItem(key: string): void {
    this.store.delete(key)
  }
  clear(): void {
    this.store.clear()
  }
}

Object.defineProperty(globalThis, 'localStorage', {
  configurable: true,
  value: new MemoryStorage(),
})

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('App', () => {
  it('입력창에 제목을 입력해 추가하면 목록에 나타난다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    expect(screen.getByText('우유 사기')).toBeInTheDocument()
  })

  it('완료 체크박스를 토글하면 완료 상태가 반영된다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))
    await user.click(screen.getByRole('checkbox'))

    expect(screen.getByRole('checkbox')).toBeChecked()
  })

  it('삭제 버튼을 클릭하면 목록에서 사라진다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))
    await user.click(screen.getByRole('button', { name: '삭제' }))

    expect(screen.queryByText('우유 사기')).not.toBeInTheDocument()
  })

  it('태그를 부착하면 화면에 태그 칩이 나타나고, 제거하면 사라진다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    await user.type(screen.getByLabelText('태그 추가'), '집중{Enter}')

    expect(screen.getByRole('button', { name: '집중 태그 제거' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '집중 태그 제거' }))

    expect(screen.queryByRole('button', { name: '집중 태그 제거' })).not.toBeInTheDocument()
  })

  it('태그 필터를 선택하면 해당 태그의 할일만 남고, 해제하면 전체가 복원된다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))
    await user.type(screen.getByLabelText('새 할일'), '보고서 작성')
    await user.click(screen.getByRole('button', { name: '추가' }))

    const tagInputs = screen.getAllByLabelText('태그 추가')
    await user.type(tagInputs[0], '집안일{Enter}')
    await user.type(tagInputs[1], '업무{Enter}')

    await user.click(screen.getByRole('button', { name: '집안일' }))

    expect(screen.getByText('우유 사기')).toBeInTheDocument()
    expect(screen.queryByText('보고서 작성')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '집안일' }))

    expect(screen.getByText('우유 사기')).toBeInTheDocument()
    expect(screen.getByText('보고서 작성')).toBeInTheDocument()
  })

  it('할일에서 집중을 시작하면 남은 시간이 표시되고, 중단하면 사라진다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    vi.useFakeTimers()

    fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
    expect(screen.getByText('25:00')).toBeInTheDocument()

    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(screen.getByText('24:59')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '중단' }))
    expect(screen.queryByText('24:59')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '집중 시작' })).toBeInTheDocument()

    vi.useRealTimers()
  })

  it('진행 중 탭 제목에 남은 시간이 표시되고, 중단·완료 후 todo-app로 복원된다', async () => {
    const user = userEvent.setup()
    render(<App />)

    expect(document.title).toBe('todo-app')

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    vi.useFakeTimers()

    fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
    expect(document.title).toBe('(25:00) todo-app')

    fireEvent.click(screen.getByRole('button', { name: '중단' }))
    expect(document.title).toBe('todo-app')

    fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
    expect(document.title).toBe('(25:00) todo-app')

    act(() => {
      vi.advanceTimersByTime(25 * 60 * 1000)
    })
    expect(document.title).toBe('todo-app')

    vi.useRealTimers()
  })

  it('집중을 완료하면 해당 할일 옆에 완료된 뽀모도로 횟수가 반영된다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    expect(screen.getByText('완료 0회')).toBeInTheDocument()

    vi.useFakeTimers()

    fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
    act(() => {
      vi.advanceTimersByTime(25 * 60 * 1000)
    })

    expect(screen.getByText('완료 1회')).toBeInTheDocument()

    vi.useRealTimers()
  })

  it('집중 완료 시 종료 알림 배너가 표시되고, 닫기 조작으로 배너가 사라진다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    vi.useFakeTimers()

    fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()

    act(() => {
      vi.advanceTimersByTime(25 * 60 * 1000)
    })

    expect(screen.getByRole('alert')).toHaveTextContent('집중 타이머가 종료되었습니다.')

    fireEvent.click(screen.getByRole('button', { name: '닫기' }))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()

    vi.useRealTimers()
  })

  it('타이머를 중단하면 종료 알림 배너가 표시되지 않고 완료 횟수도 증가하지 않는다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    vi.useFakeTimers()

    fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
    act(() => {
      vi.advanceTimersByTime(1000)
    })
    fireEvent.click(screen.getByRole('button', { name: '중단' }))

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByText('완료 0회')).toBeInTheDocument()

    vi.useRealTimers()
  })

  it('초기 렌더(완료 0회)에서는 휴식 제안 UI가 표시되지 않는다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    expect(screen.queryByRole('button', { name: '휴식 시작' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '건너뛰기' })).not.toBeInTheDocument()
  })

  it('집중 완료 직후 휴식 제안 UI가 표시되고, 휴식 시작을 선택하면 짧은 휴식 타이머가 시작된다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    vi.useFakeTimers()

    fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
    act(() => {
      vi.advanceTimersByTime(25 * 60 * 1000)
    })

    expect(screen.getByRole('status')).toHaveTextContent('짧은 휴식(5분)을 시작할까요?')
    expect(screen.getByRole('alert')).toHaveTextContent('집중 타이머가 종료되었습니다.')

    fireEvent.click(screen.getByRole('button', { name: '휴식 시작' }))

    expect(screen.getByText('05:00')).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()

    vi.useRealTimers()
  })

  it('휴식 제안에서 건너뛰기를 선택하면 제안이 사라지고 새 타이머가 시작되지 않는다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    vi.useFakeTimers()

    fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
    act(() => {
      vi.advanceTimersByTime(25 * 60 * 1000)
    })

    fireEvent.click(screen.getByRole('button', { name: '건너뛰기' }))

    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '집중 시작' })).toBeInTheDocument()

    vi.useRealTimers()
  })

  it('집중 완료 4회째에는 긴 휴식(15분) 제안이 표시된다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    vi.useFakeTimers()

    for (let i = 0; i < 3; i += 1) {
      fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000)
      })
      expect(screen.getByRole('status')).toHaveTextContent('짧은 휴식(5분)을 시작할까요?')
      fireEvent.click(screen.getByRole('button', { name: '건너뛰기' }))
    }

    fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
    act(() => {
      vi.advanceTimersByTime(25 * 60 * 1000)
    })

    expect(screen.getByRole('status')).toHaveTextContent('긴 휴식(15분)을 시작할까요?')

    vi.useRealTimers()
  })

  it('focus 25분 자동 완료 후 타임라인에 "완료" 항목이, 진행 중 중단 후 "중단" 항목이 나타난다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    vi.useFakeTimers()

    fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
    act(() => {
      vi.advanceTimersByTime(25 * 60 * 1000)
    })

    expect(document.querySelector('.timeline')).toHaveTextContent('완료')

    fireEvent.click(screen.getByRole('button', { name: '집중 시작' }))
    act(() => {
      vi.advanceTimersByTime(1000)
    })
    fireEvent.click(screen.getByRole('button', { name: '중단' }))

    expect(document.querySelector('.timeline')).toHaveTextContent('중단')

    vi.useRealTimers()
  })

  it('새로고침 시 25분 미경과 상태로 남아있던 타이머는 남은 시간을 이어서 표시한다', () => {
    const now = new Date('2024-01-01T00:00:00.000Z')
    vi.useFakeTimers()
    vi.setSystemTime(now)

    const startedAt = new Date(now.getTime() - 10 * 60 * 1000).toISOString()
    const todo: Todo = { id: 't1', title: '우유 사기', tags: [], done: false, createdAt: startedAt }
    const initialData: StorageData = {
      schemaVersion: SCHEMA_VERSION,
      todos: [todo],
      sessions: [],
      timerState: { todoId: 't1', type: 'focus', startedAt },
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(initialData))

    render(<App />)

    expect(screen.getByText('15:00')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '중단' })).toBeInTheDocument()

    vi.useRealTimers()
  })

  it('새로고침 시 25분을 초과해 진행 중이던 타이머는 완료 처리되고 종료 알림 배너가 표시된다', () => {
    const now = new Date('2024-01-01T00:00:00.000Z')
    vi.useFakeTimers()
    vi.setSystemTime(now)

    const startedAt = new Date(now.getTime() - 26 * 60 * 1000).toISOString()
    const todo: Todo = { id: 't1', title: '우유 사기', tags: [], done: false, createdAt: startedAt }
    const initialData: StorageData = {
      schemaVersion: SCHEMA_VERSION,
      todos: [todo],
      sessions: [],
      timerState: { todoId: 't1', type: 'focus', startedAt },
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(initialData))

    render(<App />)

    expect(screen.getByRole('alert')).toHaveTextContent('집중 타이머가 종료되었습니다.')
    expect(screen.getByText('완료 1회')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '집중 시작' })).toBeInTheDocument()

    const stored = readStorage()
    expect(stored.timerState).toBeNull()
    expect(stored.sessions).toHaveLength(1)
    expect(stored.sessions[0].result).toBe('completed')

    vi.useRealTimers()
  })

  it('완료된 세션이 저장된 상태에서 렌더링해도 useTodos의 마운트 저장이 sessions/todos를 덮어쓰지 않는다', () => {
    const startedAt = new Date().toISOString()
    const todo: Todo = { id: 't1', title: '기존 할일', tags: [], done: false, createdAt: startedAt }
    const session: Session = {
      id: 's1',
      todoId: 't1',
      type: 'focus',
      startedAt,
      endedAt: startedAt,
      result: 'completed',
    }
    const initialData: StorageData = {
      schemaVersion: SCHEMA_VERSION,
      todos: [todo],
      sessions: [session],
      timerState: null,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(initialData))

    render(<App />)

    const stored = readStorage()
    expect(stored.sessions).toEqual([session])
    expect(stored.todos).toEqual([todo])
  })

  it('localStorage 데이터가 손상되어 있으면(JSON 파싱 실패) 경고 배너를 표시하고 빈 상태로 시작한다', () => {
    localStorage.setItem(STORAGE_KEY, '{ this is not valid json')

    render(<App />)

    expect(screen.getByRole('alert')).toHaveTextContent(
      '저장된 데이터를 읽는 중 문제가 발생해 빈 상태로 시작합니다.',
    )
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  })

  it('localStorage 데이터가 스키마 불일치면 경고 배너를 표시하고 빈 상태로 시작한다', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ schemaVersion: SCHEMA_VERSION, todos: 'not-an-array' }))

    render(<App />)

    expect(screen.getByRole('alert')).toHaveTextContent(
      '저장된 데이터를 읽는 중 문제가 발생해 빈 상태로 시작합니다.',
    )
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  })

  it('정상 데이터로 렌더링하면 경고 배너가 표시되지 않는다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('localStorage 쓰기가 실패하면(용량 초과 등) 쓰기 실패 경고 배너를 표시하고, 추가한 할일은 화면(메모리 상태)에 계속 표시된다', async () => {
    const user = userEvent.setup()
    render(<App />)

    vi.spyOn(localStorage, 'setItem').mockImplementation(() => {
      throw new Error('QuotaExceededError')
    })

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    expect(screen.getByRole('alert')).toHaveTextContent('저장에 실패했으나 현재 상태는 유지됩니다.')
    expect(screen.getByText('우유 사기')).toBeInTheDocument()
    expect(screen.getByRole('checkbox')).toBeInTheDocument()
  })

  it('localStorage 쓰기가 정상 동작하면 쓰기 실패 경고 배너가 표시되지 않는다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('새 할일'), '우유 사기')
    await user.click(screen.getByRole('button', { name: '추가' }))

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
