import { describe, expect, it } from "vitest";
import { createDefaultState, STORAGE_KEY, type SavedState } from "./schema";
import { createPersistence, type StorageDriver } from "./storage";

function createMemoryDriver(): StorageDriver {
  const map = new Map<string, string>();
  return {
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => {
      map.set(key, value);
    },
  };
}

function createThrowingDriver(): StorageDriver {
  return {
    getItem: () => {
      throw new Error("storage unavailable");
    },
    setItem: () => {
      throw new Error("storage unavailable");
    },
  };
}

/** getItem은 정상 동작하지만 setItem만 예외를 던지는(쿼터 초과 등) 드라이버. */
function createSetItemThrowingDriver(): StorageDriver {
  const map = new Map<string, string>();
  return {
    getItem: (key) => map.get(key) ?? null,
    setItem: () => {
      throw new Error("quota exceeded");
    },
  };
}

describe("persistence/storage", () => {
  it("정상 라운드트립: save 후 load가 동일한 상태를 복원한다", () => {
    const persistence = createPersistence(createMemoryDriver());
    const state: SavedState = {
      ...createDefaultState(),
      balance: 5000,
      bankruptcyCount: 2,
      records: { "horse-1": { racesRun: 3, wins: 1, recentResults: [1, 3, 2] } },
    };

    const saveResult = persistence.save(state);
    expect(saveResult.disabled).toBe(false);

    const loadResult = persistence.load();
    expect(loadResult.status).toBe("ok");
    expect(loadResult.state).toEqual(state);
  });

  it("저장된 값이 없으면 empty 상태와 기본값을 반환한다", () => {
    const persistence = createPersistence(createMemoryDriver());
    const loadResult = persistence.load();
    expect(loadResult.status).toBe("empty");
    expect(loadResult.state).toEqual(createDefaultState());
  });

  it("JSON 파싱 실패 시 예외 없이 초기값과 corrupted 상태를 반환한다", () => {
    const driver = createMemoryDriver();
    driver.setItem(STORAGE_KEY, "{ this is not valid json");
    const persistence = createPersistence(driver);

    const loadResult = persistence.load();
    expect(loadResult.status).toBe("corrupted");
    expect(loadResult.state).toEqual(createDefaultState());
  });

  it("스키마 불일치 데이터 입력 시 예외 없이 초기값과 corrupted 상태를 반환한다", () => {
    const driver = createMemoryDriver();
    driver.setItem(STORAGE_KEY, JSON.stringify({ version: 1, balance: "not-a-number" }));
    const persistence = createPersistence(driver);

    const loadResult = persistence.load();
    expect(loadResult.status).toBe("corrupted");
    expect(loadResult.state).toEqual(createDefaultState());
  });

  it("스키마 버전이 다르면 corrupted로 취급한다", () => {
    const driver = createMemoryDriver();
    driver.setItem(STORAGE_KEY, JSON.stringify({ ...createDefaultState(), version: 999 }));
    const persistence = createPersistence(driver);

    const loadResult = persistence.load();
    expect(loadResult.status).toBe("corrupted");
  });

  it("save 단독 실패: load 없이 save만 호출해도 setItem 예외 시 disabled로 전환되어 이후 메모리로 우회한다", () => {
    const persistence = createPersistence(createSetItemThrowingDriver());
    const state: SavedState = { ...createDefaultState(), balance: 4000 };

    const saveResult = persistence.save(state);
    expect(saveResult.disabled).toBe(true);
    expect(persistence.isDisabled()).toBe(true);

    const loadResult = persistence.load();
    expect(loadResult.status).toBe("disabled");
    expect(loadResult.state).toEqual(state);
  });

  it("records의 개별 항목이 손상되면(isRaceRecord 불일치) corrupted로 리셋된다", () => {
    const driver = createMemoryDriver();
    const invalid = {
      ...createDefaultState(),
      records: { "horse-1": { racesRun: 3, wins: "not-a-number", recentResults: [1, 2] } },
    };
    driver.setItem(STORAGE_KEY, JSON.stringify(invalid));
    const persistence = createPersistence(driver);

    const loadResult = persistence.load();
    expect(loadResult.status).toBe("corrupted");
    expect(loadResult.state).toEqual(createDefaultState());
  });

  it("settings.horseCount가 범위(4~8)를 벗어나면 corrupted로 리셋된다", () => {
    const driver = createMemoryDriver();
    const invalid = {
      ...createDefaultState(),
      settings: { horseCount: 99, muted: false },
    };
    driver.setItem(STORAGE_KEY, JSON.stringify(invalid));
    const persistence = createPersistence(driver);

    const loadResult = persistence.load();
    expect(loadResult.status).toBe("corrupted");
    expect(loadResult.state).toEqual(createDefaultState());
  });

  it("저장소 접근이 예외를 던지면 세션 메모리로 폴백하고 disabled 상태를 노출한다", () => {
    const persistence = createPersistence(createThrowingDriver());

    const loadResult = persistence.load();
    expect(loadResult.status).toBe("disabled");
    expect(loadResult.state).toEqual(createDefaultState());
    expect(persistence.isDisabled()).toBe(true);

    const state: SavedState = { ...createDefaultState(), balance: 7000 };
    const saveResult = persistence.save(state);
    expect(saveResult.disabled).toBe(true);

    const reloaded = persistence.load();
    expect(reloaded.status).toBe("disabled");
    expect(reloaded.state).toEqual(state);
  });
});
