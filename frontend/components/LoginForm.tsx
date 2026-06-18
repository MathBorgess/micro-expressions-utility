"use client";

import { type FormEvent, useState } from "react";
import { login } from "@/lib/api";
import { Button, Card, Input, Label } from "@/components/ui";

export default function LoginForm({ onLogin }: { onLogin: (token: string) => void }) {
  const [username, setUsername] = useState("vendedor");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      onLogin(await login(username, password));
    } catch {
      setError("Credenciais inválidas.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-6">
      <Card className="p-6">
        <h1 className="mb-1 text-xl font-semibold tracking-tight">Entrar</h1>
        <p className="mb-6 text-[13px] text-muted">Acesse para analisar suas reuniões.</p>
        <form onSubmit={submit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="username">Usuário</Label>
            <Input
              id="username"
              value={username}
              autoComplete="username"
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="password">Senha</Label>
            <Input
              id="password"
              type="password"
              value={password}
              autoComplete="current-password"
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-[13px] text-danger">{error}</p>}
          <Button type="submit" disabled={loading}>
            {loading ? "Entrando…" : "Entrar"}
          </Button>
        </form>
      </Card>
    </main>
  );
}
