export function positionPercent(progress, trackLength = 1000) {
  if (trackLength <= 0) return 0;
  if (progress <= 0) return 0;
  if (progress >= trackLength) return 100;
  return (progress / trackLength) * 100;
}

export function formatBalance(balance) {
  return `잔고: ${balance}`;
}

export function formatOddsLabel(horse) {
  return `${horse.name} (${horse.odds.toFixed(2)}배)`;
}

export function formatResultMessage(settle) {
  const { won, delta, winner } = settle;
  if (won) {
    return `적중! ${winner.name} 1등 — +${delta}`;
  }
  return `실패. ${winner.name} 1등 — ${delta}`;
}

export function setDisabled(elements, disabled) {
  for (const el of elements) {
    el.disabled = !!disabled;
  }
}

export function applyHorsePositions(horses, lanes, trackLength = 1000) {
  const len = Math.min(horses.length, lanes.length);
  for (let i = 0; i < len; i++) {
    lanes[i].horseEl.style.left = `${positionPercent(horses[i].progress, trackLength)}%`;
  }
}

export function formatBetHint(reason) {
  switch (reason) {
    case "NO_BALANCE": return "잔고가 부족합니다.";
    case "INVALID_HORSE": return "베팅할 말을 선택하세요.";
    case "INVALID_AMOUNT": return "베팅 금액을 정수로 입력하세요.";
    case "BELOW_MIN": return "최소 베팅 금액은 10입니다.";
    case "EXCEEDS_BALANCE": return "베팅 금액이 현재 잔고를 초과합니다.";
    default: return "베팅 정보를 확인해주세요.";
  }
}
