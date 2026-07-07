import { describe, expect, it } from "vitest";
import type { RaceRecord } from "./types";
import { RECENT_RESULTS_LIMIT, updateRecordsWithRaceResult } from "./records";

describe("updateRecordsWithRaceResult", () => {
  it("기존 기록이 있는 말: racesRun +1, 우승 시 wins +1, recentResults 맨 앞에 추가된다", () => {
    const records: Record<string, RaceRecord> = {
      "horse-1": { racesRun: 3, wins: 1, recentResults: [2, 4, 1] },
    };

    const updated = updateRecordsWithRaceResult(records, [{ id: "horse-1", rank: 1 }]);

    expect(updated["horse-1"]).toEqual({ racesRun: 4, wins: 2, recentResults: [1, 2, 4, 1] });
  });

  it("우승이 아니면 wins가 증가하지 않는다", () => {
    const records: Record<string, RaceRecord> = {
      "horse-1": { racesRun: 3, wins: 1, recentResults: [2, 4, 1] },
    };

    const updated = updateRecordsWithRaceResult(records, [{ id: "horse-1", rank: 3 }]);

    expect(updated["horse-1"]).toEqual({ racesRun: 4, wins: 1, recentResults: [3, 2, 4, 1] });
  });

  it("recentResults는 최근 5개만 유지하고 6번째부터는 밀려난다", () => {
    const records: Record<string, RaceRecord> = {
      "horse-1": { racesRun: 5, wins: 0, recentResults: [1, 2, 3, 4, 5] },
    };

    const updated = updateRecordsWithRaceResult(records, [{ id: "horse-1", rank: 2 }]);

    expect(updated["horse-1"].recentResults).toEqual([2, 1, 2, 3, 4]);
    expect(updated["horse-1"].recentResults).toHaveLength(RECENT_RESULTS_LIMIT);
  });

  it("신규 출전(records에 키 없음): racesRun=1, wins=우승 여부, recentResults=[rank]로 새로 생성된다", () => {
    const updated = updateRecordsWithRaceResult({}, [{ id: "horse-new", rank: 1 }]);

    expect(updated["horse-new"]).toEqual({ racesRun: 1, wins: 1, recentResults: [1] });

    const updatedLoser = updateRecordsWithRaceResult({}, [{ id: "horse-new", rank: 4 }]);
    expect(updatedLoser["horse-new"]).toEqual({ racesRun: 1, wins: 0, recentResults: [4] });
  });

  it("여러 말을 한 번에 갱신하고, 순위에 없는 다른 말의 기록은 건드리지 않는다", () => {
    const records: Record<string, RaceRecord> = {
      "horse-1": { racesRun: 1, wins: 0, recentResults: [2] },
      "horse-2": { racesRun: 1, wins: 1, recentResults: [1] },
      "horse-untouched": { racesRun: 9, wins: 3, recentResults: [1, 1, 2] },
    };

    const updated = updateRecordsWithRaceResult(records, [
      { id: "horse-1", rank: 1 },
      { id: "horse-2", rank: 2 },
    ]);

    expect(updated["horse-1"]).toEqual({ racesRun: 2, wins: 1, recentResults: [1, 2] });
    expect(updated["horse-2"]).toEqual({ racesRun: 2, wins: 1, recentResults: [2, 1] });
    expect(updated["horse-untouched"]).toEqual(records["horse-untouched"]);
  });

  it("입력 records를 변경하지 않는다(방어 복사)", () => {
    const records: Record<string, RaceRecord> = {
      "horse-1": { racesRun: 1, wins: 0, recentResults: [2] },
    };
    const snapshot = JSON.parse(JSON.stringify(records));

    const updated = updateRecordsWithRaceResult(records, [{ id: "horse-1", rank: 1 }]);

    expect(records).toEqual(snapshot);
    expect(updated).not.toBe(records);
    expect(updated["horse-1"]).not.toBe(records["horse-1"]);
  });
});
