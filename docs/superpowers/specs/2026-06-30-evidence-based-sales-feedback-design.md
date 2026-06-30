# Evidence-Based Sales Feedback — Design Spec

**Data:** 2026-06-30  
**Escopo:** Opção A — visão científica ampla + caminho pragmático para o repo local-first  
**Status:** Aprovado para implementação (Fase 1)

---

## 1. Executive Summary

O sistema atual (`MediaPipe Face Mesh` → heurísticas geométricas → timeline Whisper → prompt Ollama) produz relatórios que **interpretam** comportamento como emoção/objeção/engajamento, apesar do PRD declarar o oposto. A causa raiz não é só o LLM: a **representação facial é fraca** (gaze proxy via nariz, confiança fixa 1.0), o **contexto conversacional é mínimo** (só keywords de resistência) e o **prompt incentiva inferência mental** ("objeções identificadas", "alto engajamento").

**Objetivo:** Maximizar **confiabilidade, calibração, explicabilidade e utilidade** para vendedores B2B, produzindo **observações evidenciadas** com hipóteses alternativas e scores de confiança — nunca leitura de mente.

**Estratégia (Opção A):**

| Camada | Ideal (literatura) | Pragmático (este repo, allowlist atual) |
|--------|-------------------|-------------------------------------------|
| Percepção | AUs FACS + gaze 3D + vídeo transformers | MediaPipe iris + pose geométrica + face quality + optical flow leve (cv2/numpy) |
| Temporal | Apex detection MER + modelos seqüenciais | Janelas multiescala + suavização + mudanças de comportamento |
| Multimodal | Fusão áudio-vídeo-texto treinada | Transcrição + prosódia heurística (energia/silêncio) + sincronização temporal |
| Raciocínio | LLM com structured output + calibrador | Prompt evidence-first + validação estrutural + lista de frases proibidas |
| Avaliação | MER-F1 + ECE + estudo A/B com vendedores | Harness estendido + golden set interno + acordo inter-anotador |

**Legenda de evidência (usada em todo o documento):**

- **[LIT]** — suportado por literatura revisada por pares
- **[ENG]** — engenharia / boas práticas da indústria, sem consenso científico forte
- **[HYP]** — hipótese experimental a validar

---

## 2. Current Weaknesses (Failure Analysis — Part 1)

### 2.1 Pipeline de percepção

| Modo de falha | Manifestação no sistema | Severidade |
|---------------|-------------------------|------------|
| Face detection miss | `multi_face_landmarks` vazio → frame descartado silenciosamente | Alta |
| Landmark drift | MediaPipe em vídeo comprimido/baixa luz → jitter em `face_center_x/y` | Alta |
| Gaze falso | `looking_at_screen` = nariz perto do centro do frame **[ENG]** | Crítica |
| Pose confundida com emoção | Aceno vertical classificado sem contexto de fala | Alta |
| Oclusão (mão, óculos, máscara) | Landmarks instáveis, confiança ainda 1.0 | Alta |
| Iluminação / WB | Contraste baixo degrada mesh; sem face quality gate | Média |
| Compressão H.264 | Blocos 8×8, ghosting em bordas faciais | Média |
| FPS baixo (<15) | Perda de micro-movimentos; duração de gaze subestimada | Média |
| Optical flow noise | Não implementado; se adicionado sem gate, amplifica ruído **[HYP]** | — |
| Alinhamento facial pobre | Sem normalização canônica; métricas não comparáveis entre frames | Alta |
| Cross-subject / cross-cultural | Limiares fixos (`GAZE_AWAY_MIN_SECONDS=3.0`) **[LIT]** variabilidade inter-indivíduo | Alta |
| Apex frame | Sem localização de pico de movimento; eventos em frame arbitrário | Média |
| Macro-expression contamination | Gestos de cabeça tratados como sinais afetivos | Alta |
| Micro-expression rarity | MER: ~3–4 Hz, duração 40–200 ms **[LIT]** — invisível em heurísticas de 6 frames | Crítica para MER; baixa para MVP observacional |

### 2.2 Interpretação e LLM

| Modo de falha | Evidência |
|---------------|-----------|
| Prompt hallucination | SYSTEM_PROMPT pede "objeções" e "engajamento" sem exigir citação de evidência |
| LLM overconfidence | Sem campo de confiança; temperatura 0.7 default |
| Label ambiguity | "Resistência" = keyword + olhar_desviado (pode ser pensamento) |
| Thinking vs disagreement | Indistinguível só com face **[LIT]** |
| Attention vs interest | Mesma ambiguidade **[LIT]** |
| Listener not looking at presenter | Em calls gravadas, "tela" ≠ apresentador |
| Dataset bias | Treino implícito do LLM em narrativas emocionais de vendas |

### 2.3 Dados e avaliação

- Sem golden set anotado para calibração
- E2E valida estrutura Markdown, não veracidade comportamental
- Confiança heurística não calibrada (não é probabilidade)

---

## 3. Scientific Limitations (Part 2)

### 3.1 O que a ciência sustenta fortemente **[LIT]**

1. **Emoção não é diretamente observável** — expressões são **ações sociais** mediadas por contexto (Barrett, 2017; Fridlund, 1994). Inferir estado interno a partir de face isolada tem baixa validade ecológica.

2. **Micro-expressões são raras e probabilísticas** — taxas baixas em dados espontâneos; detecção automática tem recall limitado mesmo em MER (Li et al., 2022 survey).

3. **Mesma combinação de AUs → múltiplos estados** — AU6+AU12 pode ser sorriso social, máscara, ou esforço cognitivo dependendo de postura, voz e turno (Krumhuber et al., 2019).

4. **Contexto multimodal é necessário** — fusão face+voz+linguagem supera unimodal em afeto **quando** o ground truth é rotulagem de vídeo completo, não micro-sinal isolado (Poria et al., 2017; Gandhi & Nagarajan, 2023 surveys).

5. **Comprador não revela "confiança" na face** — trust em vendas correlaciona mais com **conteúdo verbal, reciprocidade e histórico** do que com AUs (Nguyen et al., 2018 — cautela: domínio específico).

6. **Calibração importa** — modelos de afeto frequentemente overconfident; ECE e reliability diagrams são padrão (Guo et al., 2017).

### 3.2 O que permanece especulativo **[HYP]**

- Mapear "afastamento_da_tela" → desengajamento comercial
- Optical flow facial sem AUs → resistência a preço
- LLM local 8B raciocínio causal multimodal sem structured grounding
- Transfer direto de MER-CNN para reuniões Zoom com 1 rosto

### 3.3 Implicação de produto

O assistente deve operar como **analista comportamental conservador**: relatar **mudanças observáveis** sincronizadas ao **tópico da negociação**, nunca como detector de emoção.

---

## 4. Vision Model Improvements (Part 3)

Comparativo resumido (ideal vs pragmático):

| Técnica | Vantagem | Desvantagem | Repo |
|---------|----------|-------------|------|
| RetinaFace/SCRFD | Robustez pose/occlusão **[LIT]** | Nova dep | Fase 3+ **[HYP]** |
| Face alignment 5/68 pts | Normaliza AUs **[LIT]** | Pipeline extra | Fase 2 — warp leve com MediaPipe **[ENG]** |
| MediaPipe iris | Gaze melhor que nariz **[ENG]** | Não é gaze 3D real | **Fase 1** |
| Head pose (PnP landmarks) | Separa olhar vs rotação **[LIT]** | Ruído em baixa res | **Fase 1** |
| AU detection (OpenFace/py-feat) | Vocabulário FACS interpretável **[LIT]** | Deps pesadas | Fase 3 — requer aprovação allowlist |
| Optical flow (Farneback cv2) | Movimento fino lábios/sobrancelha **[ENG]** | Sensível a compressão | Fase 2 opcional |
| Temporal smoothing (EMA/Kalman) | Estabiliza landmarks **[ENG]** | Atraso temporal | **Fase 1** |
| Face quality score (blur, size) | Reduz falsos positivos **[LIT]** | Pode descartar dados | **Fase 1** |
| Apex detection | Alinha evento ao pico **[LIT]** MER | Complexo | Fase 2 |
| Video transformers (TimeSformer) | Representação rica **[LIT]** | GPU, dados | Longo prazo |
| Self-supervised (MAE-V) | Generalização **[LIT]** | Treino | Longo prazo |

**Fase 1 (allowlist):** `face_quality.py`, iris gaze, pose yaw/pitch proxy, confiança por frame, filtro de frames ruins antes de `detect_signals`.

---

## 5. Multimodal Improvements (Part 4)

Cada modalidade **reduz ambiguidade** quando cruzada:

| Modalidade | O que observa | Desambigua |
|------------|---------------|------------|
| Transcrição | Objeção explícita, perguntas | Face ambígua + verbal claro → foco no verbal |
| Turn-taking | Quem fala quando | Olhar desviado durante fala própria vs escuta |
| Silêncio pós-pergunta | Latência de resposta | Pensamento vs resistência |
| Prosódia (energia, pausas) | Hesitação | Concordância verbal fraca + pausa longa |
| Head nod + verbal "sim" | Aceno positivo | Engajamento mais plausível **[ENG]** |
| Keyword + sinal facial | Co-ocorrência temporal | Hipótese resistência, não conclusão |
| Semantic (LLM) | Tópico preço/ROI | Ancora interpretação ao negócio |

**Fase 1:** `conversation.py` — gaps entre segmentos, contagem de perguntas, flags `verbal_objection`, `verbal_agreement` (regex conservador).

**Fase 2:** energia RMS por segmento via numpy no WAV já extraído (sem nova dep).

---

## 6. Prompt Improvements (Part 5)

### 6.1 Princípios

1. Separar **Observação** / **Hipótese** / **Recomendação**
2. Exigir timestamp + modalidade para cada afirmação
3. Proibir verbos de estado mental sem evidência convergente
4. Forçar ≥2 hipóteses alternativas quando confiança < 0.7
5. Incluir score de confiança 0–1 por bloco

### 6.2 Template (resumo — versão completa no plano de implementação)

```text
Você é um analista de comunicação comercial. NUNCA afirme emoções ou intenções internas.

Regras:
- OBSERVAÇÃO: apenas comportamento mensurável (olhar, postura, gesto, fala, silêncio).
- INTERPRETAÇÃO: sempre com "pode indicar" + alternativas.
- PROIBIDO sem ≥2 modalidades: "odiou", "perdeu confiança", "ficou com medo", "rejeitou".
- Cite [HH:MM:SS] e a fonte (vídeo/transcrição/silêncio).

Estrutura obrigatória:
# Relatório de Análise Comercial
## 1. Comportamentos Observados
## 2. Linha do Tempo
## 3. Mudanças de Comportamento
## 4. Hipóteses Interpretativas (com alternativas)
## 5. Contexto Conversacional
## 6. Confiança e Limitações
## 7. Perguntas de Follow-up Sugeridas
## 8. Oportunidades e Coaching
```

---

## 7. LLM Reasoning Improvements

| Melhoria | Tipo | Fase |
|----------|------|------|
| Observation packet JSON no prompt | **[ENG]** grounding | 1 |
| Validação de cabeçalhos + frases proibidas | **[ENG]** | 1 |
| Retry temperature 0.2 (já existe) | **[ENG]** | 1 |
| Chain-of-thought interno, output só Markdown | **[HYP]** | 2 |
| Structured JSON intermediário + render | **[ENG]** | 2 |
| RAG sobre playbook de vendas | **[HYP]** | 3 |

---

## 8. Confidence Calibration

**Definição operacional (MVP):**

```
confidence = min(face_quality, tracking_stability) * modality_agreement_bonus
```

- `modality_agreement_bonus`: 1.0 se verbal+visual alinhados; 0.6 se só visual; 0.8 se só verbal explícito
- Reportar ECE quando houver labels humanos **[LIT]**
- Separar **epistemic** (incerteza do modelo) de **aleatoric** (ruído de vídeo) **[ENG]**

---

## 9. Evaluation Pipeline (Part 8)

### 9.1 Métricas offline

| Métrica | Alvo Fase 1 | Alvo Fase 3 |
|---------|-------------|-------------|
| Face tracking stability (ID switch rate) | <5% frames | <2% |
| % frames face_quality > 0.5 | >70% | >85% |
| Forbidden phrase rate no relatório | 0% | 0% |
| Structural validity | >95% | >99% |
| Human usefulness (Likert 1–5) | ≥3.5 | ≥4.0 |

### 9.2 Protocolo humano

- 30 clipes anotados: observação / não-observação (não emoção)
- Cohen's κ entre 2 anotadores **[LIT]** alvo κ > 0.6
- Comparar relatório v1 vs v2 em estudo within-subject **[HYP]**

### 9.3 A/B com vendedores

- Métrica primária: qualidade do follow-up (cego)
- Secundária: tempo de leitura, NPS do relatório, taxa de "insight acionável"

---

## 10. Research Backlog (Part 7 — Datasets)

| Dataset | Uso | Fase |
|---------|-----|------|
| DISFA, BP4D | AU transfer | 3+ |
| MER2020-24 | Apex, MER | Longo prazo |
| IEMOCAP, MELD | Multimodal afeto (cautela domínio) | Pesquisa |
| CallCenter, Switchboard | Turn-taking | 2 |
| Vendas internas anonimizadas | Domain adaptation | Contínuo |

Estratégias: weak supervision com keywords **[ENG]**, pseudo-labels conservadores, active learning em frames de baixa confiança, cross-dataset eval antes de deploy.

---

## 11. Architecture Recommendations

```
video + audio
    ↓
[face-analysis] → FrameMetrics* + quality_score
    ↓
[signals] → SignalEvent* (comportamental, não emocional)
    ↓
[conversation] → ConversationFeatures (gaps, verbal flags)
    ↓
[observations] → BehavioralObservation* (evidence + hypotheses + confidence)
    ↓
[timeline] → TimelineEntry enriquecida
    ↓
[context/prompt] → evidence-first prompt
    ↓
[report_builder] → validate structure + forbidden phrases
```

**Novos módulos:** `core/face_quality.py`, `core/conversation.py`, `core/observations.py`  
**Modificar:** `prompt.py`, `report.py`, `mediapipe_real.py`, `timeline.py`, mocks, testes E2E

**Schema version:** incrementar `SCHEMA_VERSION` → `2` com campo `observations` opcional retrocompatível.

---

## 12. Risk Analysis

| Risco | Mitigação |
|-------|-----------|
| Relatório mais longo → fadiga | Resumo executivo no topo; coaching acionável |
| Falsos negativos (cautela excessiva) | Destacar "padrões que merecem follow-up" |
| Vendedor ignora incerteza | UI futura: badges de confiança |
| Regressão E2E | Atualizar `STATIC_REPORT_MARKDOWN` e headers |
| Scope creep MER | MER fora do MVP; só observações macro |

---

## 13. Suggested Experiments

1. **E1:** Iris vs nariz — % redução de falsos `olhar_desviado` em 10 clipes rotulados **[HYP]**
2. **E2:** Com vs sem face quality gate — precisão de eventos **[HYP]**
3. **E3:** Prompt v1 vs v2 — taxa de frases proibidas (automático) + avaliação humana **[HYP]**
4. **E4:** +conversation features — κ observação humana **[HYP]**

---

## 14. Prioritized Roadmap (Part 9)

| Horizonte | Entregas | Impacto | Complexidade |
|-----------|----------|---------|--------------|
| **Quick wins (2 sem)** | Prompt evidence-first, novo schema relatório, observations layer, face quality, iris gaze, conversation gaps | Alto | Baixa–Média |
| **Médio (1–2 meses)** | Pose 3D proxy, optical flow leve, prosódia RMS, apex heurístico, golden set 30 clipes | Alto | Média |
| **Pesquisa (3–6 meses)** | AU detector, calibração ECE, structured JSON LLM, avaliação κ | Muito alto | Alta |
| **Longo prazo (6–18 meses)** | Video transformer, domain adaptation vendas, A/B conversão | Transformacional | Muito alta |

---

## Referências selecionadas

- Barrett, L. F. (2017). *How Emotions Are Made.*
- Fridlund, A. J. (1994). Human facial expression as social display.
- Li, S. et al. (2022). Micro-expression survey.
- Poria, S. et al. (2017). Context-aware multimodal fusion.
- Guo, C. et al. (2017). On calibration of modern neural networks.
- Krumhuber, E. et al. (2019). Social context of facial displays.

---

*Próximo passo: implementar Fase 1 conforme plano em `docs/superpowers/plans/2026-06-30-evidence-based-sales-feedback.md`.*
