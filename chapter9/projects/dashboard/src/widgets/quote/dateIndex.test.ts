import { describe, it, expect } from 'vitest';
import { computeQuoteIndex } from './dateIndex';

describe('computeQuoteIndex', () => {
  it('기본 매핑: 2026-05-05, total=30 → 5', () => {
    // 20260505 % 30 === 5
    expect(computeQuoteIndex(new Date(2026, 4, 5), 30)).toBe(5);
  });

  it('인접 일자 인덱스 변화: 2026-05-06, total=30 → 6', () => {
    // 20260506 % 30 === 6 (전일 대비 +1)
    expect(computeQuoteIndex(new Date(2026, 4, 6), 30)).toBe(6);
  });

  it('total=1 → 항상 0', () => {
    expect(computeQuoteIndex(new Date(2026, 4, 5), 1)).toBe(0);
  });

  it('total<=0 방어: total=0 → 0', () => {
    expect(computeQuoteIndex(new Date(2026, 4, 5), 0)).toBe(0);
  });

  it('연도 경계: 2027-01-01, total=30 → 1', () => {
    // 20270101 % 30 === 1
    expect(computeQuoteIndex(new Date(2027, 0, 1), 30)).toBe(1);
  });
});
