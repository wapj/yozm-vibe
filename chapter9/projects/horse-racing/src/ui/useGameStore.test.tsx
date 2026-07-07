import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";
import { createDefaultState } from "../persistence/schema";
import { createGameStore, type GameStore } from "../store/gameStore";
import { useGameStore } from "./useGameStore";

afterEach(cleanup);

let probeRenderCount = 0;

function Probe({ store }: { store: GameStore }) {
  const state = useGameStore(store);
  probeRenderCount += 1;
  return (
    <div>
      <span data-testid="balance">{state.balance}</span>
      <span data-testid="bankruptcy">{state.bankruptcyCount}</span>
    </div>
  );
}

describe("useGameStore", () => {
  it("스토어 변경(adjustBalance)이 구독 컴포넌트의 리렌더로 반영된다", () => {
    const store = createGameStore(createDefaultState());
    render(<Probe store={store} />);

    expect(screen.getByTestId("balance").textContent).toBe("10000");

    act(() => {
      store.adjustBalance(-500);
    });

    expect(screen.getByTestId("balance").textContent).toBe("9500");
  });

  it("스토어 변경(dispatch)도 구독 컴포넌트의 리렌더로 반영된다", () => {
    const store = createGameStore(createDefaultState());
    render(<Probe store={store} />);

    act(() => {
      store.dispatch("START_COUNTDOWN");
      store.adjustBalance(-1);
    });

    expect(screen.getByTestId("balance").textContent).toBe("9999");
  });

  it("getState가 매번 새 객체를 반환해도 무한 리렌더 없이 emit 횟수만큼만 유한하게 갱신된다", () => {
    const store = createGameStore(createDefaultState());
    probeRenderCount = 0;
    render(<Probe store={store} />);
    const afterMount = probeRenderCount;

    act(() => {
      for (let i = 0; i < 5; i += 1) {
        store.adjustBalance(-1);
      }
    });

    // 무한 리렌더였다면 이 단언에 도달하기 전에 테스트가 타임아웃/스택오버플로로 실패한다.
    expect(probeRenderCount).toBeGreaterThan(afterMount);
    expect(probeRenderCount).toBeLessThan(afterMount + 20);
    expect(screen.getByTestId("balance").textContent).toBe("9995");
  });

  it("동일 store 참조가 유지되는 한 부모 리렌더에도 재구독하지 않는다", () => {
    const store = createGameStore(createDefaultState());
    let subscribeCalls = 0;
    const originalSubscribe = store.subscribe;
    store.subscribe = (listener) => {
      subscribeCalls += 1;
      return originalSubscribe(listener);
    };

    function Wrapper() {
      const [tick, setTick] = useState(0);
      return (
        <div>
          <button onClick={() => setTick((t) => t + 1)}>tick:{tick}</button>
          <Probe store={store} />
        </div>
      );
    }

    render(<Wrapper />);
    act(() => {
      fireEvent.click(screen.getByRole("button"));
      fireEvent.click(screen.getByRole("button"));
    });

    expect(subscribeCalls).toBe(1);
  });
});
