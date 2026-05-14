export interface ScheduleItem {
  id: string
  date: string   // 'YYYY-MM-DD'
  time: string | null  // 'HH:MM' 또는 null(시각 미지정)
  title: string
  done: boolean
}
