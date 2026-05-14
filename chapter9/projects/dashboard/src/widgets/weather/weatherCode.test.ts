import { describe, it, expect } from 'vitest'
import { describeWeather } from './weatherCode'

describe('describeWeather', () => {
  it('맑음(0)을 반환한다', () => {
    expect(describeWeather(0)).toEqual({ emoji: '☀️', description: '맑음' })
  })

  it('코드 1/2/3이 각각 다른 이모지와 설명을 반환한다', () => {
    const r1 = describeWeather(1)
    const r2 = describeWeather(2)
    const r3 = describeWeather(3)
    expect(r1.emoji).not.toBe('')
    expect(r1.description).not.toBe('')
    expect(r2.emoji).not.toBe(r1.emoji)
    expect(r2.description).not.toBe(r1.description)
    expect(r3.emoji).not.toBe(r2.emoji)
    expect(r3.description).not.toBe(r2.description)
  })

  it('이슬비/비 그룹(51, 63)이 비 계열 라벨을 반환한다', () => {
    const r51 = describeWeather(51)
    const r63 = describeWeather(63)
    expect(r51.description.includes('비')).toBe(true)
    expect(r63.description.includes('비')).toBe(true)
  })

  it('눈 그룹(71)이 눈 계열 라벨을 반환한다', () => {
    expect(describeWeather(71).description.includes('눈')).toBe(true)
  })

  it('뇌우(95)가 뇌우 계열 라벨을 반환한다', () => {
    const r = describeWeather(95)
    expect(r.description.includes('뇌우') || r.description.includes('천둥')).toBe(true)
  })

  it('알 수 없는 코드(999)는 기본 폴백을 반환한다', () => {
    expect(describeWeather(999)).toEqual({ emoji: '❓', description: '알 수 없음' })
  })
})
