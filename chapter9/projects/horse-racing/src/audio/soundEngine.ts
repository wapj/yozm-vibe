/**
 * T23a: Web Audio oscillator/gain으로 효과음을 신시사이즈하는 사운드 엔진(PRD 4.8).
 * 외부 오디오 파일 없이 5종 사운드(출발 팡파르·발굽 루프·스킬 발동·피니시 함성·정산
 * 승/패)를 이름으로 재생한다. AudioContext 생성·노드 연결·스케줄링은 주입 가능한
 * AudioBackend 뒤에 감춰, jsdom 하네스에서도 mock 백엔드로 배선을 검증할 수 있다.
 *
 * 자동재생 게이팅(PRD 4.8): enable()이 호출되기 전에는 백엔드가 생성되지 않고,
 * play/startLoop 호출은 조용히 무시된다(큐잉하지 않음).
 *
 * 음소거(PRD 4.8·4.9): 모든 사운드는 마스터 게인 노드를 거쳐 destination에 연결된다.
 * 음소거 시 마스터 게인을 0으로 낮춰 실제 가청 출력을 차단한다(노드 생성 자체는
 * 막지 않아 배선 검증이 재생 시도 여부와 무관하게 가능하다).
 */
import { createWebAudioBackend } from "./webAudioBackend";
import type {
  AudioBackend,
  AudioBackendFactory,
  CreateSoundEngineOptions,
  GainLike,
  LoopSoundName,
  OneShotSoundName,
  OscillatorLike,
  SoundEngine,
} from "./types";

interface ToneSpec {
  type: OscillatorType;
  frequency: number;
  duration: number;
}

/** T23a REVIEW 갭 흡수: 테스트가 이름→톤·엔벨로프 스펙을 값으로 단언할 수 있도록 노출한다(로직 변경 없음). */
export const ATTACK_SECONDS = 0.02;

export const ONE_SHOT_TONES: Record<OneShotSoundName, ToneSpec> = {
  "start-fanfare": { type: "square", frequency: 880, duration: 0.4 },
  "skill-activation": { type: "sawtooth", frequency: 660, duration: 0.25 },
  "finish-cheer": { type: "triangle", frequency: 990, duration: 0.6 },
  "settlement-win": { type: "sine", frequency: 784, duration: 0.5 },
  "settlement-lose": { type: "sine", frequency: 220, duration: 0.5 },
};

const HOOFBEAT_TONE: Pick<ToneSpec, "type" | "frequency"> = { type: "square", frequency: 90 };

export function createSoundEngine(
  backendFactory: AudioBackendFactory = createWebAudioBackend,
  options: CreateSoundEngineOptions = {},
): SoundEngine {
  let backend: AudioBackend | null = null;
  let masterGain: GainLike | null = null;
  let muted = options.muted ?? false;
  const loopNodes = new Map<LoopSoundName, OscillatorLike>();

  function ensureBackend(): void {
    if (backend) return;
    backend = backendFactory();
    masterGain = backend.createGain();
    masterGain.gain.value = muted ? 0 : 1;
    masterGain.connect(backend.destination);
  }

  function playTone(spec: ToneSpec): void {
    if (!backend || !masterGain) return;
    const osc = backend.createOscillator();
    const envelope = backend.createGain();
    osc.type = spec.type;
    osc.frequency.value = spec.frequency;
    osc.connect(envelope);
    envelope.connect(masterGain);

    const now = backend.currentTime;
    envelope.gain.setValueAtTime(0, now);
    envelope.gain.linearRampToValueAtTime(1, now + ATTACK_SECONDS);
    envelope.gain.linearRampToValueAtTime(0, now + spec.duration);

    osc.start(now);
    osc.stop(now + spec.duration);
  }

  return {
    enable() {
      ensureBackend();
      void backend?.resume();
    },
    setMuted(next) {
      muted = next;
      if (masterGain) masterGain.gain.value = muted ? 0 : 1;
    },
    play(name) {
      if (!backend) return;
      playTone(ONE_SHOT_TONES[name]);
    },
    startLoop(name) {
      if (!backend || !masterGain || loopNodes.has(name)) return;
      const osc = backend.createOscillator();
      const envelope = backend.createGain();
      osc.type = HOOFBEAT_TONE.type;
      osc.frequency.value = HOOFBEAT_TONE.frequency;
      osc.connect(envelope);
      envelope.connect(masterGain);
      osc.start(backend.currentTime);
      loopNodes.set(name, osc);
    },
    stopLoop(name) {
      const osc = loopNodes.get(name);
      if (!osc || !backend) return;
      osc.stop(backend.currentTime);
      loopNodes.delete(name);
    },
  };
}
