import { act, cleanup, render } from "@testing-library/react";
import { useEffect } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { SoundEngine } from "../audio/types";
import { createDefaultState } from "../persistence/schema";
import { createMockRenderContext } from "../render/testing";
import type { RafSource } from "../render/types";
import { createSeededRng } from "../sim/rng";
import type { RaceState, RankedRunner, RunnerState } from "../sim/types";
import { createGameStore, type GameStore } from "../store/gameStore";
import { RaceCanvas } from "./RaceCanvas";
import type { TimerSource } from "./types";
import { useGameController, type UseGameController, type UseGameControllerOptions } from "./useGameController";

/** T23b 배선 테스트가 소비하는, 호출 이름·순서·인자를 관찰할 수 있는 mock SoundEngine. */
function createMockSoundEngine(): SoundEngine {
  return {
    enable: vi.fn(),
    setMuted: vi.fn(),
    play: vi.fn(),
    startLoop: vi.fn(),
    stopLoop: vi.fn(),
  };
}

afterEach(cleanup);

function createManualTimer(): TimerSource & { flushAll(): void; pendingCount(): number } {
  let handleCounter = 0;
  const scheduled = new Map<number, () => void>();
  return {
    schedule(callback) {
      handleCounter += 1;
      scheduled.set(handleCounter, callback);
      return handleCounter;
    },
    cancel(handle) {
      scheduled.delete(handle);
    },
    flushAll() {
      const callbacks = [...scheduled.values()];
      scheduled.clear();
      callbacks.forEach((callback) => callback());
    },
    pendingCount() {
      return scheduled.size;
    },
  };
}

function Probe({
  store,
  options,
  handleRef,
}: {
  store: GameStore;
  options?: UseGameControllerOptions;
  handleRef: { current: UseGameController | null };
}) {
  const controller = useGameController(store, options);
  useEffect(() => {
    handleRef.current = controller;
  });
  return null;
}

function mount(store: GameStore, options?: UseGameControllerOptions): { current: UseGameController | null } {
  const handleRef: { current: UseGameController | null } = { current: null };
  render(<Probe store={store} options={options} handleRef={handleRef} />);
  return handleRef;
}

describe("useGameController", () => {
  it("베팅 확정→선차감→카운트다운→경주 생성→완주→정산→로비 복귀의 전체 라이프사이클을 배선한다", () => {
    const store = createGameStore(createDefaultState());
    const timer = createManualTimer();
    const handle = mount(store, { rng: createSeededRng(1), timer });

    const lobbyEntries = handle.current!.lobbyEntries;
    const betHorseId = lobbyEntries[0].horse.id;

    act(() => {
      handle.current!.handleBetConfirm(betHorseId, 500);
    });

    expect(store.getState().balance).toBe(9500);
    expect(store.getState().phase).toBe("countdown");
    expect(timer.pendingCount()).toBe(1);

    act(() => {
      timer.flushAll();
    });

    expect(store.getState().phase).toBe("racing");
    expect(handle.current!.raceState).not.toBeNull();
    // 경주 생성은 로비 스냅샷을 재사용한다: 참가자 스탯이 베팅 시점 로비 currentStats와 같다.
    const runnerStats = handle.current!.raceState!.runners.map((runner) => runner.stats);
    expect(runnerStats).toEqual(lobbyEntries.map((entry) => entry.currentStats));

    const winningRunner = handle.current!.raceState!.runners.find((runner) => runner.id === betHorseId)!;
    const otherRunners = handle.current!.raceState!.runners.filter((runner) => runner.id !== betHorseId);

    const finishedState = {
      runners: [
        { ...winningRunner, position: 1000 },
        ...otherRunners.map((runner) => ({ ...runner, position: 500 })),
      ],
      elapsedTime: 20,
      finished: true,
    };
    const rankings = [
      { id: betHorseId, position: 1000, rank: 1 },
      ...otherRunners.map((runner) => ({ id: runner.id, position: 500, rank: 2 })),
    ];

    act(() => {
      handle.current!.handleFrame(finishedState, rankings);
    });

    expect(store.getState().phase).toBe("settlement");
    const betOdds = lobbyEntries.find((entry) => entry.horse.id === betHorseId)!.odds;
    const expectedPayout = Math.round(500 * betOdds);
    expect(handle.current!.settlement).toEqual({ won: true, payout: expectedPayout, balanceChange: expectedPayout });
    expect(store.getState().balance).toBe(9500 + expectedPayout);
    expect(handle.current!.commentaryMessages.length).toBeGreaterThan(0);

    // T21: 완주 순위로 출전마 전적(records)이 갱신된다(우승마 wins 증가, 나머지 racesRun만 증가).
    expect(store.getState().records[betHorseId]).toEqual({ racesRun: 1, wins: 1, recentResults: [1] });
    for (const runner of otherRunners) {
      expect(store.getState().records[runner.id]).toEqual({ racesRun: 1, wins: 0, recentResults: [2] });
    }

    act(() => {
      timer.flushAll();
    });

    expect(store.getState().phase).toBe("lobby");
    expect(handle.current!.raceState).toBeNull();
    expect(handle.current!.settlement).toEqual({ won: true, payout: expectedPayout, balanceChange: expectedPayout });
  });

  it("미적중이면 잔고 증감 없이 정산되고 로비로 복귀한다", () => {
    const store = createGameStore(createDefaultState());
    const timer = createManualTimer();
    const handle = mount(store, { rng: createSeededRng(1), timer });

    const lobbyEntries = handle.current!.lobbyEntries;
    const betHorseId = lobbyEntries[0].horse.id;
    const otherHorseId = lobbyEntries[1].horse.id;

    act(() => {
      handle.current!.handleBetConfirm(betHorseId, 500);
    });
    act(() => {
      timer.flushAll();
    });

    const balanceAfterBet = store.getState().balance;
    const runners = handle.current!.raceState!.runners;

    const finishedState = {
      runners: runners.map((runner) =>
        runner.id === otherHorseId ? { ...runner, position: 1000 } : { ...runner, position: 400 },
      ),
      elapsedTime: 18,
      finished: true,
    };
    const rankings = runners.map((runner) => ({
      id: runner.id,
      position: runner.id === otherHorseId ? 1000 : 400,
      rank: runner.id === otherHorseId ? 1 : 2,
    }));

    act(() => {
      handle.current!.handleFrame(finishedState, rankings);
    });

    expect(handle.current!.settlement).toEqual({ won: false, payout: 0, balanceChange: 0 });
    expect(store.getState().balance).toBe(balanceAfterBet);
  });

  it("완주 프레임은 한 번만 정산 배선을 트리거한다(중복 dispatch 없음)", () => {
    const store = createGameStore(createDefaultState());
    const timer = createManualTimer();
    const handle = mount(store, { rng: createSeededRng(1), timer });

    const betHorseId = handle.current!.lobbyEntries[0].horse.id;
    act(() => {
      handle.current!.handleBetConfirm(betHorseId, 100);
    });
    act(() => {
      timer.flushAll();
    });

    const runners = handle.current!.raceState!.runners;
    const finishedState = {
      runners: runners.map((runner) =>
        runner.id === betHorseId ? { ...runner, position: 1000 } : { ...runner, position: 300 },
      ),
      elapsedTime: 20,
      finished: true,
    };
    const rankings = runners.map((runner) => ({
      id: runner.id,
      position: runner.id === betHorseId ? 1000 : 300,
      rank: runner.id === betHorseId ? 1 : 2,
    }));

    const recordRaceResultSpy = vi.spyOn(store, "recordRaceResult");

    act(() => {
      handle.current!.handleFrame(finishedState, rankings);
      handle.current!.handleFrame(finishedState, rankings);
    });

    expect(store.getState().phase).toBe("settlement");
    expect(timer.pendingCount()).toBe(1); // 로비 복귀 타이머 1개만 예약된다(정산이 중복 실행되지 않음).
    expect(recordRaceResultSpy).toHaveBeenCalledTimes(1); // T21: 전적 갱신도 완주당 정확히 1회만 호출된다.
  });

  it("탭 자동 일시정지 실연결: 실 document visibility 소스에서 racing 중 hidden→store paused=true, 복귀 시 paused=false", () => {
    const store = createGameStore(createDefaultState());
    const timer = createManualTimer();
    const handle = mount(store, { rng: createSeededRng(1), timer });

    const betHorseId = handle.current!.lobbyEntries[0].horse.id;
    act(() => {
      handle.current!.handleBetConfirm(betHorseId, 100);
      timer.flushAll();
    });

    expect(store.getState().phase).toBe("racing");

    const raf: RafSource = {
      request: () => 1,
      cancel: () => {},
    };
    const ctx = createMockRenderContext();

    const originalDescriptor = Object.getOwnPropertyDescriptor(Document.prototype, "hidden");
    let hidden = false;
    Object.defineProperty(document, "hidden", { configurable: true, get: () => hidden });

    try {
      render(
        <RaceCanvas
          initialState={handle.current!.raceState!}
          horses={handle.current!.horses}
          machine={handle.current!.machine}
          getContext={() => ctx}
          raf={raf}
        />,
      );

      expect(store.getState().paused).toBe(false);

      hidden = true;
      act(() => {
        document.dispatchEvent(new Event("visibilitychange"));
      });
      expect(store.getState().paused).toBe(true);

      hidden = false;
      act(() => {
        document.dispatchEvent(new Event("visibilitychange"));
      });
      expect(store.getState().paused).toBe(false);
    } finally {
      if (originalDescriptor) {
        Object.defineProperty(document, "hidden", originalDescriptor);
      } else {
        delete (document as unknown as Record<string, unknown>).hidden;
      }
    }
  });

  it("로비 재진입 시 로비 스냅샷을 다시 굴린다", () => {
    const store = createGameStore(createDefaultState());
    const timer = createManualTimer();
    let callCount = 0;
    const rng = () => {
      callCount += 1;
      return createSeededRng(callCount)();
    };
    const handle = mount(store, { rng, timer });

    const firstLobbyEntries = handle.current!.lobbyEntries;
    const betHorseId = firstLobbyEntries[0].horse.id;

    act(() => {
      handle.current!.handleBetConfirm(betHorseId, 100);
      timer.flushAll();
    });

    const runners = handle.current!.raceState!.runners;
    const finishedState = {
      runners: runners.map((runner) => ({ ...runner, position: runner.id === betHorseId ? 1000 : 300 })),
      elapsedTime: 20,
      finished: true,
    };
    const rankings = runners.map((runner) => ({
      id: runner.id,
      position: runner.id === betHorseId ? 1000 : 300,
      rank: runner.id === betHorseId ? 1 : 2,
    }));

    act(() => {
      handle.current!.handleFrame(finishedState, rankings);
      timer.flushAll();
    });

    expect(store.getState().phase).toBe("lobby");
    const secondLobbyEntries = handle.current!.lobbyEntries;
    expect(secondLobbyEntries).not.toBe(firstLobbyEntries);
    expect(secondLobbyEntries.map((entry) => entry.currentStats)).not.toEqual(
      firstLobbyEntries.map((entry) => entry.currentStats),
    );
  });

  describe("T23b: 게임 이벤트에 사운드 연결 + 음소거 실반영 배선", () => {
    function buildRankings(runners: RunnerState[], winnerId: string): RankedRunner[] {
      return runners.map((runner) => ({
        id: runner.id,
        position: runner.id === winnerId ? 1000 : 300,
        rank: runner.id === winnerId ? 1 : 2,
      }));
    }

    it("베팅 확정 시 enable()이 호출되고, enable 호출이 첫 사운드 재생보다 앞선다", () => {
      const store = createGameStore(createDefaultState());
      const timer = createManualTimer();
      const sound = createMockSoundEngine();
      const handle = mount(store, { rng: createSeededRng(1), timer, sound });

      const betHorseId = handle.current!.lobbyEntries[0].horse.id;

      act(() => {
        handle.current!.handleBetConfirm(betHorseId, 100);
      });
      expect(sound.enable).toHaveBeenCalledTimes(1);

      act(() => {
        timer.flushAll();
      });

      const runners = handle.current!.raceState!.runners;
      const firstFrame: RaceState = { runners, elapsedTime: 0, finished: false };
      act(() => {
        handle.current!.handleFrame(firstFrame, buildRankings(runners, betHorseId));
      });

      expect(sound.play).toHaveBeenCalledWith("start-fanfare");
      expect(sound.startLoop).toHaveBeenCalledWith("hoofbeat");

      const enableOrder = vi.mocked(sound.enable).mock.invocationCallOrder[0];
      const playOrder = vi.mocked(sound.play).mock.invocationCallOrder[0];
      expect(enableOrder).toBeLessThan(playOrder);
    });

    it("스킬 발동 이벤트에서 skill-activation 사운드가 재생된다", () => {
      const store = createGameStore(createDefaultState());
      const timer = createManualTimer();
      const sound = createMockSoundEngine();
      const handle = mount(store, { rng: createSeededRng(1), timer, sound });

      const betHorseId = handle.current!.lobbyEntries[0].horse.id;
      act(() => {
        handle.current!.handleBetConfirm(betHorseId, 100);
        timer.flushAll();
      });

      const runners = handle.current!.raceState!.runners;
      const firstFrame: RaceState = { runners, elapsedTime: 0, finished: false };
      act(() => {
        handle.current!.handleFrame(firstFrame, buildRankings(runners, betHorseId));
      });

      const skillRunnerId = runners[0].id;
      const secondFrame: RaceState = {
        runners: runners.map((runner) =>
          runner.id === skillRunnerId ? { ...runner, skillActivated: true, skillActivatedAt: 1 } : runner,
        ),
        elapsedTime: 1,
        finished: false,
      };
      act(() => {
        handle.current!.handleFrame(secondFrame, buildRankings(runners, betHorseId));
      });

      expect(sound.play).toHaveBeenCalledWith("skill-activation");
    });

    it("완주 시 finish-cheer·발굽 루프 정지가 일어나고, 적중이면 settlement-win이 재생된다", () => {
      const store = createGameStore(createDefaultState());
      const timer = createManualTimer();
      const sound = createMockSoundEngine();
      const handle = mount(store, { rng: createSeededRng(1), timer, sound });

      const betHorseId = handle.current!.lobbyEntries[0].horse.id;
      act(() => {
        handle.current!.handleBetConfirm(betHorseId, 100);
        timer.flushAll();
      });

      const runners = handle.current!.raceState!.runners;
      const rankings = buildRankings(runners, betHorseId);
      // deriveRaceEvents는 prevFrameRef===null인 첫 호출을 "start"로만 취급하므로(T20b),
      // "finish" 이벤트를 끌어내려면 완주 이전의 프레임을 먼저 한 번 거쳐야 한다.
      const runningState: RaceState = { runners, elapsedTime: 0, finished: false };
      act(() => {
        handle.current!.handleFrame(runningState, rankings);
      });

      const finishedState: RaceState = {
        runners: runners.map((runner) => ({ ...runner, position: runner.id === betHorseId ? 1000 : 300 })),
        elapsedTime: 20,
        finished: true,
      };

      act(() => {
        handle.current!.handleFrame(finishedState, rankings);
      });

      expect(sound.play).toHaveBeenCalledWith("finish-cheer");
      expect(sound.stopLoop).toHaveBeenCalledWith("hoofbeat");
      expect(sound.play).toHaveBeenCalledWith("settlement-win");
      expect(sound.play).not.toHaveBeenCalledWith("settlement-lose");
    });

    it("미적중이면 settlement-lose가 재생된다", () => {
      const store = createGameStore(createDefaultState());
      const timer = createManualTimer();
      const sound = createMockSoundEngine();
      const handle = mount(store, { rng: createSeededRng(1), timer, sound });

      const lobbyEntries = handle.current!.lobbyEntries;
      const betHorseId = lobbyEntries[0].horse.id;
      const otherHorseId = lobbyEntries[1].horse.id;
      act(() => {
        handle.current!.handleBetConfirm(betHorseId, 100);
        timer.flushAll();
      });

      const runners = handle.current!.raceState!.runners;
      const rankings = buildRankings(runners, otherHorseId);
      const finishedState: RaceState = {
        runners: runners.map((runner) => ({ ...runner, position: runner.id === otherHorseId ? 1000 : 300 })),
        elapsedTime: 20,
        finished: true,
      };

      act(() => {
        handle.current!.handleFrame(finishedState, rankings);
      });

      expect(sound.play).toHaveBeenCalledWith("settlement-lose");
      expect(sound.play).not.toHaveBeenCalledWith("settlement-win");
    });

    it("settings.muted 변경(초기값 포함)이 setMuted 호출로 실반영된다", () => {
      const sound = createMockSoundEngine();
      const handleRef: { current: UseGameController | null } = { current: null };

      const mutedFalseStore = createGameStore(createDefaultState());
      const { rerender } = render(<Probe store={mutedFalseStore} options={{ sound }} handleRef={handleRef} />);

      expect(sound.setMuted).toHaveBeenNthCalledWith(1, false);

      const mutedTrueSaved = { ...createDefaultState(), settings: { ...createDefaultState().settings, muted: true } };
      const mutedTrueStore = createGameStore(mutedTrueSaved);
      rerender(<Probe store={mutedTrueStore} options={{ sound }} handleRef={handleRef} />);

      expect(sound.setMuted).toHaveBeenNthCalledWith(2, true);

      rerender(<Probe store={mutedFalseStore} options={{ sound }} handleRef={handleRef} />);

      expect(sound.setMuted).toHaveBeenNthCalledWith(3, false);
    });
  });
});
