import { describe, expect, it } from "vitest";
import { SAVE_SCHEMA_VERSION } from "./schema";
import { toSavedState } from "./projection";

describe("toSavedState", () => {
  it("balance·bankruptcyCount·records·settings를 그대로 옮기고 version을 SAVE_SCHEMA_VERSION으로 채운다", () => {
    const records = { horse1: { racesRun: 3, wins: 1, recentResults: [1, 3, 2] } };
    const settings = { horseCount: 6, muted: true };

    const result = toSavedState({ balance: 4200, bankruptcyCount: 2, records, settings });

    expect(result).toEqual({
      version: SAVE_SCHEMA_VERSION,
      balance: 4200,
      bankruptcyCount: 2,
      records,
      settings,
    });
  });

  it("상태 머신 필드(phase·paused)와 horses는 결과에 포함되지 않는다", () => {
    const stateWithExtraFields = {
      phase: "racing",
      paused: true,
      horses: [{ id: "horse1" }],
      balance: 10000,
      bankruptcyCount: 0,
      records: {},
      settings: { horseCount: 5, muted: false },
    };

    const result = toSavedState(stateWithExtraFields as never) as unknown as Record<string, unknown>;

    expect(Object.keys(result).sort()).toEqual(["balance", "bankruptcyCount", "records", "settings", "version"]);
    expect(result.phase).toBeUndefined();
    expect(result.paused).toBeUndefined();
    expect(result.horses).toBeUndefined();
  });
});
