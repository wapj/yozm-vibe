import { useEffect } from "react";

type Props = { message: string; onClose: () => void; durationMs?: number };

export function Toast({ message, onClose, durationMs = 4000 }: Props) {
  useEffect(() => {
    const id = setTimeout(onClose, durationMs);
    return () => clearTimeout(id);
  }, [onClose, durationMs]);
  return (
    <div role="status" aria-live="polite" data-testid="toast">
      {message}
    </div>
  );
}
