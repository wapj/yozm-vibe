export function tickSpeed(meanSpeed, rng = Math.random) {
  return meanSpeed * (1 + (rng() * 2 - 1) * 0.2);
}

export function simulateRace(horses, options = {}) {
  const { rng = Math.random, dt = 0.05, trackLength = 1000 } = options;

  const positions = horses.map(() => 0);
  const finishTimes = new Array(horses.length).fill(null);
  let tick = 0;

  while (finishTimes.some(t => t === null)) {
    tick++;
    for (let i = 0; i < horses.length; i++) {
      if (finishTimes[i] !== null) continue;
      positions[i] += dt * tickSpeed(horses[i].meanSpeed, rng);
      if (positions[i] >= trackLength) {
        finishTimes[i] = tick * dt + rng() * 0.001;
      }
    }
  }

  const order = horses.map((_, i) => i).sort((a, b) => finishTimes[a] - finishTimes[b]);
  const ranks = new Array(horses.length);
  order.forEach((horseIdx, pos) => { ranks[horseIdx] = pos + 1; });

  return horses.map((horse, i) => ({
    ...horse,
    finishTime: finishTimes[i],
    rank: ranks[i],
  }));
}
