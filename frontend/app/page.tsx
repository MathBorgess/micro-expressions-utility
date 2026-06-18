"use client";

import { useEffect, useState } from "react";
import LoginForm from "@/components/LoginForm";
import UploadForm from "@/components/UploadForm";
import MeetingsPanel from "@/components/MeetingsPanel";

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    setToken(localStorage.getItem("token"));
  }, []);

  function handleLogin(value: string) {
    localStorage.setItem("token", value);
    setToken(value);
  }

  function handleLogout() {
    localStorage.removeItem("token");
    setToken(null);
  }

  if (!token) return <LoginForm onLogin={handleLogin} />;

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-8 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-semibold leading-tight tracking-tight">
            Insights de Vendas
          </h1>
          <p className="text-[13px] text-muted">
            Transforme gravações de reuniões em recomendações acionáveis.
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="text-[13px] text-muted transition-colors hover:text-ink"
        >
          Sair
        </button>
      </header>

      <div className="grid gap-6 md:grid-cols-[320px_1fr]">
        <UploadForm token={token} onUploaded={() => setRefreshKey((key) => key + 1)} />
        <MeetingsPanel token={token} refreshKey={refreshKey} />
      </div>
    </main>
  );
}
