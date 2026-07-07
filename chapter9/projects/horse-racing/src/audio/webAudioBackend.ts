/**
 * 브라우저 AudioContext를 AudioBackend로 위임하는 기본 구현. createSoundEngine이
 * enable() 호출 시점에만 이 팩토리를 실행해, AudioContext 생성이 자동재생 게이팅보다
 * 먼저 일어나지 않게 한다(PRD 4.8). jsdom은 AudioContext를 구현하지 않으므로 이 파일은
 * 실브라우저 `npm run dev` 수동 확인 몫이며 vitest 대상이 아니다.
 */
import type { AudioBackend } from "./types";

export function createWebAudioBackend(): AudioBackend {
  const ctx = new AudioContext();
  return {
    get currentTime() {
      return ctx.currentTime;
    },
    destination: ctx.destination,
    createOscillator: () => ctx.createOscillator(),
    createGain: () => ctx.createGain(),
    resume: () => ctx.resume(),
  };
}
