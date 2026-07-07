/**
 * T23a: Web Audio 사운드 엔진이 소비하는 백엔드 인터페이스. AudioContext·OscillatorNode·
 * GainNode 생성과 스케줄링을 이 인터페이스 뒤로 감싸, jsdom(Web Audio 미구현)에서도
 * mock 백엔드로 배선(호출 순서·게이팅·음소거)을 검증할 수 있게 한다.
 */

export interface AudioParamLike {
  value: number;
  setValueAtTime(value: number, time: number): unknown;
  linearRampToValueAtTime(value: number, time: number): unknown;
  exponentialRampToValueAtTime(value: number, time: number): unknown;
}

export interface AudioNodeLike {
  connect(destination: AudioNodeLike): AudioNodeLike;
}

export interface OscillatorLike extends AudioNodeLike {
  type: OscillatorType;
  frequency: AudioParamLike;
  start(when?: number): void;
  stop(when?: number): void;
}

export interface GainLike extends AudioNodeLike {
  gain: AudioParamLike;
}

export interface AudioBackend {
  readonly currentTime: number;
  readonly destination: AudioNodeLike;
  createOscillator(): OscillatorLike;
  createGain(): GainLike;
  resume(): Promise<void>;
}

export type AudioBackendFactory = () => AudioBackend;

/** 1회성 효과음. 정산은 승/패로 나뉘어 이름 기준 5종(PRD 4.8: 팡파르·스킬·함성·정산 승/패). */
export type OneShotSoundName =
  | "start-fanfare"
  | "skill-activation"
  | "finish-cheer"
  | "settlement-win"
  | "settlement-lose";

/** 경주 중 반복되는 발굽 소리. 1회성 효과음과 달리 start/stop으로 제어한다. */
export type LoopSoundName = "hoofbeat";

export interface CreateSoundEngineOptions {
  /** 생략 시 false(음소거 아님). GameSettings.muted를 그대로 소비할 수 있다. */
  muted?: boolean;
}

export interface SoundEngine {
  /** 첫 사용자 입력 이후 1회 호출해 AudioContext를 활성화한다(PRD 4.8 자동재생 정책). */
  enable(): void;
  setMuted(muted: boolean): void;
  play(name: OneShotSoundName): void;
  startLoop(name: LoopSoundName): void;
  stopLoop(name: LoopSoundName): void;
}
