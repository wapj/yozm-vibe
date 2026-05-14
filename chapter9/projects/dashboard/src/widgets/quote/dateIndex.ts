export function computeQuoteIndex(date: Date, total: number): number {
  if (total <= 0) return 0;
  const key = date.getFullYear() * 10000 + (date.getMonth() + 1) * 100 + date.getDate();
  return key % total;
}
