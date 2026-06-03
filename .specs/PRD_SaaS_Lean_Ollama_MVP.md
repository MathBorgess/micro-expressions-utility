# PRD — SaaS Lean de Suporte a Vendas com Insights Comportamentais (Local-First)

**Versão:** 2.0 (Lean MVP)  
**Data:** Maio/2026  
**Status:** MVP para Validação de Mercado

---

# 1. Visão do Produto

## Resumo Executivo

O produto é um SaaS enxuto para vendedores B2B que transforma gravações de reuniões em insights acionáveis utilizando:

- Transcrição automática de áudio
- Análise facial baseada em landmarks
- LLM local via Ollama
- Relatórios automáticos pós-reunião

O objetivo não é detectar mentiras ou estados emocionais com certeza.

O sistema busca identificar possíveis sinais de:

- Interesse
- Engajamento
- Confusão
- Resistência
- Mudanças comportamentais

e transformá-los em recomendações práticas para o vendedor.

---

## Hipótese Principal

Se vendedores receberem análises automáticas sobre:

- Momentos de maior interesse
- Possíveis objeções
- Trechos críticos da conversa

então conseguirão melhorar follow-ups e aumentar sua taxa de conversão.

---

# 2. Público-Alvo

## Persona Principal (MVP)

### Executivo de Vendas B2B

Perfil:

- SDR
- Account Executive
- Closer
- Consultor Comercial

Objetivos:

- Fechar mais negócios
- Melhorar follow-ups
- Identificar objeções ocultas

Dores:

- Calls longas
- Muitas informações dispersas
- Dificuldade para revisar reuniões

---

## Fora do Escopo do MVP

Não será desenvolvido inicialmente:

- Dashboard de gestores
- Coaching de equipe
- Benchmarking organizacional
- Analytics corporativo

---

# 3. Objetivos do MVP

## Objetivo Principal

Validar se vendedores percebem valor em análises automáticas de reuniões.

---

## KPIs de Validação

### Produto

- 30 usuários ativos
- 100 reuniões processadas
- 50% dos usuários retornando após primeira análise

### Uso

- Tempo médio de leitura do relatório
- Número de reuniões processadas por usuário

### Negócio

- Entrevistas qualitativas
- NPS
- Taxa de conversão para plano pago

---

# 4. Escopo do MVP

## RF-001 — Upload da Reunião

### Descrição

O usuário poderá:

Opção 1:

- Fazer upload manual de vídeo

Formatos:

- MP4
- MOV
- WEBM

Opção 2 (futuro próximo):

- Extensão Chrome para gravar tela e webcam

---

### Fora do MVP

Não implementar:

- Zoom SDK
- Microsoft Teams SDK
- Google Meet SDK
- Bots de gravação

---

## RF-002 — Extração de Dados Faciais

### Objetivo

Extrair indicadores faciais simples de baixo custo computacional.

### Tecnologia

MediaPipe Face Mesh

### Dados Extraídos

Exemplos:

- Direção do olhar
- Frequência de piscadas
- Movimentos de cabeça
- Alterações faciais relevantes

### Saída

JSON estruturado.

Exemplo:

```json
{
  "timestamp": "00:12:15",
  "signal": "queda_engajamento",
  "confidence": 0.74
}
```

Não haverá classificação emocional complexa.

---

## RF-003 — Transcrição Automática

### Objetivo

Converter fala em texto.

### Tecnologia

Whisper local

Alternativas:

- Faster-Whisper
- Whisper.cpp

### Saída

```text
00:05:12 Cliente:
"Precisamos avaliar orçamento."
```

---

## RF-004 — Timeline de Eventos

Combinar:

- Transcrição
- Dados faciais

Gerando eventos como:

- Possível objeção
- Queda de atenção
- Aumento de interesse

Exemplo:

```text
05:12 → Cliente menciona orçamento
05:15 → Mudança facial relevante
```

---

## RF-005 — Resumo Pós-Reunião com Ollama

### Fluxo Principal

1. Upload do vídeo
2. Extração de áudio
3. Transcrição via Whisper
4. Extração facial via MediaPipe
5. Conversão dos sinais para JSON
6. Envio para Ollama
7. Geração do relatório

---

### Contexto enviado ao Ollama

#### Transcrição

```text
[Vendedor]
...
[Cliente]
...
```

#### Timeline Comportamental

```json
[
  {
    "time":"05:12",
    "signal":"queda_engajamento"
  },
  {
    "time":"17:30",
    "signal":"aumento_interesse"
  }
]
```

---

### Prompt Base

O Ollama receberá:

- Transcrição completa
- Timeline dos sinais faciais

E deverá gerar:

1. Resumo executivo
2. Principais objeções
3. Momentos relevantes
4. Próximos passos sugeridos
5. Riscos da negociação

---

### Exemplo de Saída

```markdown
## Principais Objeções

- Preço
- Tempo de implementação

## Momentos de Interesse

17:30 — Cliente solicitou demonstração.

## Próximos Passos

- Enviar proposta
- Agendar reunião técnica
```

---

# 5. Arquitetura Lean

## Frontend

- Next.js
- React
- Tailwind

---

## Backend

Opção preferencial:

- FastAPI (Python)

ou

- NestJS (Node)

Escolher apenas um backend.

---

## Banco

MVP Local:

- SQLite

Produção Inicial:

- PostgreSQL
- ou Supabase

---

## IA

### Transcrição

- Faster-Whisper

### Visão Computacional

- MediaPipe

### LLM

- Ollama

Modelos possíveis:

- Llama 3
- Qwen
- Mistral

---

## Filas

Fila simples:

- Banco de dados
- ou Redis

Processamento sequencial.

Sem Kafka.

Sem RabbitMQ.

---

## Infraestrutura

### Desenvolvimento

Docker Compose

Serviços:

- App
- Banco
- Ollama

---

### Produção Inicial

Hospedagem simples:

- VPS
- Hetzner
- Contabo
- DigitalOcean

Meta:

US$10–30/mês

---

# 6. Requisitos Não Funcionais

## Escalabilidade

Meta MVP:

- Até 500 reuniões/mês

Processamento:

- Assíncrono
- Sequencial

Sem necessidade de escala horizontal.

---

## Performance

Meta:

- Relatório gerado em até 15 minutos

---

## Segurança

- HTTPS
- Senhas criptografadas
- Controle de acesso básico

---

## Privacidade

- Consentimento obrigatório
- Exclusão manual de vídeos
- Retenção configurável

---

## IA Responsável

O sistema não deve:

- Detectar mentiras
- Diagnosticar emoções
- Inferir condições psicológicas
- Inferir condições médicas

---

# 7. Critérios de Aceite

## RF-001

- Upload concluído
- Vídeo armazenado
- Consentimento registrado

---

## RF-002

- Landmarks detectados
- JSON gerado

---

## RF-003

- Transcrição disponível

---

## RF-004

- Timeline exibida ao usuário

---

## RF-005

- Relatório gerado pelo Ollama
- Objeções identificadas
- Próximos passos sugeridos

---

# 8. Principais Riscos

## Produto

Os vendedores podem não perceber valor suficiente nos insights.

---

## Técnico

Modelos locais podem gerar análises inconsistentes.

---

## Legal

Necessidade de consentimento explícito para gravação e processamento.

---

# 9. Roadmap

## Fase 1 — MVP (4–6 semanas)

- Upload de vídeo
- Whisper
- MediaPipe
- Ollama
- Timeline
- Relatório pós-reunião

Objetivo:

Validar disposição de pagamento.

---

## Fase 2

- Extensão Chrome
- CRM básico
- Melhorias de prompts

---

## Fase 3

- Coach em tempo real
- Benchmarking
- Multiusuário

---

## Fase 4

- APIs
- Enterprise
- Analytics avançados

---

# 10. Decisões Estratégicas de MVP

## O que NÃO será construído

- Kubernetes
- AWS complexa
- Dashboard de gestor
- Integrações Zoom/Meet/Teams
- Modelos proprietários pagos
- Processamento distribuído
- Microserviços

---

## Filosofia

Validar primeiro.

Escalar depois.

Todo o sistema deve conseguir rodar localmente em uma única máquina utilizando:

- Docker Compose
- SQLite/PostgreSQL
- MediaPipe
- Whisper
- Ollama
