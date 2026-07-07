import { useState } from "react";
import type { HorseProfile } from "../domain/types";
import { validateBetAmount } from "./betValidation";

export interface BetPanelProps {
  horses: HorseProfile[];
  balance: number;
  onConfirm: (horseId: string, amount: number) => void;
}

const PRESET_AMOUNTS = [100, 500, 1000];

/**
 * PRD 4.3: 출전마 선택·베팅 금액 설정(프리셋/직접 입력)·검증까지 담당한다.
 * 확정 이후의 상태 전이·잔고 선차감·경주 생성은 T20 오케스트레이션의 몫이다.
 * 잔고보다 큰 프리셋 버튼은 비활성 처리한다(클램프보다 사용자 의도가 분명한
 * 가장 단순한 선택지, 되돌리기 쉬운 표시 결정).
 */
export function BetPanel({ horses, balance, onConfirm }: BetPanelProps) {
  const [selectedHorseId, setSelectedHorseId] = useState<string | null>(null);
  const [amount, setAmount] = useState<number | null>(null);

  const validation = amount === null ? { valid: false } : validateBetAmount(amount, balance);
  const canConfirm = selectedHorseId !== null && validation.valid;

  function handleConfirm(): void {
    if (selectedHorseId !== null && amount !== null && validation.valid) {
      onConfirm(selectedHorseId, amount);
    }
  }

  function handleDirectInputChange(value: string): void {
    if (value === "") {
      setAmount(null);
      return;
    }
    const parsed = Number(value);
    setAmount(Number.isNaN(parsed) ? null : parsed);
  }

  return (
    <section className="card bet-panel" aria-label="베팅 패널">
      <fieldset>
        <legend>출전마 선택</legend>
        {horses.map((horse) => (
          <label key={horse.id}>
            <input
              type="radio"
              name="bet-horse"
              value={horse.id}
              checked={selectedHorseId === horse.id}
              onChange={() => setSelectedHorseId(horse.id)}
            />
            {`${horse.number}번 ${horse.name}`}
          </label>
        ))}
      </fieldset>

      <div className="bet-panel__presets" role="group" aria-label="베팅 금액 프리셋">
        {PRESET_AMOUNTS.map((preset) => (
          <button
            key={preset}
            type="button"
            disabled={preset > balance}
            onClick={() => setAmount(preset)}
          >
            {preset.toLocaleString("ko-KR")}
          </button>
        ))}
        <button type="button" onClick={() => setAmount(balance)}>
          올인
        </button>
      </div>

      <label>
        직접 입력
        <input
          type="number"
          value={amount ?? ""}
          onChange={(event) => handleDirectInputChange(event.target.value)}
        />
      </label>

      {amount !== null && !validation.valid && validation.reason && (
        <p className="bet-panel__error" role="alert">
          {validation.reason}
        </p>
      )}

      <button type="button" disabled={!canConfirm} onClick={handleConfirm}>
        베팅 확정
      </button>
    </section>
  );
}
