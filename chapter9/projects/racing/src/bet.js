export function validateBet({ horseIndex, amount, balance }) {
  if (!Number.isInteger(balance) || balance <= 0) {
    return { ok: false, error: "NO_BALANCE" };
  }
  if (!Number.isInteger(horseIndex) || horseIndex < 0 || horseIndex > 4) {
    return { ok: false, error: "INVALID_HORSE" };
  }
  if (!Number.isInteger(amount) || !Number.isFinite(amount)) {
    return { ok: false, error: "INVALID_AMOUNT" };
  }
  if (amount < 10) {
    return { ok: false, error: "BELOW_MIN" };
  }
  if (amount > balance) {
    return { ok: false, error: "EXCEEDS_BALANCE" };
  }
  return { ok: true };
}

export function settleBet({ horseIndex, amount, horses }) {
  const betHorse = horses[horseIndex];
  const winner = horses.find(h => h.rank === 1);
  if (betHorse.rank === 1) {
    const delta = amount * (betHorse.odds - 1);
    return { won: true, delta, payout: amount * betHorse.odds, winner };
  }
  return { won: false, delta: -amount, payout: 0, winner };
}
