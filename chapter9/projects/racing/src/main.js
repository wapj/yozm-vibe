import { settleBet, validateBet } from "./bet.js";
import { createHorses } from "./model.js";
import { simulateRace } from "./race.js";
import { formatBalance, formatOddsLabel, formatResultMessage, applyHorsePositions, formatBetHint } from "./ui.js";
import { createSoundEngine } from "./sound.js";
import { loadBalance, saveBalance, loadMuted, saveMuted } from "./storage.js";

export function computeFramePositions(horses, elapsedSec, trackLength = 1000) {
  return horses.map(horse => {
    if (elapsedSec < 0) return 0;
    if (!Number.isFinite(horse.finishTime) || horse.finishTime <= 0) return 0;
    return Math.min(elapsedSec / horse.finishTime, 1) * trackLength;
  });
}

export function roundDelta(value) {
  return Math.round(value);
}

export function runOneRace({ balance, horses, bet }) {
  const { won, delta, winner } = settleBet({ horseIndex: bet.horseIndex, amount: bet.amount, horses });
  const roundedDelta = roundDelta(delta);
  const newBalance = balance + roundedDelta;
  return { winner, won, delta: roundedDelta, newBalance };
}

export function initApp(document, deps = {}) {
  const rng = deps.rng ?? Math.random;
  const requestAnimationFrame = deps.requestAnimationFrame ?? globalThis.requestAnimationFrame;
  const now = deps.now ?? (() => Date.now() / 1000);
  const audioContext = deps.audioContext !== undefined ? deps.audioContext : (typeof globalThis.AudioContext === "function" ? new globalThis.AudioContext() : null);
  const sound = createSoundEngine(audioContext);
  const storage = deps.storage !== undefined ? deps.storage : (typeof globalThis.localStorage !== "undefined" && typeof globalThis.localStorage.getItem === "function" ? globalThis.localStorage : null);
  sound.setMuted(loadMuted(storage));

  const state = {
    balance: deps.initialBalance ?? loadBalance(storage),
    horses: createHorses(rng),
    running: false,
    lanes: [],
  };

  function renderLaneLabels() {
    for (const horse of state.horses) {
      document.querySelector(`.lane[data-horse="${horse.name}"] .lane-label`).textContent = formatOddsLabel(horse);
    }
  }

  document.querySelector("#balance").textContent = formatBalance(state.balance);
  renderLaneLabels();
  document.querySelector("#mute-btn").textContent = sound.isMuted() ? "🔇" : "🔊";

  state.lanes = state.horses.map(horse => ({
    name: horse.name,
    horseEl: document.querySelector(`.lane[data-horse="${horse.name}"] .horse`),
  }));

  function onStart() {
    if (state.running) return;

    const hintEl = document.querySelector("#bet-hint");
    hintEl.hidden = true;
    hintEl.textContent = "";

    const selectedRadio = document.querySelector('input[name="horse"]:checked');
    if (!selectedRadio) return;
    const horseIndex = state.horses.findIndex(h => h.name === selectedRadio.value);
    if (horseIndex === -1) return;
    const amount = parseInt(document.querySelector("#bet-amount").value, 10);
    const betResult = validateBet({ horseIndex, amount, balance: state.balance });
    if (!betResult.ok) {
      hintEl.textContent = formatBetHint(betResult.error);
      hintEl.hidden = false;
      return;
    }

    document.querySelector("#start-btn").disabled = true;
    state.running = true;
    sound.playStart();

    const simulated = simulateRace(state.horses, { rng });
    const result = runOneRace({ balance: state.balance, horses: simulated, bet: { horseIndex, amount } });
    state.horses = simulated;

    const totalDuration = Math.max(...simulated.map(h => h.finishTime));
    const startTime = now();

    function finishRace() {
      const finalHorses = simulated.map(h => ({ ...h, progress: 1000 }));
      applyHorsePositions(finalHorses, state.lanes);
      sound.playFinish();
      if (result.won) sound.playWin(); else sound.playLoss();
      state.balance = result.newBalance;
      saveBalance(storage, state.balance);
      document.querySelector("#balance").textContent = formatBalance(state.balance);
      const message = formatResultMessage({ won: result.won, delta: result.delta, winner: result.winner });
      if (state.balance < 10) {
        document.querySelector("#game-over-message").textContent = message;
        document.querySelector("#game-over-modal").hidden = false;
      } else {
        document.querySelector("#result-message").textContent = message;
        document.querySelector("#result-modal").hidden = false;
      }
      state.running = false;
    }

    function frame() {
      const elapsedSec = now() - startTime;
      const positions = computeFramePositions(simulated, elapsedSec);
      const horsesWithProgress = simulated.map((h, i) => ({ ...h, progress: positions[i] }));
      applyHorsePositions(horsesWithProgress, state.lanes);

      if (elapsedSec < totalDuration) {
        requestAnimationFrame(frame);
      } else {
        finishRace();
      }
    }

    if (requestAnimationFrame) {
      requestAnimationFrame(frame);
    } else {
      finishRace();
    }
  }

  document.querySelector("#start-btn").addEventListener("click", onStart);

  function onNextRace() {
    document.querySelector("#result-modal").hidden = true;
    state.horses = createHorses(rng);
    renderLaneLabels();
    document.querySelector("#start-btn").disabled = false;
  }

  document.querySelector("#next-race-btn").addEventListener("click", onNextRace);

  function onRestart() {
    state.balance = 1000;
    saveBalance(storage, state.balance);
    document.querySelector("#balance").textContent = formatBalance(state.balance);
    document.querySelector("#result-modal").hidden = true;
    document.querySelector("#game-over-modal").hidden = true;
    state.horses = createHorses(rng);
    renderLaneLabels();
    state.lanes = state.horses.map(horse => ({
      name: horse.name,
      horseEl: document.querySelector(`.lane[data-horse="${horse.name}"] .horse`),
    }));
    document.querySelector("#start-btn").disabled = false;
  }
  document.querySelector("#restart-btn").addEventListener("click", onRestart);

  document.querySelector("#mute-btn").addEventListener("click", () => {
    sound.setMuted(!sound.isMuted());
    document.querySelector("#mute-btn").textContent = sound.isMuted() ? "🔇" : "🔊";
    saveMuted(storage, sound.isMuted());
  });
}

if (typeof document !== "undefined") { initApp(document); }
