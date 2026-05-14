export interface WeatherLabel {
  emoji: string
  description: string
}

export function describeWeather(code: number): WeatherLabel {
  if (code === 0) return { emoji: '☀️', description: '맑음' }
  if (code === 1) return { emoji: '🌤️', description: '대체로 맑음' }
  if (code === 2) return { emoji: '⛅', description: '부분적 흐림' }
  if (code === 3) return { emoji: '☁️', description: '흐림' }
  if (code === 45 || code === 48) return { emoji: '🌫️', description: '안개' }
  if (code >= 51 && code <= 55) return { emoji: '🌧️', description: '이슬비' }
  if (code >= 56 && code <= 67) return { emoji: '🌧️', description: '비' }
  if (code >= 71 && code <= 77) return { emoji: '🌨️', description: '눈' }
  if (code >= 80 && code <= 82) return { emoji: '🌦️', description: '소나기' }
  if (code >= 83 && code <= 86) return { emoji: '🌦️', description: '소낙눈' }
  if (code >= 95 && code <= 99) return { emoji: '⛈️', description: '뇌우' }
  return { emoji: '❓', description: '알 수 없음' }
}
