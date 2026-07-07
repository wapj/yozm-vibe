import { describe, expect, it } from "vitest";
import { createInitialMachineState, transition } from "./machine";

describe("game state machine", () => {
  it("정의된 순서(로비→카운트다운→경주→피니시→정산→로비)로만 전이한다", () => {
    let state = createInitialMachineState();
    expect(state.phase).toBe("lobby");

    state = transition(state, "START_COUNTDOWN");
    expect(state.phase).toBe("countdown");

    state = transition(state, "START_RACE");
    expect(state.phase).toBe("racing");

    state = transition(state, "FINISH");
    expect(state.phase).toBe("finish");

    state = transition(state, "SETTLE");
    expect(state.phase).toBe("settlement");

    state = transition(state, "RESET");
    expect(state.phase).toBe("lobby");
  });

  it("정의되지 않은 전이는 거부되어 상태가 그대로 유지된다", () => {
    const state = createInitialMachineState();
    expect(transition(state, "START_RACE")).toEqual(state);
    expect(transition(state, "FINISH")).toEqual(state);
    expect(transition(state, "SETTLE")).toEqual(state);
    expect(transition(state, "RESET")).toEqual(state);
  });

  it("PAUSE는 경주 중에만 유효하다", () => {
    const lobby = createInitialMachineState();
    expect(transition(lobby, "PAUSE")).toEqual(lobby);

    let racing = transition(lobby, "START_COUNTDOWN");
    racing = transition(racing, "START_RACE");
    expect(racing).toEqual({ phase: "racing", paused: false });

    const paused = transition(racing, "PAUSE");
    expect(paused).toEqual({ phase: "racing", paused: true });
  });

  it("RESUME은 paused 상태에서만 유효하다", () => {
    let racing = transition(createInitialMachineState(), "START_COUNTDOWN");
    racing = transition(racing, "START_RACE");

    expect(transition(racing, "RESUME")).toEqual(racing);

    const paused = transition(racing, "PAUSE");
    const resumed = transition(paused, "RESUME");
    expect(resumed).toEqual({ phase: "racing", paused: false });
  });

  it("paused 상태에서는 FINISH 등 다른 전이가 모두 거부된다", () => {
    let racing = transition(createInitialMachineState(), "START_COUNTDOWN");
    racing = transition(racing, "START_RACE");
    const paused = transition(racing, "PAUSE");

    expect(transition(paused, "FINISH")).toEqual(paused);
    expect(transition(paused, "START_COUNTDOWN")).toEqual(paused);
  });
});
