import { describe, expect, it, vi } from "vitest";
import { ATTACK_SECONDS, ONE_SHOT_TONES, createSoundEngine } from "./soundEngine";
import type {
  AudioBackend,
  AudioNodeLike,
  AudioParamLike,
  GainLike,
  OneShotSoundName,
  OscillatorLike,
} from "./types";

function createMockAudioParam(): AudioParamLike {
  return {
    value: 0,
    setValueAtTime: vi.fn(),
    linearRampToValueAtTime: vi.fn(),
    exponentialRampToValueAtTime: vi.fn(),
  };
}

function createMockOscillator(): OscillatorLike {
  return {
    type: "sine",
    frequency: createMockAudioParam(),
    connect: vi.fn((destination: AudioNodeLike) => destination),
    start: vi.fn(),
    stop: vi.fn(),
  };
}

function createMockGain(): GainLike {
  return {
    gain: createMockAudioParam(),
    connect: vi.fn((destination: AudioNodeLike) => destination),
  };
}

/** 호출 순서·생성된 노드를 관찰할 수 있는 mock AudioBackend. */
function createMockBackend() {
  const oscillators: OscillatorLike[] = [];
  const gains: GainLike[] = [];
  const destination: AudioNodeLike = { connect: vi.fn((d: AudioNodeLike) => d) };

  const backend: AudioBackend = {
    currentTime: 0,
    destination,
    createOscillator: vi.fn(() => {
      const osc = createMockOscillator();
      oscillators.push(osc);
      return osc;
    }),
    createGain: vi.fn(() => {
      const gain = createMockGain();
      gains.push(gain);
      return gain;
    }),
    resume: vi.fn(() => Promise.resolve()),
  };

  return { backend, oscillators, gains };
}

describe("createSoundEngine", () => {
  it("enable() 이전에는 백엔드가 생성되지 않고 play/startLoop 호출이 무시된다", () => {
    const { backend, oscillators } = createMockBackend();
    const factory = vi.fn(() => backend);
    const engine = createSoundEngine(factory);

    engine.play("start-fanfare");
    engine.startLoop("hoofbeat");

    expect(factory).not.toHaveBeenCalled();
    expect(oscillators).toHaveLength(0);
  });

  it("enable()은 백엔드를 1회만 생성하고 resume을 호출한다", () => {
    const { backend } = createMockBackend();
    const factory = vi.fn(() => backend);
    const engine = createSoundEngine(factory);

    engine.enable();
    engine.enable();

    expect(factory).toHaveBeenCalledTimes(1);
    expect(backend.resume).toHaveBeenCalled();
  });

  it("활성화 이후 play(name)은 오실레이터·게인 노드를 생성·연결한 뒤 start/stop을 호출한다", () => {
    const { backend, oscillators, gains } = createMockBackend();
    const engine = createSoundEngine(() => backend);
    engine.enable();

    engine.play("start-fanfare");

    expect(oscillators).toHaveLength(1);
    // gains[0]은 enable()에서 만든 마스터 게인, gains[1]은 이번 재생의 엔벨로프.
    expect(gains).toHaveLength(2);
    const [osc] = oscillators;
    const [master, envelope] = gains;

    expect(osc.connect).toHaveBeenCalledWith(envelope);
    expect(envelope.connect).toHaveBeenCalledWith(master);
    expect(osc.start).toHaveBeenCalledTimes(1);
    expect(osc.stop).toHaveBeenCalledTimes(1);

    const connectOrder = vi.mocked(osc.connect).mock.invocationCallOrder[0];
    const startOrder = vi.mocked(osc.start).mock.invocationCallOrder[0];
    expect(connectOrder).toBeLessThan(startOrder);
  });

  it("음소거 상태에서는 마스터 게인이 0이 되어 재생 시도에도 출력이 차단되고, 해제 시 복원된다", () => {
    const { backend, gains } = createMockBackend();
    const engine = createSoundEngine(() => backend, { muted: true });

    engine.enable();
    const [master] = gains;
    expect(master.gain.value).toBe(0);

    engine.play("start-fanfare");
    expect(backend.createOscillator).toHaveBeenCalledTimes(1);

    engine.setMuted(false);
    expect(master.gain.value).toBe(1);

    engine.play("start-fanfare");
    expect(backend.createOscillator).toHaveBeenCalledTimes(2);
  });

  it("setMuted를 enable() 이전에 호출해도 활성화 시점의 마스터 게인에 반영된다", () => {
    const { backend, gains } = createMockBackend();
    const engine = createSoundEngine(() => backend, { muted: false });

    engine.setMuted(true);
    engine.enable();

    expect(gains[0].gain.value).toBe(0);
  });

  it("발굽 루프는 start/stop으로 제어되고, stop 호출이 해당 노드를 멈춘다", () => {
    const { backend, oscillators } = createMockBackend();
    const engine = createSoundEngine(() => backend);
    engine.enable();

    engine.startLoop("hoofbeat");

    expect(oscillators).toHaveLength(1);
    const [loopOsc] = oscillators;
    expect(loopOsc.start).toHaveBeenCalledTimes(1);
    expect(loopOsc.stop).not.toHaveBeenCalled();

    engine.stopLoop("hoofbeat");
    expect(loopOsc.stop).toHaveBeenCalledTimes(1);

    // 정지 이후 다시 시작하면 새 노드가 만들어진다(이전 노드 재사용 없음).
    engine.startLoop("hoofbeat");
    expect(oscillators).toHaveLength(2);
  });

  it("이미 재생 중인 루프를 다시 startLoop해도 중복 노드를 만들지 않는다", () => {
    const { backend, oscillators } = createMockBackend();
    const engine = createSoundEngine(() => backend);
    engine.enable();

    engine.startLoop("hoofbeat");
    engine.startLoop("hoofbeat");

    expect(oscillators).toHaveLength(1);
  });

  it("게이팅 이전 stopLoop 호출은 아무 효과가 없다", () => {
    const { backend, oscillators } = createMockBackend();
    const engine = createSoundEngine(() => backend);

    expect(() => engine.stopLoop("hoofbeat")).not.toThrow();
    expect(oscillators).toHaveLength(0);
  });

  it("백엔드 미주입 시 기본 팩토리를 지연 평가하며, enable 이전에는 생성 시도가 없다", () => {
    expect(() => createSoundEngine()).not.toThrow();
  });

  const REMAINING_ONE_SHOT_NAMES: OneShotSoundName[] = [
    "skill-activation",
    "finish-cheer",
    "settlement-win",
    "settlement-lose",
  ];

  it.each(REMAINING_ONE_SHOT_NAMES)(
    "%s 사운드는 ONE_SHOT_TONES 스펙대로 오실레이터를 설정하고 엔벨로프를 스케줄한다(T23a REVIEW 갭 흡수)",
    (name) => {
      const { backend, oscillators, gains } = createMockBackend();
      const engine = createSoundEngine(() => backend);
      engine.enable();

      engine.play(name);

      const [osc] = oscillators;
      const [, envelope] = gains;
      const spec = ONE_SHOT_TONES[name];

      expect(osc.type).toBe(spec.type);
      expect(osc.frequency.value).toBe(spec.frequency);
      expect(envelope.gain.setValueAtTime).toHaveBeenCalledWith(0, backend.currentTime);
      expect(envelope.gain.linearRampToValueAtTime).toHaveBeenNthCalledWith(
        1,
        1,
        backend.currentTime + ATTACK_SECONDS,
      );
      expect(envelope.gain.linearRampToValueAtTime).toHaveBeenNthCalledWith(2, 0, backend.currentTime + spec.duration);
    },
  );
});
