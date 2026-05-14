const DAYS = ['일', '월', '화', '수', '목', '금', '토'];

export function formatDateLine(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const dow = DAYS[date.getDay()];
  return `${year}-${month}-${day} (${dow})`;
}

export function formatTimeLine(date: Date): string {
  const h = String(date.getHours()).padStart(2, '0');
  const m = String(date.getMinutes()).padStart(2, '0');
  const s = String(date.getSeconds()).padStart(2, '0');
  return `${h}:${m}:${s}`;
}
