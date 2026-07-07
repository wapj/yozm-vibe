export interface StorageBannerProps {
  visible: boolean;
}

/** PRD 4.4·6번: 저장이 비활성화된 경우에만 안내를 노출한다. */
export function StorageBanner({ visible }: StorageBannerProps) {
  if (!visible) return null;

  return (
    <div className="storage-banner" role="alert">
      저장이 비활성화되어 있습니다. 이 브라우저에서는 잔고와 전적이 저장되지 않습니다.
    </div>
  );
}
