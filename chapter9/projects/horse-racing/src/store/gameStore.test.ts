import { describe, expect, it } from "vitest";
import { createDefaultState } from "../persistence/schema";
import { createGameStore } from "./gameStore";

describe("gameStore", () => {
  it("초기 상태는 lobby이며 저장된 잔고·전적·설정·말 카탈로그를 반영한다", () => {
    const saved = { ...createDefaultState(), balance: 3000, bankruptcyCount: 1 };
    const store = createGameStore(saved);
    const state = store.getState();

    expect(state.phase).toBe("lobby");
    expect(state.paused).toBe(false);
    expect(state.balance).toBe(3000);
    expect(state.bankruptcyCount).toBe(1);
    expect(state.horses).toHaveLength(saved.settings.horseCount);
  });

  it("정의된 순서로 전이하며 구독자에게 알린다", () => {
    const store = createGameStore(createDefaultState());
    const seenPhases: string[] = [];
    store.subscribe((state) => seenPhases.push(state.phase));

    store.dispatch("START_COUNTDOWN");
    store.dispatch("START_RACE");
    store.dispatch("FINISH");
    store.dispatch("SETTLE");
    store.dispatch("RESET");

    expect(seenPhases).toEqual(["countdown", "racing", "finish", "settlement", "lobby"]);
  });

  it("정의되지 않은 전이는 무시된다", () => {
    const store = createGameStore(createDefaultState());
    store.dispatch("FINISH");
    expect(store.getState().phase).toBe("lobby");
  });

  it("PAUSE/RESUME은 경주 중에만 유효하다", () => {
    const store = createGameStore(createDefaultState());

    store.dispatch("PAUSE");
    expect(store.getState().paused).toBe(false);

    store.dispatch("START_COUNTDOWN");
    store.dispatch("START_RACE");
    store.dispatch("PAUSE");
    expect(store.getState().paused).toBe(true);

    store.dispatch("RESUME");
    expect(store.getState().paused).toBe(false);
  });

  it("잔고가 최소 베팅액(100) 미만이 되면 기본 잔고로 재충전되고 파산 횟수가 1 증가한다", () => {
    const saved = { ...createDefaultState(), balance: 150 };
    const store = createGameStore(saved);

    store.adjustBalance(-100);

    const state = store.getState();
    expect(state.balance).toBe(10000);
    expect(state.bankruptcyCount).toBe(1);
  });

  it("잔고가 최소 베팅액 이상이면 파산 처리되지 않는다", () => {
    const store = createGameStore(createDefaultState());
    store.adjustBalance(-500);

    const state = store.getState();
    expect(state.balance).toBe(9500);
    expect(state.bankruptcyCount).toBe(0);
  });

  it("파산 경계값: 잔고가 정확히 MIN_BET_AMOUNT(100)이면 파산 처리되지 않는다", () => {
    const saved = { ...createDefaultState(), balance: 200 };
    const store = createGameStore(saved);
    store.adjustBalance(-100);

    const state = store.getState();
    expect(state.balance).toBe(100);
    expect(state.bankruptcyCount).toBe(0);
  });

  it("파산 경계값: 잔고가 99가 되면 파산 처리되어 기본 잔고로 재충전되고 파산 횟수가 1 증가한다", () => {
    const saved = { ...createDefaultState(), balance: 200 };
    const store = createGameStore(saved);
    store.adjustBalance(-101);

    const state = store.getState();
    expect(state.balance).toBe(10000);
    expect(state.bankruptcyCount).toBe(1);
  });

  it("adjustBalance 호출 시 구독자에게 변경된 잔고가 emit된다", () => {
    const store = createGameStore(createDefaultState());
    const seenBalances: number[] = [];
    store.subscribe((state) => seenBalances.push(state.balance));

    store.adjustBalance(-300);
    store.adjustBalance(500);

    expect(seenBalances).toEqual([9700, 10200]);
  });

  it("방어 복사: 전달한 saved.records/saved.settings 객체를 그대로 참조하지 않는다", () => {
    const saved = createDefaultState();
    saved.records["horse-1"] = { racesRun: 2, wins: 1, recentResults: [1, 3] };

    const store = createGameStore(saved);
    store.dispatch("START_COUNTDOWN");
    store.dispatch("START_RACE");
    store.adjustBalance(-1000);

    const state = store.getState();
    expect(state.records).not.toBe(saved.records);
    expect(state.settings).not.toBe(saved.settings);

    saved.records["horse-2"] = { racesRun: 5, wins: 2, recentResults: [1] };
    expect(store.getState().records["horse-2"]).toBeUndefined();

    saved.settings.muted = true;
    expect(store.getState().settings.muted).toBe(false);
  });

  it("recordRaceResult 호출 시 완주 순위로 전적이 갱신되고, 잔고·파산·설정 등 다른 상태는 변경되지 않는다", () => {
    const saved = { ...createDefaultState(), balance: 5000, bankruptcyCount: 2 };
    saved.records["horse-1"] = { racesRun: 2, wins: 1, recentResults: [1, 3] };
    const store = createGameStore(saved);
    const settingsBefore = store.getState().settings;

    store.recordRaceResult([
      { id: "horse-1", position: 1000, rank: 1 },
      { id: "horse-2", position: 800, rank: 2 },
    ]);

    const state = store.getState();
    expect(state.records["horse-1"]).toEqual({ racesRun: 3, wins: 2, recentResults: [1, 1, 3] });
    expect(state.records["horse-2"]).toEqual({ racesRun: 1, wins: 0, recentResults: [2] });
    expect(state.balance).toBe(5000);
    expect(state.bankruptcyCount).toBe(2);
    expect(state.settings).toBe(settingsBefore);
    expect(state.phase).toBe("lobby");
  });

  it("recordRaceResult 호출 시 구독자에게 갱신된 records가 emit된다", () => {
    const store = createGameStore(createDefaultState());
    const seenRecords: Record<string, unknown>[] = [];
    store.subscribe((state) => seenRecords.push(state.records));

    store.recordRaceResult([{ id: "horse-1", position: 1000, rank: 1 }]);

    expect(seenRecords).toHaveLength(1);
    expect(seenRecords[0]["horse-1"]).toEqual({ racesRun: 1, wins: 1, recentResults: [1] });
  });

  it("구독 해제 후에는 알림을 받지 않는다", () => {
    const store = createGameStore(createDefaultState());
    const seenPhases: string[] = [];
    const unsubscribe = store.subscribe((state) => seenPhases.push(state.phase));

    store.dispatch("START_COUNTDOWN");
    unsubscribe();
    store.dispatch("START_RACE");

    expect(seenPhases).toEqual(["countdown"]);
  });
});
