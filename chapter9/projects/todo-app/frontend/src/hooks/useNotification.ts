import { useCallback, useState } from "react";

type NotifyFn = (title: string, body: string, fallback: (msg: string) => void) => void;

export function useNotification() {
  const [permission, setPermission] = useState<NotificationPermission>(() =>
    typeof Notification === "undefined" ? "denied" : Notification.permission,
  );

  const requestPermission = useCallback(async (): Promise<NotificationPermission> => {
    if (typeof Notification === "undefined") return "denied";
    try {
      const result = await Notification.requestPermission();
      setPermission(result);
      return result;
    } catch {
      setPermission("denied");
      return "denied";
    }
  }, []);

  const notify: NotifyFn = useCallback(
    (title, body, fallback) => {
      if (typeof Notification === "undefined" || permission !== "granted") {
        fallback(body);
        return;
      }
      try {
        new Notification(title, { body });
      } catch {
        fallback(body);
      }
    },
    [permission],
  );

  return { permission, requestPermission, notify };
}
