interface Item {
  id: string
  date: string
  time: string | null
  title: string
  done: boolean
}

export function formatToday(now: Date): string {
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function filterToday(items: Item[], today: string): Item[] {
  return items.filter(i => i.date === today)
}

export function sortByTime(items: Item[]): Item[] {
  return [...items].sort((a, b) => {
    if (a.time === null && b.time === null) return 0
    if (a.time === null) return 1
    if (b.time === null) return -1
    return a.time < b.time ? -1 : a.time > b.time ? 1 : 0
  })
}
