import { createDefaultState, STORAGE_KEY, validateSavedState, type SavedState } from "./schema";

/** localStorage와 동일한 형태의 최소 인터페이스. 테스트에서는 임의 구현을 주입한다. */
export interface StorageDriver {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export type LoadStatus = "ok" | "empty" | "corrupted" | "disabled";

export interface LoadResult {
  state: SavedState;
  status: LoadStatus;
}

export interface SaveResult {
  disabled: boolean;
}

export interface PersistenceController {
  load(): LoadResult;
  save(state: SavedState): SaveResult;
  isDisabled(): boolean;
}

export function createLocalStorageDriver(): StorageDriver {
  return {
    getItem: (key) => window.localStorage.getItem(key),
    setItem: (key, value) => window.localStorage.setItem(key, value),
  };
}

/**
 * 저장/로드 컨트롤러를 생성한다. driver 접근이 예외를 던지면(저장소 미가용)
 * 이후 모든 접근을 세션 메모리로 폴백하고 disabled 상태를 노출한다.
 */
export function createPersistence(
  driver: StorageDriver,
  storageKey: string = STORAGE_KEY,
): PersistenceController {
  let disabled = false;
  let memoryFallback: string | null = null;

  function safeGet(): string | null {
    if (disabled) return memoryFallback;
    try {
      return driver.getItem(storageKey);
    } catch {
      disabled = true;
      return memoryFallback;
    }
  }

  function safeSet(value: string): void {
    if (disabled) {
      memoryFallback = value;
      return;
    }
    try {
      driver.setItem(storageKey, value);
    } catch {
      disabled = true;
      memoryFallback = value;
    }
  }

  return {
    load(): LoadResult {
      const raw = safeGet();
      if (raw === null) {
        return { state: createDefaultState(), status: disabled ? "disabled" : "empty" };
      }

      let parsed: unknown;
      try {
        parsed = JSON.parse(raw);
      } catch {
        return { state: createDefaultState(), status: "corrupted" };
      }

      const validated = validateSavedState(parsed);
      if (!validated) {
        return { state: createDefaultState(), status: "corrupted" };
      }
      return { state: validated, status: disabled ? "disabled" : "ok" };
    },
    save(state: SavedState): SaveResult {
      safeSet(JSON.stringify(state));
      return { disabled };
    },
    isDisabled(): boolean {
      return disabled;
    },
  };
}
