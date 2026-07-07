import { useEffect, useState } from "react";
import type { GameStore, GameStoreState } from "../store/gameStore";

/**
 * `GameStore`(subscribe/getState)를 React 컴포넌트에 잇는 구독 브리지 훅.
 *
 * `getState()`는 매 emit마다 새 객체를 반환하므로(`gameStore.ts`), `useSyncExternalStore`의
 * `getSnapshot`에 그대로 넘기면 참조가 매번 달라져 스냅샷 불안정으로 이어진다. 대신
 * subscribe + useState 패턴을 쓴다: 렌더 중에는 store를 읽지 않고, effect에서 구독을 걸어
 * emit이 있을 때만 setState한다. 마운트 시점에 상태가 이미 바뀌었을 가능성(초기 렌더~effect
 * 사이)에 대비해 구독 직후 최신 상태로 한 번 동기화한다.
 */
export function useGameStore(store: GameStore): GameStoreState {
  const [state, setState] = useState<GameStoreState>(() => store.getState());

  useEffect(() => {
    setState(store.getState());
    return store.subscribe(setState);
  }, [store]);

  return state;
}
