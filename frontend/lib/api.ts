// Cliente HTTP do backend FastAPI. Base configurável via NEXT_PUBLIC_API_URL.

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface MeetingSummary {
  id: number;
  filename: string;
  status: JobStatus;
  created_at: string;
}

export interface MeetingReport {
  meeting_id: number;
  status: JobStatus;
  report_markdown: string | null;
}

function authHeaders(token: string | null): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function login(username: string, password: string): Promise<string> {
  const res = await fetch(`${BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Credenciais inválidas");
  const data = (await res.json()) as { access_token: string };
  return data.access_token;
}

export async function listMeetings(token: string | null): Promise<MeetingSummary[]> {
  const res = await fetch(`${BASE}/api/v1/meetings/`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Falha ao listar reuniões");
  return (await res.json()) as MeetingSummary[];
}

export async function uploadMeeting(
  file: File,
  consent: boolean,
  token: string | null,
): Promise<{ meeting_id: number }> {
  const form = new FormData();
  form.append("file", file);
  form.append("consent", String(consent));
  const res = await fetch(`${BASE}/api/v1/meetings/upload`, {
    method: "POST",
    headers: authHeaders(token),
    body: form,
  });
  if (!res.ok) throw new Error("Falha no upload");
  return (await res.json()) as { meeting_id: number };
}

export async function getReport(id: number, token: string | null): Promise<MeetingReport> {
  const res = await fetch(`${BASE}/api/v1/meetings/${id}/report`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Falha ao buscar relatório");
  return (await res.json()) as MeetingReport;
}

export async function deleteMeeting(id: number, token: string | null): Promise<void> {
  const res = await fetch(`${BASE}/api/v1/meetings/${id}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Falha ao excluir reunião");
}
