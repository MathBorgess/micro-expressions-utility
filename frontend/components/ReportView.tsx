"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { getReport } from "@/lib/api";
import { Card } from "@/components/ui";

export default function ReportView({
  token,
  meetingId,
  onBack,
}: {
  token: string;
  meetingId: number;
  onBack: () => void;
}) {
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getReport(meetingId, token)
      .then((report) => {
        if (active) {
          setMarkdown(report.report_markdown);
          setLoading(false);
        }
      })
      .catch(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [meetingId, token]);

  return (
    <Card className="p-6">
      <button onClick={onBack} className="mb-4 text-[13px] text-muted transition-colors hover:text-ink">
        ← Voltar
      </button>
      {loading ? (
        <p className="text-[13px] text-muted">Carregando relatório…</p>
      ) : markdown ? (
        <article className="report flex flex-col gap-3">
          <ReactMarkdown>{markdown}</ReactMarkdown>
        </article>
      ) : (
        <p className="text-[13px] text-muted">Relatório indisponível.</p>
      )}
    </Card>
  );
}
