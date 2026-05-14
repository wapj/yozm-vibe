import { describe, it, expect } from 'vitest';
import { formatDateLine, formatTimeLine } from './format';

describe('formatDateLine', () => {
  it('2026-05-05 (화) 포맷', () => {
    expect(formatDateLine(new Date(2026, 4, 5, 12, 0, 0))).toBe('2026-05-05 (화)');
  });

  it('한 자리 월/일 zero-pad: 2026-01-01 (목)', () => {
    expect(formatDateLine(new Date(2026, 0, 1, 0, 0, 0))).toBe('2026-01-01 (목)');
  });

  it('요일 매핑 0~6 전체 (일~토)', () => {
    // 2026-01-04 = 일요일 (getDay()=0)
    const dates = [
      new Date(2026, 0, 4),  // 일
      new Date(2026, 0, 5),  // 월
      new Date(2026, 0, 6),  // 화
      new Date(2026, 0, 7),  // 수
      new Date(2026, 0, 8),  // 목
      new Date(2026, 0, 9),  // 금
      new Date(2026, 0, 10), // 토
    ];
    const expected = ['일', '월', '화', '수', '목', '금', '토'];
    dates.forEach((d, i) => {
      expect(formatDateLine(d)).toContain(`(${expected[i]})`);
    });
  });
});

describe('formatTimeLine', () => {
  it('zero-pad 3개 모두: 09:05:07', () => {
    expect(formatTimeLine(new Date(2026, 4, 5, 9, 5, 7))).toBe('09:05:07');
  });

  it('24시간제 자정 직전: 23:59:59', () => {
    expect(formatTimeLine(new Date(2026, 4, 5, 23, 59, 59))).toBe('23:59:59');
  });

  it('자정: 00:00:00', () => {
    expect(formatTimeLine(new Date(2026, 4, 5, 0, 0, 0))).toBe('00:00:00');
  });
});
