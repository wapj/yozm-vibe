/** PRD 4.6: 경주 중 주요 이벤트를 자막형 중계 문구로 표시하기 위한 순수 모듈. */

export const COMMENTARY_EVENT_TYPES = [
  "start",
  "lead-change",
  "skill-activation",
  "final-stretch",
  "close-race",
  "finish",
] as const;

export type CommentaryEventType = (typeof COMMENTARY_EVENT_TYPES)[number];

export interface CommentaryEvent {
  type: CommentaryEventType;
  /** 선두 교체·결승선 통과 이벤트에서 대상 말 이름. */
  horseName?: string;
  /** 스킬 발동 이벤트에서 발동된 스킬 표시명. */
  skillName?: string;
}

const COMMENTARY_POOLS: Record<CommentaryEventType, string[]> = {
  start: ["게이트가 열렸습니다!", "출발! 말들이 힘차게 튀어나갑니다!"],
  "lead-change": [
    "{horseName}이(가) 선두로 치고 나갑니다!",
    "선두가 바뀝니다! {horseName}, 앞으로 나섭니다!",
  ],
  "skill-activation": [
    "{horseName}, {skillName} 발동!",
    "{horseName}이(가) {skillName}(으)로 속도를 끌어올립니다!",
  ],
  "final-stretch": [
    "이제 최종 직선 구간입니다!",
    "마지막 직선, 승부처에 들어섭니다!",
  ],
  "close-race": [
    "선두 다툼이 치열합니다, 접전입니다!",
    "간발의 차이, 결과를 예측할 수 없습니다!",
  ],
  finish: [
    "{horseName}, 결승선 통과! 우승입니다!",
    "드디어 결승선을 통과했습니다! {horseName}의 우승!",
  ],
};

function fillTemplate(template: string, event: CommentaryEvent): string {
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    const value = (event as unknown as Record<string, unknown>)[key];
    return typeof value === "string" ? value : match;
  });
}

/**
 * 이벤트 타입의 문구 풀에서 rng로 한 줄을 골라 파라미터를 치환한다.
 * rng는 0 이상 1 미만의 실수를 반환해야 한다(호출부 책임). 동일 rng 시퀀스는
 * 항상 동일 문구를 선택해 결정적이다.
 */
export function pickCommentaryLine(event: CommentaryEvent, rng: () => number): string {
  const pool = COMMENTARY_POOLS[event.type];
  const index = Math.min(pool.length - 1, Math.floor(rng() * pool.length));
  return fillTemplate(pool[index], event);
}
