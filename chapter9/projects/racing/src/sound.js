const SOUND_PARAMS = {
  start:  { freq: 880, duration: 0.15, attack: 0.01, peak: 0.2 },
  finish: { freq: 660, duration: 0.20, attack: 0.01, peak: 0.2 },
  win:    { freq: 988, duration: 0.25, attack: 0.01, peak: 0.2 },
  loss:   { freq: 220, duration: 0.30, attack: 0.01, peak: 0.2 },
};

export function createSoundEngine(audioContext) {
  let muted = false;

  function playTone(name) {
    if (!audioContext || muted) return;
    const { freq, duration, attack, peak } = SOUND_PARAMS[name];
    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(freq, audioContext.currentTime);
    gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
    gain.gain.linearRampToValueAtTime(peak, audioContext.currentTime + attack);
    gain.gain.linearRampToValueAtTime(0.0001, audioContext.currentTime + duration);
    osc.connect(gain);
    gain.connect(audioContext.destination);
    osc.start(audioContext.currentTime);
    osc.stop(audioContext.currentTime + duration);
  }

  return {
    playStart()       { playTone("start"); },
    playFinish()      { playTone("finish"); },
    playWin()         { playTone("win"); },
    playLoss()        { playTone("loss"); },
    setMuted(value)   { muted = !!value; },
    isMuted()         { return muted; },
  };
}
