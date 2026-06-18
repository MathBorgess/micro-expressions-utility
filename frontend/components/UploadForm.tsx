"use client";

import { type FormEvent, useState } from "react";
import { uploadMeeting } from "@/lib/api";
import { Button, Card, Label } from "@/components/ui";

export default function UploadForm({
  token,
  onUploaded,
}: {
  token: string;
  onUploaded: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file || !consent) return;
    setBusy(true);
    setError(null);
    try {
      await uploadMeeting(file, consent, token);
      setFile(null);
      setConsent(false);
      onUploaded();
    } catch {
      setError("Não foi possível enviar o vídeo.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-base font-semibold">Nova reunião</h2>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="file">Vídeo (MP4, ≤ 200 MB)</Label>
          <input
            id="file"
            type="file"
            accept="video/mp4,video/quicktime,video/webm"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-[13px] file:mr-3 file:rounded-md file:border file:border-line file:bg-white file:px-3 file:py-1.5 file:text-[13px]"
          />
        </div>
        <label className="flex items-start gap-2 text-[13px] text-muted">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            className="mt-0.5"
          />
          Tenho consentimento dos participantes para processar esta gravação.
        </label>
        {error && <p className="text-[13px] text-danger">{error}</p>}
        <Button type="submit" disabled={!file || !consent || busy}>
          {busy ? "Enviando…" : "Enviar e processar"}
        </Button>
      </form>
    </Card>
  );
}
