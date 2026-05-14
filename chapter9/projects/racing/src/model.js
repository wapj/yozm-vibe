const HORSES = [
  { name: "Thunder", color: "#ef4444" },
  { name: "Mystic",  color: "#3b82f6" },
  { name: "Golden",  color: "#f59e0b" },
  { name: "Emerald", color: "#10b981" },
  { name: "Shadow",  color: "#8b5cf6" },
];

export function computeOdds(meanSpeed) {
  const raw = 200 / meanSpeed;
  const clamped = Math.min(Math.max(raw, 1.5), 10.0);
  return Math.round(clamped * 100) / 100;
}

export function createHorses(rng = Math.random) {
  return HORSES.map(({ name, color }) => {
    const meanSpeed = 80 + rng() * 40;
    const odds = computeOdds(meanSpeed);
    return { name, color, meanSpeed, odds };
  });
}
