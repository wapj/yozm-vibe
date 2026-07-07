import { describe, expect, it } from "vitest";
import { COMMENTARY_EVENT_TYPES, pickCommentaryLine, type CommentaryEvent } from "./commentary";

function constantRng(value: number): () => number {
  return () => value;
}

describe("pickCommentaryLine", () => {
  it("이벤트 타입은 PRD 4.6의 여섯 종을 포함한다", () => {
    expect(COMMENTARY_EVENT_TYPES.length).toBe(6);
    expect(COMMENTARY_EVENT_TYPES).toEqual([
      "start",
      "lead-change",
      "skill-activation",
      "final-stretch",
      "close-race",
      "finish",
    ]);
  });

  it("동일 rng 시퀀스는 같은 이벤트 타입에 대해 같은 문구를 선택한다", () => {
    const event: CommentaryEvent = { type: "start" };
    const first = pickCommentaryLine(event, constantRng(0));
    const second = pickCommentaryLine(event, constantRng(0));
    expect(first).toBe(second);
  });

  it("서로 다른 rng 값은 서로 다른 문구를 고를 수 있다", () => {
    const event: CommentaryEvent = { type: "start" };
    const low = pickCommentaryLine(event, constantRng(0));
    const high = pickCommentaryLine(event, constantRng(0.99));
    expect(low).not.toBe(high);
  });

  it("선두 교체 이벤트에서 말 이름이 문구에 반영된다", () => {
    const event: CommentaryEvent = { type: "lead-change", horseName: "번개질주" };
    const line = pickCommentaryLine(event, constantRng(0));
    expect(line).toContain("번개질주");
  });

  it("스킬 발동 이벤트에서 말 이름과 스킬명이 문구에 반영된다", () => {
    const event: CommentaryEvent = {
      type: "skill-activation",
      horseName: "은빛바람",
      skillName: "라스트 스퍼트",
    };
    const line = pickCommentaryLine(event, constantRng(0));
    expect(line).toContain("은빛바람");
    expect(line).toContain("라스트 스퍼트");
  });

  it("여섯 이벤트 타입 모두 예외 없이 문구를 반환한다", () => {
    for (const type of COMMENTARY_EVENT_TYPES) {
      const event: CommentaryEvent = { type, horseName: "테스트말", skillName: "테스트스킬" };
      const line = pickCommentaryLine(event, constantRng(0.5));
      expect(typeof line).toBe("string");
      expect(line.length).toBeGreaterThan(0);
    }
  });
});
