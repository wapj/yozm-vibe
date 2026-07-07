import { useState } from "react";
import type { GameSettings } from "../persistence/schema";
import { MAX_HORSE_COUNT, MIN_HORSE_COUNT } from "../persistence/schema";

export interface SettingsPanelProps {
  settings: GameSettings;
  bankruptcyCount: number;
  onSettingsChange: (settings: GameSettings) => void;
  onReset: () => void;
}

const HORSE_COUNT_OPTIONS = Array.from(
  { length: MAX_HORSE_COUNT - MIN_HORSE_COUNT + 1 },
  (_, index) => MIN_HORSE_COUNT + index,
);

/**
 * PRD 4.9: 출전마 수·음소거 설정의 표시·변경과 데이터 초기화 확인까지 담당한다.
 * 실제 store 반영(카탈로그 재생성·저장)과 초기화 리셋 배선은 T20 오케스트레이션의 몫이다.
 * 초기화 확인은 window.confirm 대신 인라인 2단계 확인으로 구현한다(jsdom에서 상호작용을
 * 직접 단언할 수 있는 가장 단순한 형태, 되돌리기 쉬운 표시 결정).
 */
export function SettingsPanel({
  settings,
  bankruptcyCount,
  onSettingsChange,
  onReset,
}: SettingsPanelProps) {
  const [confirmingReset, setConfirmingReset] = useState(false);

  function handleHorseCountChange(value: string): void {
    onSettingsChange({ ...settings, horseCount: Number(value) });
  }

  function handleMutedToggle(): void {
    onSettingsChange({ ...settings, muted: !settings.muted });
  }

  function handleResetConfirm(): void {
    setConfirmingReset(false);
    onReset();
  }

  return (
    <section className="card settings-panel" aria-label="설정">
      <p>파산 횟수: {bankruptcyCount}</p>

      <label>
        출전마 수
        <select
          value={settings.horseCount}
          onChange={(event) => handleHorseCountChange(event.target.value)}
        >
          {HORSE_COUNT_OPTIONS.map((count) => (
            <option key={count} value={count}>
              {count}
            </option>
          ))}
        </select>
      </label>

      <label>
        음소거
        <input type="checkbox" checked={settings.muted} onChange={handleMutedToggle} />
      </label>

      {!confirmingReset && (
        <button type="button" onClick={() => setConfirmingReset(true)}>
          데이터 초기화
        </button>
      )}

      {confirmingReset && (
        <div className="settings-panel__reset-confirm" role="group" aria-label="데이터 초기화 확인">
          <p>정말 초기화하시겠습니까? 잔고·전적·설정이 모두 리셋됩니다.</p>
          <button type="button" onClick={handleResetConfirm}>
            확인
          </button>
          <button type="button" onClick={() => setConfirmingReset(false)}>
            취소
          </button>
        </div>
      )}
    </section>
  );
}
