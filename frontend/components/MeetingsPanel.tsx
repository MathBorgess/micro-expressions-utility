"use client";

import { useCallback, useEffect, useState } from "react";
import { listMeetings, type MeetingSummary } from "@/lib/api";
import { Card, StatusBadge } from "@/components/ui";
import ReportView from "@/components/ReportView";

const POLL_INTERVAL_MS = 5000;

export default function MeetingsPanel({
  token,
  refreshKey,
}: {
  token: string;
  refreshKey: number;
}) {
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [selected, setSelected] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    try {
      setMeetings(await listMeetings(token));
    } catch {
      /* erro de rede transitório — silencioso até o próximo poll */
    }
  }, [token]);

  useEffect(() => {
    void refresh();
  }, [refresh, refreshKey]);

  // Polling de status a cada 5s enquanto houver reuniões em andamento.
  useEffect(() => {
    const inProgress = meetings.some((m) => m.status === "pending" || m.status === "processing");
    if (!inProgress) return;
    const id = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [meetings, refresh]);

  if (selected !== null) {
    return <ReportView token={token} meetingId={selected} onBack={() => setSelected(null)} />;
  }

  return (
    <Card>
      <div className="border-b border-line px-6 py-4">
        <h2 className="text-base font-semibold">Reuniões</h2>
      </div>
      {meetings.length === 0 ? (
        <p className="px-6 py-8 text-[13px] text-muted">
          Nenhuma reunião ainda. Envie um vídeo para começar.
        </p>
      ) : (
        <ul>
          {meetings.map((meeting) => (
            <li key={meeting.id}>
              <button
                onClick={() => meeting.status === "completed" && setSelected(meeting.id)}
                disabled={meeting.status !== "completed"}
                className="flex w-full items-center justify-between gap-4 border-b border-line px-6 py-3 text-left transition-colors hover:bg-page disabled:cursor-default disabled:hover:bg-white"
              >
                <span className="min-w-0 truncate text-[14px]">{meeting.filename}</span>
                <StatusBadge status={meeting.status} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
