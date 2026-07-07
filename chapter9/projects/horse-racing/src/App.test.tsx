import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import App from "./App";
import { createDefaultState, STORAGE_KEY } from "./persistence/schema";
import { createPersistence, type StorageDriver } from "./persistence/storage";
import { createMockRenderContext } from "./render/testing";
import type { RafSource, RenderContext } from "./render/types";
import { createSeededRng } from "./sim/rng";
import { createGameStore } from "./store/gameStore";
import { CommentaryFeed } from "./ui/CommentaryFeed";
import { RaceCanvas } from "./ui/RaceCanvas";
import type { TimerSource } from "./ui/types";
import { useGameController, type UseGameController, type UseGameControllerOptions } from "./ui/useGameController";

afterEach(cleanup);

function createInMemoryDriver(): StorageDriver & { data: Record<string, string> } {
  const data: Record<string, string> = {};
  return {
    data,
    getItem: (key) => data[key] ?? null,
    setItem: (key, value) => {
      data[key] = value;
    },
  };
}

function createManualTimer(): TimerSource & { flushAll(): void } {
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
  };
}

/** RaceCanvas.test.tsx·loop.test.ts와 동일한 가짜 raf: 테스트가 프레임 타임스탬프를 직접 통제한다. */
function createManualRaf(): RafSource & { tick(timeMs: number): void } {
  let pending: ((timeMs: number) => void) | null = null;
  let handleCounter = 0;
  return {
    request(callback) {
      pending = callback;
      return ++handleCounter;
    },
    cancel() {
      pending = null;
    },
    tick(timeMs: number) {
      const callback = pending;
      pending = null;
      callback?.(timeMs);
    },
  };
}

const createMockCtx = createMockRenderContext;

/** 경주를 완주까지 구동한다(500ms 단위로 60초 분량, 완주 후 tick은 안전하게 무해하다). */
function driveRaceToCompletion(raf: ReturnType<typeof createManualRaf>): void {
  raf.tick(0);
  for (let elapsed = 500; elapsed <= 60000; elapsed += 500) {
    raf.tick(elapsed);
  }
}

describe("App", () => {
  it("제목과 초기 잔고를 렌더링한다", () => {
    render(<App />);
    expect(screen.getByText("브라우저 경마 베팅 게임")).toBeTruthy();
    expect(screen.getByText("잔고: 10,000원")).toBeTruthy();
  });

  it("저장소가 비어 있으면(status=empty) 저장 비활성 배너를 노출하지 않는다", () => {
    const emptyDriver: StorageDriver = {
      getItem: () => null,
      setItem: () => {},
    };

    render(<App driver={emptyDriver} />);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("저장된 데이터가 정상이면(status=ok) 저장 비활성 배너를 노출하지 않는다", () => {
    const savedJson = JSON.stringify(createDefaultState());
    const okDriver: StorageDriver = {
      getItem: () => savedJson,
      setItem: () => {},
    };

    render(<App driver={okDriver} />);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("저장소 접근이 실패하면(status=disabled) 저장 비활성 배너를 노출한다", () => {
    const throwingDriver: StorageDriver = {
      getItem: () => {
        throw new Error("storage unavailable");
      },
      setItem: () => {
        throw new Error("storage unavailable");
      },
    };

    render(<App driver={throwingDriver} />);
    expect(screen.getByRole("alert")).toBeTruthy();
  });

  describe("T15 이월 메모 해소: props.store 주입 시에도 실제 저장 상태가 배너에 반영된다", () => {
    it("store를 주입해도 driver가 실패하면 저장 비활성 배너를 노출한다", () => {
      const store = createGameStore(createDefaultState());
      const throwingDriver: StorageDriver = {
        getItem: () => {
          throw new Error("storage unavailable");
        },
        setItem: () => {
          throw new Error("storage unavailable");
        },
      };

      render(<App store={store} driver={throwingDriver} />);
      expect(screen.getByRole("alert")).toBeTruthy();
    });

    it("store를 주입하고 driver가 정상이면 저장 비활성 배너를 노출하지 않는다", () => {
      const store = createGameStore(createDefaultState());
      const okDriver: StorageDriver = {
        getItem: () => null,
        setItem: () => {},
      };

      render(<App store={store} driver={okDriver} />);
      expect(screen.queryByRole("alert")).toBeNull();
    });
  });

  describe("화면 컴포지션: phase에 따라 로비/경주/정산 화면이 조립된다", () => {
    it("lobby: 말 카드 목록·베팅 패널·잔고·설정이 함께 렌더된다", () => {
      const driver = createInMemoryDriver();
      render(<App driver={driver} />);

      expect(screen.getAllByRole("article")).toHaveLength(5);
      expect(screen.getByLabelText("베팅 패널")).toBeTruthy();
      expect(screen.getByLabelText("잔고 정보")).toBeTruthy();
      expect(screen.getByLabelText("설정")).toBeTruthy();
      expect(document.querySelector("canvas")).toBeNull();
    });

    it("BetPanel.onConfirm이 handleBetConfirm에 연결되어 선차감·countdown 전이가 일어나고, raceState 준비 전에는 RaceCanvas가 미마운트된다", () => {
      const driver = createInMemoryDriver();
      const timer = createManualTimer();
      render(<App driver={driver} controllerOptions={{ timer, rng: createSeededRng(1) }} />);

      fireEvent.click(screen.getByRole("radio", { name: "1번 번개질주" }));
      fireEvent.click(screen.getByText("100"));
      fireEvent.click(screen.getByText("베팅 확정"));

      expect(screen.getByText("잔고: 9,900원")).toBeTruthy();
      expect(screen.queryByLabelText("베팅 패널")).toBeNull();
      expect(screen.getByLabelText("실황 중계")).toBeTruthy();
      expect(document.querySelector("canvas")).toBeNull(); // countdown 중 raceState===null

      act(() => {
        timer.flushAll();
      });

      expect(document.querySelector("canvas")).not.toBeNull(); // racing 진입 후 RaceCanvas 마운트
    });

    it("countdown→racing→finish→settlement까지 화면이 전환되며 SettlementResult가 적중/지급액/정산 후 잔고를 렌더링한다", () => {
      const driver = createInMemoryDriver();
      const timer = createManualTimer();
      const raf = createManualRaf();
      const ctx = createMockCtx();

      render(
        <App
          driver={driver}
          controllerOptions={{ timer, rng: createSeededRng(3) }}
          raceCanvasOverrides={{ getContext: () => ctx, raf, rng: createSeededRng(3) }}
        />,
      );

      fireEvent.click(screen.getByRole("radio", { name: "1번 번개질주" }));
      fireEvent.click(screen.getByText("100"));
      fireEvent.click(screen.getByText("베팅 확정"));

      act(() => {
        timer.flushAll();
      });

      act(() => {
        driveRaceToCompletion(raf);
      });

      expect(screen.getByLabelText("정산 결과")).toBeTruthy();
      // 정산 중에도 완주 연출(피니시 배너·폭죽)이 보이도록 경주 화면을 유지한다.
      expect(screen.getByLabelText("경주 화면")).toBeTruthy();
      expect(screen.queryByLabelText("베팅 패널")).toBeNull();
      expect(screen.getByText(/^(적중|미적중)$/)).toBeTruthy();
      expect(screen.getByText(/^지급액: /)).toBeTruthy();
      expect(screen.getByText(/^정산 후 잔고: /)).toBeTruthy();
    });
  });

  describe("T18 이월 메모 해소: BetPanel 실마운트 시 미입력·소수 입력 경로", () => {
    it("금액 미입력 상태에서는 role=alert 검증 메시지가 노출되지 않는다", () => {
      const driver = createInMemoryDriver();
      render(<App driver={driver} />);

      fireEvent.click(screen.getByRole("radio", { name: "1번 번개질주" }));
      expect(screen.queryByRole("alert")).toBeNull();
    });

    it("직접 입력에 소수를 입력하면 정수 아님 사유가 노출된다", () => {
      const driver = createInMemoryDriver();
      render(<App driver={driver} />);

      fireEvent.click(screen.getByRole("radio", { name: "1번 번개질주" }));
      fireEvent.change(screen.getByLabelText("직접 입력"), { target: { value: "100.5" } });

      expect(screen.getByRole("alert").textContent).toBe("정수 아님");
    });
  });

  describe("T19 이월 메모 해소: 설정 변경·초기화가 store에 실연결된다", () => {
    it("출전마 수 변경 시 카탈로그가 재생성되어 로비 말 카드 수가 일치한다", () => {
      const driver = createInMemoryDriver();
      render(<App driver={driver} />);

      expect(screen.getAllByRole("article")).toHaveLength(5);

      fireEvent.change(screen.getByLabelText("출전마 수"), { target: { value: "7" } });

      expect(screen.getAllByRole("article")).toHaveLength(7);
    });

    it("음소거 토글의 true→false 반전 경로가 store settings.muted에 반영된다", () => {
      const driver = createInMemoryDriver();
      render(<App driver={driver} />);

      const getCheckbox = () => screen.getByLabelText("음소거") as HTMLInputElement;
      expect(getCheckbox().checked).toBe(false);

      fireEvent.click(getCheckbox()); // false -> true
      expect(getCheckbox().checked).toBe(true);

      fireEvent.click(getCheckbox()); // true -> false
      expect(getCheckbox().checked).toBe(false);
    });

    it("초기화 확인 후 잔고·파산 횟수가 기본값으로 복귀하고 저장 계층도 리셋된다", () => {
      const seedState = { ...createDefaultState(), balance: 5000, bankruptcyCount: 2 };
      const store = createGameStore(seedState);
      const driver = createInMemoryDriver();

      render(<App store={store} driver={driver} />);

      expect(screen.getByText("잔고: 5,000원")).toBeTruthy();
      expect(screen.getByText("파산 횟수: 2회")).toBeTruthy();

      fireEvent.click(screen.getByText("데이터 초기화"));
      fireEvent.click(screen.getByText("확인"));

      expect(screen.getByText("잔고: 10,000원")).toBeTruthy();
      expect(screen.getByText("파산 횟수: 0회")).toBeTruthy();
      expect(JSON.parse(driver.data[STORAGE_KEY]).balance).toBe(10000);
    });

    it("초기화 시 저장 쓰기가 실패하면 저장 비활성 배너가 노출된다", () => {
      const writeThrowingDriver: StorageDriver = {
        getItem: () => null,
        setItem: () => {
          throw new Error("write failed");
        },
      };

      render(<App driver={writeThrowingDriver} />);
      expect(screen.queryByRole("alert")).toBeNull();

      fireEvent.click(screen.getByText("데이터 초기화"));
      fireEvent.click(screen.getByText("확인"));

      expect(screen.getByRole("alert").textContent).toContain("저장이 비활성화");
    });
  });

  describe("T22: 지속적 자동 저장 배선(store 변경 → persistence.save)", () => {
    function extractBalanceFromSettlement(): number {
      const text = screen.getByText(/^정산 후 잔고: /).textContent ?? "";
      return Number(text.replace(/[^0-9]/g, ""));
    }

    it("베팅 확정→경주 구동→완주→정산 라이프사이클 후 persistence.save가 갱신된 잔고·전적을 담은 SavedState로 호출된다", () => {
      const driver = createInMemoryDriver();
      const timer = createManualTimer();
      const raf = createManualRaf();
      const ctx = createMockCtx();

      render(
        <App
          driver={driver}
          controllerOptions={{ timer, rng: createSeededRng(3) }}
          raceCanvasOverrides={{ getContext: () => ctx, raf, rng: createSeededRng(3) }}
        />,
      );

      fireEvent.click(screen.getByRole("radio", { name: "1번 번개질주" }));
      fireEvent.click(screen.getByText("100"));
      fireEvent.click(screen.getByText("베팅 확정"));

      act(() => {
        timer.flushAll();
      });
      act(() => {
        driveRaceToCompletion(raf);
      });

      const displayedBalance = extractBalanceFromSettlement();
      const saved = JSON.parse(driver.data[STORAGE_KEY]);

      expect(saved.balance).toBe(displayedBalance);
      expect(Object.keys(saved.records).length).toBeGreaterThan(0);
      expect(Object.values(saved.records).every((record) => (record as { racesRun: number }).racesRun >= 1)).toBe(
        true,
      );
    });

    it("새로고침 라운드트립: 같은 driver로 새 persistence를 만들어 load()하면 정산 후 잔고·전적이 복원된다", () => {
      const driver = createInMemoryDriver();
      const timer = createManualTimer();
      const raf = createManualRaf();
      const ctx = createMockCtx();

      render(
        <App
          driver={driver}
          controllerOptions={{ timer, rng: createSeededRng(3) }}
          raceCanvasOverrides={{ getContext: () => ctx, raf, rng: createSeededRng(3) }}
        />,
      );

      fireEvent.click(screen.getByRole("radio", { name: "1번 번개질주" }));
      fireEvent.click(screen.getByText("100"));
      fireEvent.click(screen.getByText("베팅 확정"));

      act(() => {
        timer.flushAll();
      });
      act(() => {
        driveRaceToCompletion(raf);
      });

      const displayedBalance = extractBalanceFromSettlement();

      const reloadedPersistence = createPersistence(driver);
      const { state, status } = reloadedPersistence.load();

      expect(status).toBe("ok");
      expect(state.balance).toBe(displayedBalance);
      expect(Object.keys(state.records).length).toBeGreaterThan(0);
    });

    it("store 교체 후에도 자동 저장이 유지된다: 설정 변경으로 store가 교체된 뒤 발생하는 잔고·전적 변경이 새 store에서 지속 저장된다", () => {
      const driver = createInMemoryDriver();
      const timer = createManualTimer();
      const raf = createManualRaf();
      const ctx = createMockCtx();

      render(
        <App
          driver={driver}
          controllerOptions={{ timer, rng: createSeededRng(5) }}
          raceCanvasOverrides={{ getContext: () => ctx, raf, rng: createSeededRng(5) }}
        />,
      );

      fireEvent.change(screen.getByLabelText("출전마 수"), { target: { value: "6" } });
      expect(JSON.parse(driver.data[STORAGE_KEY]).settings.horseCount).toBe(6);

      fireEvent.click(screen.getByRole("radio", { name: "1번 번개질주" }));
      fireEvent.click(screen.getByText("100"));
      fireEvent.click(screen.getByText("베팅 확정"));

      act(() => {
        timer.flushAll();
      });
      act(() => {
        driveRaceToCompletion(raf);
      });

      const displayedBalance = extractBalanceFromSettlement();
      const saved = JSON.parse(driver.data[STORAGE_KEY]);

      expect(saved.balance).toBe(displayedBalance);
      expect(saved.settings.horseCount).toBe(6);
      expect(Object.keys(saved.records).length).toBeGreaterThan(0);
    });

    it("진행 중 저장 시도가 실패하면 SaveResult.disabled=true로 전환되고 StorageBanner가 노출된다", () => {
      const data: Record<string, string> = {};
      let failWrites = false;
      const flakyDriver: StorageDriver = {
        getItem: (key) => data[key] ?? null,
        setItem: (key, value) => {
          if (failWrites) throw new Error("storage unavailable");
          data[key] = value;
        },
      };
      const timer = createManualTimer();

      render(<App driver={flakyDriver} controllerOptions={{ timer, rng: createSeededRng(2) }} />);
      expect(screen.queryByRole("alert")).toBeNull();

      failWrites = true;
      fireEvent.click(screen.getByRole("radio", { name: "1번 번개질주" }));
      fireEvent.click(screen.getByText("100"));
      fireEvent.click(screen.getByText("베팅 확정"));

      expect(screen.getByRole("alert").textContent).toContain("저장이 비활성화");
    });
  });
});

function ControllerHarness({
  store,
  options,
  raceCanvasProps,
  handleRef,
}: {
  store: ReturnType<typeof createGameStore>;
  options?: UseGameControllerOptions;
  raceCanvasProps: {
    getContext: (canvas: HTMLCanvasElement) => RenderContext | null;
    raf: RafSource;
    rng: () => number;
  };
  handleRef: { current: UseGameController | null };
}) {
  const controller = useGameController(store, options);
  handleRef.current = controller;
  return (
    <>
      {controller.raceState && (
        <RaceCanvas
          initialState={controller.raceState}
          horses={controller.horses}
          machine={controller.machine}
          onFrame={controller.handleFrame}
          getContext={raceCanvasProps.getContext}
          raf={raceCanvasProps.raf}
          rng={raceCanvasProps.rng}
        />
      )}
      <CommentaryFeed messages={controller.commentaryMessages} />
    </>
  );
}

describe("T20b REVIEW 권장 메모 흡수: 컨트롤러를 통과한 실황 자막의 통합 스냅샷", () => {
  it("경주 프레임을 주입 rng·가짜 loop으로 구동해도 CommentaryFeed에 {horseName}/{skillName} 리터럴이 남지 않는다", () => {
    const store = createGameStore(createDefaultState());
    const timer = createManualTimer();
    const raf = createManualRaf();
    const ctx = createMockCtx();
    const handleRef: { current: UseGameController | null } = { current: null };

    render(
      <ControllerHarness
        store={store}
        options={{ timer, rng: createSeededRng(7) }}
        raceCanvasProps={{ getContext: () => ctx, raf, rng: createSeededRng(7) }}
        handleRef={handleRef}
      />,
    );

    const betHorseId = handleRef.current!.lobbyEntries[0].horse.id;
    act(() => {
      handleRef.current!.handleBetConfirm(betHorseId, 100);
      timer.flushAll();
    });

    act(() => {
      driveRaceToCompletion(raf);
    });

    expect(handleRef.current!.commentaryMessages.length).toBeGreaterThan(0);
    const feed = screen.getByLabelText("실황 중계");
    expect(feed.textContent).not.toMatch(/\{[a-zA-Z]+\}/);
  });
});

describe("T24: 시각 완성도 기준선(CSS 도입)", () => {
  it("루트 컨테이너·HorseCard·잔고·설정에 지정한 시맨틱 클래스가 부여된다", () => {
    const driver = createInMemoryDriver();
    const { container } = render(<App driver={driver} />);

    expect(container.querySelector("main.app")).not.toBeNull();
    expect(container.querySelectorAll("article.horse-card").length).toBeGreaterThan(0);
    expect(screen.getByLabelText("잔고 정보").classList.contains("balance-display")).toBe(true);
    expect(screen.getByLabelText("설정").classList.contains("settings-panel")).toBe(true);
    expect(screen.getByLabelText("베팅 패널").classList.contains("bet-panel")).toBe(true);
  });

  it("정산 화면에서도 시맨틱 클래스(적중/미적중 상태 클래스 포함)가 유지된다", () => {
    const driver = createInMemoryDriver();
    const timer = createManualTimer();
    const raf = createManualRaf();
    const ctx = createMockCtx();

    render(
      <App
        driver={driver}
        controllerOptions={{ timer, rng: createSeededRng(3) }}
        raceCanvasOverrides={{ getContext: () => ctx, raf, rng: createSeededRng(3) }}
      />,
    );

    fireEvent.click(screen.getByRole("radio", { name: "1번 번개질주" }));
    fireEvent.click(screen.getByText("100"));
    fireEvent.click(screen.getByText("베팅 확정"));

    act(() => {
      timer.flushAll();
    });

    act(() => {
      driveRaceToCompletion(raf);
    });

    const settlement = screen.getByLabelText("정산 결과");
    expect(settlement.classList.contains("settlement-result")).toBe(true);
    expect(
      settlement.classList.contains("settlement-result--won") ||
        settlement.classList.contains("settlement-result--lost"),
    ).toBe(true);
  });
});

describe("T25: 전체 루프 통합 검증 (PRD 9번 성공 기준 1)", () => {
  it("베팅→카운트다운→경주→완주→정산→로비 전체 루프를 연속 2회 이상 오류 없이 반복하고, 1회차 정산이 2회차 시작을 막지 않는다", () => {
    const driver = createInMemoryDriver();
    const timer = createManualTimer();
    const raf = createManualRaf();
    const ctx = createMockCtx();

    render(
      <App
        driver={driver}
        controllerOptions={{ timer, rng: createSeededRng(11) }}
        raceCanvasOverrides={{ getContext: () => ctx, raf, rng: createSeededRng(11) }}
      />,
    );

    function playRound(): void {
      expect(screen.getByLabelText("베팅 패널")).toBeTruthy();
      expect(document.querySelector("canvas")).toBeNull();

      fireEvent.click(screen.getByRole("radio", { name: "1번 번개질주" }));
      fireEvent.click(screen.getByText("100"));
      fireEvent.click(screen.getByText("베팅 확정"));

      act(() => {
        timer.flushAll(); // 카운트다운 경과 → START_RACE
      });

      act(() => {
        driveRaceToCompletion(raf);
      });

      expect(screen.getByLabelText("정산 결과")).toBeTruthy();

      act(() => {
        timer.flushAll(); // 정산 표시 경과 → RESET → 로비 복귀
      });
    }

    playRound();
    expect(screen.getByLabelText("베팅 패널")).toBeTruthy();
    expect(screen.queryByLabelText("정산 결과")).toBeNull();

    playRound();
    expect(screen.getByLabelText("베팅 패널")).toBeTruthy();
    expect(screen.queryByLabelText("정산 결과")).toBeNull();
  });
});

describe("T25: 파산 자동 재충전 통합 검증 (PRD 4.4·9번 성공 기준 4)", () => {
  it("올인 베팅 확정으로 잔고가 최소 베팅액 미만이 되면 즉시 기본 잔고로 재충전되고 파산 횟수가 1 증가하며, 이후 루프가 정상적으로 이어진다", () => {
    const seedState = { ...createDefaultState(), balance: 150 };
    const store = createGameStore(seedState);
    const driver = createInMemoryDriver();
    const timer = createManualTimer();
    const raf = createManualRaf();
    const ctx = createMockCtx();

    render(
      <App
        store={store}
        driver={driver}
        controllerOptions={{ timer, rng: createSeededRng(13) }}
        raceCanvasOverrides={{ getContext: () => ctx, raf, rng: createSeededRng(13) }}
      />,
    );

    expect(screen.getByText("잔고: 150원")).toBeTruthy();

    fireEvent.click(screen.getByRole("radio", { name: "1번 번개질주" }));
    fireEvent.click(screen.getByText("올인")); // amount = balance(150) → adjustBalance(-150) 즉시 잔고 0
    fireEvent.click(screen.getByText("베팅 확정"));

    // 선차감 직후(경주 시작 전)에도 gameStore.adjustBalance 내부 파산 판정이 즉시 반영된다.
    expect(screen.getByText("잔고: 10,000원")).toBeTruthy();
    expect(screen.getByText("파산 횟수: 1회")).toBeTruthy();

    act(() => {
      timer.flushAll();
    });
    act(() => {
      driveRaceToCompletion(raf);
    });

    expect(screen.getByLabelText("정산 결과")).toBeTruthy();

    act(() => {
      timer.flushAll(); // RESET → 로비 복귀. 재충전 후에도 루프가 이어짐을 확인한다.
    });

    expect(screen.getByLabelText("베팅 패널")).toBeTruthy();
    expect(screen.getByText("파산 횟수: 1회")).toBeTruthy();
  });
});
