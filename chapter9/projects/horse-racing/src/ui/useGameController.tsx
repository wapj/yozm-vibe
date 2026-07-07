/**
 * T20b: 베팅 확정→선차감→카운트다운→경주 생성→상태 전이→정산→실황 emit→로비 복귀의
 * 전체 게임 루프를 배선하는 오케스트레이션 훅. `RaceCanvas`(T20a)가 이미 loop을
 * 소유하므로 이 훅은 두 번째 loop을 만들지 않고, `RaceCanvas`의 `onFrame` 콜백으로
 * 라이프사이클을 관찰한다. 정산 계산·파산 재충전·회차 변동·배당·순위 산출은
 * 재구현하지 않고 기존 함수(`calculateSettlement`·`adjustBalance`·`buildLobbyEntries`·
 * `rankRunners`)를 소비한다.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createSoundEngine } from "../audio/soundEngine";
import type { SoundEngine } from "../audio/types";
import type { GameSettings } from "../persistence/schema";
import type { HorseProfile, HorseRaceEntry } from "../domain/types";
import { calculateSettlement, type SettlementOutcome } from "../domain/settlement";
import type { RenderLoopMachine } from "../render/types";
import { createRaceState } from "../sim/engine";
import type { RaceState, RankedRunner } from "../sim/types";
import type { GameStore } from "../store/gameStore";
import type { GamePhase } from "../domain/types";
import type { CommentaryMessage } from "./CommentaryFeed";
import { pickCommentaryLine } from "./commentary";
import { buildLobbyEntries } from "./lobbyEntries";
import { buildSettlementInput, deriveRaceEvents, toRaceParticipants, type RaceFrameSnapshot } from "./raceLifecycle";
import type { TimerSource } from "./types";
import { useGameStore } from "./useGameStore";

/**
 * 로비→카운트다운 진입 후 경주 시작까지의 지연(ms). PRD에 수치가 명시되지 않아
 * generator가 정한 값이다(되돌리기 쉬운 결정). 주입 타이머로 결정적 테스트가 가능하다.
 */
export const DEFAULT_COUNTDOWN_MS = 3000;

/**
 * 정산 표시 후 로비로 자동 복귀하기까지의 지연(ms). PRD 3장 게임 루프("정산 → 로비")가
 * 순환을 전제하므로 자동 지연 복귀를 택했다(사용자 확인 대기 없음, 되돌리기 쉬운 결정).
 */
export const DEFAULT_SETTLEMENT_DISPLAY_MS = 4000;

function createBrowserTimer(): TimerSource {
  return {
    schedule: (callback, delayMs) => window.setTimeout(callback, delayMs) as unknown as number,
    cancel: (handle) => window.clearTimeout(handle),
  };
}

const BROWSER_TIMER = createBrowserTimer();

interface ActiveBet {
  horseId: string;
  amount: number;
  /** 베팅 확정 시점의 로비 스냅샷. 경주 생성·정산이 모두 이 스냅샷의 currentStats·odds를 쓴다. */
  entries: HorseRaceEntry[];
}

export interface UseGameControllerOptions {
  /** 생략 시 `Math.random`. 로비 회차 변동·경주 burst 위상·실황 문구 선택에 함께 쓰인다. */
  rng?: () => number;
  /** 생략 시 `window.setTimeout`/`clearTimeout`. 결정적 테스트를 위해 가짜 타이머를 주입할 수 있다. */
  timer?: TimerSource;
  countdownMs?: number;
  settlementDisplayMs?: number;
  /**
   * 생략 시 `createSoundEngine()`으로 지연 생성한 기본 엔진을 훅 내부에서 1회 만들어 쓴다.
   * 테스트에서 mock `SoundEngine`을 주입해 배선(호출 이름·순서·인자)을 결정적으로 검증할 수 있다.
   */
  sound?: SoundEngine;
}

export interface UseGameController {
  phase: GamePhase;
  balance: number;
  bankruptcyCount: number;
  settings: GameSettings;
  horses: HorseProfile[];
  lobbyEntries: HorseRaceEntry[];
  /** racing 진입 전(카운트다운 중 생성 대기)에는 null이다. */
  raceState: RaceState | null;
  /** store `dispatch`/`getState().paused`를 감싸 `RaceCanvas`의 탭 자동 일시정지에 연결하는 어댑터. 안정적 참조. */
  machine: RenderLoopMachine;
  settlement: SettlementOutcome | null;
  commentaryMessages: CommentaryMessage[];
  /** 베팅 패널(`BetPanel`)의 `onConfirm`에 그대로 연결한다. */
  handleBetConfirm(horseId: string, amount: number): void;
  /** `RaceCanvas`의 `onFrame`에 그대로 연결한다. */
  handleFrame(state: RaceState, rankings: RankedRunner[]): void;
}

export function useGameController(
  store: GameStore,
  options: UseGameControllerOptions = {},
): UseGameController {
  const rng = options.rng ?? Math.random;
  const timer = options.timer ?? BROWSER_TIMER;
  const countdownMs = options.countdownMs ?? DEFAULT_COUNTDOWN_MS;
  const settlementDisplayMs = options.settlementDisplayMs ?? DEFAULT_SETTLEMENT_DISPLAY_MS;

  const storeState = useGameStore(store);

  /**
   * 기본 엔진은 훅이 살아있는 동안 1회만 만든다(store 교체와 무관하게 안정적 참조 유지).
   * `createSoundEngine()` 자체는 `enable()` 전까지 실제 AudioContext를 만들지 않아 안전하다.
   */
  const defaultSoundRef = useRef<SoundEngine | undefined>(undefined);
  if (defaultSoundRef.current === undefined) {
    defaultSoundRef.current = createSoundEngine();
  }
  const sound = options.sound ?? defaultSoundRef.current;

  const machine = useMemo<RenderLoopMachine>(
    () => ({
      isPaused: () => store.getState().paused,
      dispatch: (event) => store.dispatch(event),
    }),
    [store],
  );

  const [lobbyEntries, setLobbyEntries] = useState<HorseRaceEntry[]>(() =>
    buildLobbyEntries(store.getState().horses, store.getState().records, rng),
  );
  const prevPhaseRef = useRef<GamePhase>(storeState.phase);
  /** T20c: 설정 변경·초기화가 store 인스턴스 교체로 구현되므로(gameStore.ts 미변경),
   * `storeState.horses` 참조가 바뀌면(카탈로그 재생성) phase 전이 여부와 무관하게 다시 굴린다.
   * `store`(prop) 대신 `storeState.horses`를 추적하는 이유: store 교체 직후 첫 렌더에서는
   * `useGameStore`의 재구독 effect가 아직 실행되지 않아 storeState가 이전 store 값을 그대로
   * 들고 있을 수 있다. horses 참조로 추적하면 storeState가 실제로 갱신된 렌더에서만 반응한다. */
  const prevHorsesRef = useRef<HorseProfile[]>(storeState.horses);

  useEffect(() => {
    const catalogChanged = storeState.horses !== prevHorsesRef.current;
    const enteredLobby = storeState.phase === "lobby" && prevPhaseRef.current !== "lobby";
    if (catalogChanged || enteredLobby) {
      setLobbyEntries(buildLobbyEntries(storeState.horses, storeState.records, rng));
    }
    prevHorsesRef.current = storeState.horses;
    prevPhaseRef.current = storeState.phase;
  }, [storeState.phase, storeState.horses, storeState.records, rng]);

  const [activeBet, setActiveBet] = useState<ActiveBet | null>(null);
  const [raceState, setRaceState] = useState<RaceState | null>(null);
  const [settlement, setSettlement] = useState<SettlementOutcome | null>(null);
  const [commentaryMessages, setCommentaryMessages] = useState<CommentaryMessage[]>([]);

  const activeBetRef = useRef<ActiveBet | null>(null);
  activeBetRef.current = activeBet;

  const prevFrameRef = useRef<RaceFrameSnapshot | null>(null);
  const finishHandledRef = useRef(false);
  const commentaryIdRef = useRef(0);
  const countdownHandleRef = useRef<number | null>(null);
  const settlementHandleRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (countdownHandleRef.current !== null) timer.cancel(countdownHandleRef.current);
      if (settlementHandleRef.current !== null) timer.cancel(settlementHandleRef.current);
    };
  }, [timer]);

  /** PRD 4.9: 음소거 상태가 바뀔 때(초기값 포함) 실제 오디오 출력에 반영한다. */
  useEffect(() => {
    sound.setMuted(storeState.settings.muted);
  }, [sound, storeState.settings.muted]);

  const handleBetConfirm = useCallback(
    (horseId: string, amount: number) => {
      const entries = lobbyEntries;

      try {
        // PRD 4.8 자동재생 게이팅: 첫 사용자 입력(베팅 확정)에서 AudioContext를 활성화한다.
        // AudioContext 미지원 환경(예: jsdom 테스트)에서는 조용히 무시하고 진행한다.
        sound.enable();
      } catch {
        // no-op
      }

      store.adjustBalance(-amount);
      store.dispatch("START_COUNTDOWN");

      setActiveBet({ horseId, amount, entries });
      setSettlement(null);
      setCommentaryMessages([]);
      setRaceState(null);
      prevFrameRef.current = null;
      finishHandledRef.current = false;

      countdownHandleRef.current = timer.schedule(() => {
        const participants = toRaceParticipants(entries);
        setRaceState(createRaceState(participants, rng));
        store.dispatch("START_RACE");
      }, countdownMs);
    },
    [lobbyEntries, store, timer, rng, countdownMs, sound],
  );

  const handleFrame = useCallback(
    (state: RaceState, rankings: RankedRunner[]) => {
      const snapshot: RaceFrameSnapshot = { state, rankings };
      const events = deriveRaceEvents(store.getState().horses, prevFrameRef.current, snapshot);
      prevFrameRef.current = snapshot;

      if (events.length > 0) {
        const messages: CommentaryMessage[] = events.map((event) => {
          commentaryIdRef.current += 1;
          return { id: `commentary-${commentaryIdRef.current}`, text: pickCommentaryLine(event, rng) };
        });
        setCommentaryMessages((prev) => [...prev, ...messages]);

        // 실황 이벤트→사운드(PRD 4.8). lead-change·final-stretch·close-race는 전용 사운드를 두지 않는다.
        for (const event of events) {
          if (event.type === "start") {
            sound.play("start-fanfare");
            sound.startLoop("hoofbeat");
          } else if (event.type === "skill-activation") {
            sound.play("skill-activation");
          } else if (event.type === "finish") {
            sound.play("finish-cheer");
            sound.stopLoop("hoofbeat");
          }
        }
      }

      const bet = activeBetRef.current;
      if (state.finished && !finishHandledRef.current && bet) {
        finishHandledRef.current = true;

        store.dispatch("FINISH");
        store.recordRaceResult(rankings);

        const settlementInput = buildSettlementInput(bet.entries, bet.horseId, bet.amount, rankings);
        const outcome = calculateSettlement(settlementInput);
        store.adjustBalance(outcome.balanceChange);
        store.dispatch("SETTLE");
        setSettlement(outcome);
        sound.play(outcome.won ? "settlement-win" : "settlement-lose");

        settlementHandleRef.current = timer.schedule(() => {
          store.dispatch("RESET");
          setActiveBet(null);
          setRaceState(null);
        }, settlementDisplayMs);
      }
    },
    [store, rng, timer, settlementDisplayMs, sound],
  );

  return {
    phase: storeState.phase,
    balance: storeState.balance,
    bankruptcyCount: storeState.bankruptcyCount,
    settings: storeState.settings,
    horses: storeState.horses,
    lobbyEntries,
    raceState,
    machine,
    settlement,
    commentaryMessages,
    handleBetConfirm,
    handleFrame,
  };
}
