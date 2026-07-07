import { useCallback, useEffect, useState } from "react";
import { createDefaultState, type GameSettings } from "./persistence/schema";
import { toSavedState } from "./persistence/projection";
import {
  createLocalStorageDriver,
  createPersistence,
  type PersistenceController,
  type StorageDriver,
} from "./persistence/storage";
import type { RafSource, RenderContext, VisibilitySource } from "./render/types";
import { createGameStore, type GameStore, type GameStoreState } from "./store/gameStore";
import { BalanceDisplay } from "./ui/BalanceDisplay";
import { BetPanel } from "./ui/BetPanel";
import { CommentaryFeed } from "./ui/CommentaryFeed";
import { HorseCard } from "./ui/HorseCard";
import { RaceCanvas } from "./ui/RaceCanvas";
import { SettingsPanel } from "./ui/SettingsPanel";
import { SettlementResult } from "./ui/SettlementResult";
import { StorageBanner } from "./ui/StorageBanner";
import { useGameController, type UseGameControllerOptions } from "./ui/useGameController";

export interface AppProps {
  /** 테스트에서 localStorage 대신 주입할 driver. 프로덕션은 `createLocalStorageDriver()`. */
  driver?: StorageDriver;
  /** 테스트에서 부트스트랩을 건너뛰고 미리 구성한 스토어를 직접 주입하고 싶을 때 사용한다. */
  store?: GameStore;
  /** 테스트에서 베팅→정산 라이프사이클을 결정적으로 구동하기 위해 주입한다(rng·timer 등). */
  controllerOptions?: UseGameControllerOptions;
  /** 테스트에서 `RaceCanvas`의 ctx·raf·visibility·rng를 결정적으로 대체하기 위해 주입한다. */
  raceCanvasOverrides?: {
    getContext?: (canvas: HTMLCanvasElement) => RenderContext | null;
    raf?: RafSource;
    visibility?: VisibilitySource;
    rng?: () => number;
  };
}

interface Bootstrap {
  persistence: PersistenceController;
  store: GameStore;
  storageDisabled: boolean;
}

/**
 * T15 이월 메모 해소: `props.store` 주입 여부와 무관하게 항상 실제 driver로
 * persistence를 만들고 `load()`를 실행해 저장 비활성 여부를 판정한다(과거에는
 * store 주입 시 storageDisabled를 항상 false로 고정했다). store가 주입되면
 * load 결과의 상태값 자체는 버리고 storageDisabled 판정에만 쓴다.
 */
function bootstrap(props: AppProps): Bootstrap {
  const persistence = createPersistence(props.driver ?? createLocalStorageDriver());
  const { state, status } = persistence.load();
  return {
    persistence,
    store: props.store ?? createGameStore(state),
    storageDisabled: status === "disabled" || persistence.isDisabled(),
  };
}

function App(props: AppProps = {}) {
  const [{ persistence, store: initialStore, storageDisabled: initialStorageDisabled }] = useState(() =>
    bootstrap(props),
  );
  const [store, setStore] = useState(initialStore);
  const [storageDisabled, setStorageDisabled] = useState(initialStorageDisabled);

  const controller = useGameController(store, props.controllerOptions);

  /**
   * T22: store 변경(잔고·전적·설정)을 `persistence.save`로 지속 저장한다. store가 교체되면
   * (설정 변경·초기화) 이전 구독을 해제하고 현재 store에 다시 부착한다. 매 emit마다 저장하는
   * 단순한 방식을 택했다(store emit은 dispatch·adjustBalance·recordRaceResult 호출 시점에만
   * 발생해 애니메이션 프레임마다 발생하지 않으므로 write 빈도가 문제되지 않는다). 구독은
   * attach 시점에는 저장하지 않고 이후 emit부터 반응하므로, 설정 변경·초기화 경로가 store
   * 교체 직전에 수행하는 수동 저장과 중복되지 않는다.
   */
  useEffect(() => {
    const persistCurrent = (state: GameStoreState): void => {
      const result = persistence.save(toSavedState(state));
      setStorageDisabled(result.disabled);
    };
    return store.subscribe(persistCurrent);
  }, [store, persistence]);

  /**
   * T19 이월 메모 해소: 설정 변경을 store `settings` 반영·카탈로그 재생성으로 실연결한다.
   * `gameStore.ts`에는 설정을 갱신하는 API가 없으므로(touch 범위 밖), 현재 잔고·전적을
   * 그대로 들고 새 설정으로 store 인스턴스를 다시 만들어 교체한다(되돌리기 쉬운 결정).
   * PRD 4.9(음소거 상태 저장)에 따라 저장 계층에도 함께 반영한다.
   */
  const handleSettingsChange = useCallback(
    (settings: GameSettings) => {
      const current = store.getState();
      const nextSaved = toSavedState({ ...current, settings });
      const saveResult = persistence.save(nextSaved);
      setStorageDisabled(saveResult.disabled);
      setStore(createGameStore(nextSaved));
    },
    [store, persistence],
  );

  /** T19 이월 메모 해소: 초기화를 잔고·전적·설정 리셋과 저장 계층 리셋으로 실연결한다. */
  const handleReset = useCallback(() => {
    const defaults = createDefaultState();
    const saveResult = persistence.save(defaults);
    setStorageDisabled(saveResult.disabled);
    setStore(createGameStore(defaults));
  }, [persistence]);

  /**
   * 정산(settlement) 중에도 경주 화면을 유지해 완주 연출(피니시 배너·폭죽·우승마
   * 스포트라이트)이 정산 카드와 함께 보이게 한다. 로비 복귀 시 raceState가 null이
   * 되면서 캔버스가 내려간다.
   */
  const isRacePhase =
    controller.phase === "countdown" ||
    controller.phase === "racing" ||
    controller.phase === "finish" ||
    controller.phase === "settlement";

  return (
    <main className="app">
      <h1 className="app__title">브라우저 경마 베팅 게임</h1>
      <StorageBanner visible={storageDisabled} />
      <BalanceDisplay store={store} />

      {controller.phase === "lobby" && (
        <div className="lobby">
          <section className="horse-list" aria-label="출전마 목록">
            {controller.lobbyEntries.map((entry) => (
              <HorseCard key={entry.horse.id} entry={entry} />
            ))}
          </section>
          <BetPanel
            horses={controller.horses}
            balance={controller.balance}
            onConfirm={controller.handleBetConfirm}
          />
          <SettingsPanel
            settings={controller.settings}
            bankruptcyCount={controller.bankruptcyCount}
            onSettingsChange={handleSettingsChange}
            onReset={handleReset}
          />
        </div>
      )}

      {isRacePhase && (
        <section className="race-screen" aria-label="경주 화면">
          {controller.raceState && (
            <RaceCanvas
              initialState={controller.raceState}
              horses={controller.horses}
              machine={controller.machine}
              onFrame={controller.handleFrame}
              getContext={props.raceCanvasOverrides?.getContext}
              raf={props.raceCanvasOverrides?.raf}
              visibility={props.raceCanvasOverrides?.visibility}
              rng={props.raceCanvasOverrides?.rng}
            />
          )}
          <CommentaryFeed messages={controller.commentaryMessages} />
        </section>
      )}

      {controller.phase === "settlement" && controller.settlement && (
        <SettlementResult
          won={controller.settlement.won}
          payout={controller.settlement.payout}
          balanceAfter={controller.balance}
        />
      )}
    </main>
  );
}

export default App;
