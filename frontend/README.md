# Frontend — Insights de Vendas (Next.js)

UI do Sprint 4 seguindo o design system em [`../.specs/DESIGN.md`](../.specs/DESIGN.md):
Next.js (App Router) + React + Tailwind, fontes Inter + JetBrains Mono, 2 cores por tela
(neutro + acento `#5e6ad2`), bordas 1px, sem gradientes/sombras pesadas.

## Funcionalidades
- Login básico (`POST /api/v1/auth/login`).
- Upload multipart de vídeo com consentimento.
- Lista de reuniões com **polling de status a cada 5s** até `completed`.
- Render do relatório Markdown com `react-markdown`.

## Como rodar
```bash
cd frontend
cp .env.local.example .env.local   # ajuste NEXT_PUBLIC_API_URL se necessário
npm install
npm run dev                        # http://localhost:3000
```
O backend precisa estar no ar (`uv run uvicorn app.main:app --reload`) e o CORS já libera
`http://localhost:3000` por padrão.

> Observação: este frontend foi escrito como código-fonte; rode `npm install` para baixar as
> dependências (Node 18+). Credenciais de dev padrão: usuário `vendedor`, senha `changeme`.
