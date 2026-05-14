export async function fetchHealth(): Promise<string> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error("health check failed");
  const data = (await res.json()) as { status: string };
  return data.status;
}
