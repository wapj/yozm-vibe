type Props = { taskId: number; onYes: () => void; onNo: () => void };

export function NextFocusPromptDialog({ taskId, onYes, onNo }: Props) {
  return (
    <div role="dialog" aria-modal="true" data-testid="next-focus-prompt-dialog">
      <p>휴식이 끝났습니다. 다음 집중 세션을 시작할까요? (task #{taskId})</p>
      <button type="button" onClick={onYes} data-testid="next-focus-yes">예</button>
      <button type="button" onClick={onNo} data-testid="next-focus-no">아니오</button>
    </div>
  );
}
