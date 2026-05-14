export function loadBalance(storage) {
  if (!storage) return 1000;
  const raw = storage.getItem("balance");
  if (raw === null) return 1000;
  const parsed = Number.parseInt(raw, 10);
  if (Number.isNaN(parsed) || parsed < 0) return 1000;
  return parsed;
}

export function saveBalance(storage, value) {
  if (!storage) return;
  storage.setItem("balance", String(Math.trunc(value)));
}

export function loadMuted(storage) {
  if (!storage) return false;
  return storage.getItem("muted") === "1";
}

export function saveMuted(storage, value) {
  if (!storage) return;
  storage.setItem("muted", value ? "1" : "0");
}
