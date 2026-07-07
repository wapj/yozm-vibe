import { STAT_KEYS, type HorseProfile, type SkillDefinition, type Stats } from "./types";

/** 스탯 하한. 0 이하 스탯이 도메인 모듈(승률 추정 등)에 유입되어 NaN을 만드는 경로를 차단한다. */
export const MIN_BASE_STAT = 1;

/** 5종 스킬의 도메인 정의(id·한글 표시명·설명). 렌더 레이어는 이 표시명을 그대로 소비하고 문자열을 하드코딩하지 않는다. */
export const SKILL_CATALOG: SkillDefinition[] = [
  { id: "last-spurt", name: "라스트 스퍼트", description: "종반 구간에서 대폭 가속한다." },
  { id: "slipstream", name: "슬립스트림", description: "앞 말 바로 뒤에 있을 때 가속이 지속된다." },
  { id: "start-dash", name: "스타트 대시", description: "출발 직후 폭발적으로 가속한다." },
  { id: "shake-off", name: "흔들기", description: "주변 말들을 일시적으로 감속시킨다." },
  { id: "zone", name: "무아지경", description: "일정 시간 스태미나 소모 없이 최고 속도를 유지한다." },
];

interface HorseTemplate {
  name: string;
  color: string;
  personality: string;
  baseStats: Stats;
  skillIndex: number;
}

/** 최대 8마리까지 지원하는 고정 말 템플릿. 앞에서부터 count만큼 잘라 카탈로그를 만든다. */
const HORSE_TEMPLATES: HorseTemplate[] = [
  {
    name: "번개질주",
    color: "#e63946",
    personality: "저돌적",
    baseStats: { speed: 88, stamina: 60, burst: 70, luck: 45 },
    skillIndex: 2,
  },
  {
    name: "은빛바람",
    color: "#457b9d",
    personality: "냉정함",
    baseStats: { speed: 75, stamina: 82, burst: 55, luck: 50 },
    skillIndex: 0,
  },
  {
    name: "질풍노도",
    color: "#2a9d8f",
    personality: "변덕스러움",
    baseStats: { speed: 70, stamina: 65, burst: 85, luck: 55 },
    skillIndex: 1,
  },
  {
    name: "먹구름",
    color: "#3d3d3d",
    personality: "음흉함",
    baseStats: { speed: 65, stamina: 70, burst: 60, luck: 75 },
    skillIndex: 3,
  },
  {
    name: "황금갈기",
    color: "#f4a261",
    personality: "느긋함",
    baseStats: { speed: 60, stamina: 90, burst: 50, luck: 60 },
    skillIndex: 4,
  },
  {
    name: "칠흑의별",
    color: "#1d3557",
    personality: "고독함",
    baseStats: { speed: 80, stamina: 55, burst: 65, luck: 65 },
    skillIndex: 0,
  },
  {
    name: "새벽안개",
    color: "#a8dadc",
    personality: "신중함",
    baseStats: { speed: 72, stamina: 72, burst: 58, luck: 58 },
    skillIndex: 1,
  },
  {
    name: "폭풍의아이",
    color: "#e76f51",
    personality: "즉흥적",
    baseStats: { speed: 68, stamina: 68, burst: 78, luck: 48 },
    skillIndex: 2,
  },
];

function clampStats(stats: Stats): Stats {
  const clamped = {} as Stats;
  for (const key of STAT_KEYS) {
    clamped[key] = Math.max(MIN_BASE_STAT, stats[key]);
  }
  return clamped;
}

/**
 * 출전마 카탈로그를 생성한다. id는 `horse-{순번}` 형식으로 부여하며,
 * 저장 계층의 `SavedState.records` 키로 그대로 사용할 수 있다.
 * count는 템플릿 개수(8) 이하, 1 이상으로 클램프한다.
 */
export function createHorseCatalog(count: number): HorseProfile[] {
  const clamped = Math.min(HORSE_TEMPLATES.length, Math.max(1, Math.floor(count)));
  return HORSE_TEMPLATES.slice(0, clamped).map((template, index) => ({
    id: `horse-${index + 1}`,
    number: index + 1,
    name: template.name,
    color: template.color,
    personality: template.personality,
    baseStats: clampStats(template.baseStats),
    skill: SKILL_CATALOG[template.skillIndex],
  }));
}
