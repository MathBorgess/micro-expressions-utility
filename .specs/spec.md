Como Principal QA Architect, DevSecOps Specialist e AI Agent Solutions Engineer, consolidei as decisões arquiteturais e os requisitos técnicos do sistema. Abaixo está o documento definitivo de especificação técnica.

Você pode salvar o conteúdo abaixo diretamente como `HARNESS_SPEC.md` no repositório do projeto.

---

# Specification for Harness Engineering & Automated Validation Sandbox

## Visão Geral

Este documento define as diretrizes estritas de validação, limites computacionais e critérios de aceite que compõem o Harness Engineering Pipeline. Ele atua como o guardião automatizado (Gatekeeper) para todas as contribuições de código submetidas por agentes de IA no SaaS Lean de Análise Comportamental de Vendas.

---

## 1. Arquitetura do Test Harness (Esteira de Validação)

O pipeline de testes atuará como um bloqueio absoluto em regras de repositório, garantindo a qualidade do código antes de qualquer merge.

### Fluxo Lógico de Interceptação

* O agente submete um Pull Request com alterações de código.
* O Harness intercepta o código e executa uma checagem estática de tipos e formatação.
* Em seguida, o pipeline roda os testes unitários focados em rotas e lógicas de negócios isoladas.
* O pipeline executa testes de integração local injetando um banco de dados SQLite mockado em memória.
* O Harness executa a simulação ponta a ponta (E2E) cronometrada contra o arquivo de vídeo padrão.
* O pipeline aprova o Merge se 100% dos critérios forem atingidos, caso contrário, rejeita o build com logs de erro estruturados.

### Comandos de Checagem Estática

* O código passará por análise rigorosa de formatação utilizando o comando `ruff check .`.
* O código será avaliado contra erros de tipagem utilizando o comando `mypy --strict .`.

### Regras de Cobertura de Código (Code Coverage)

* A esteira exige um mínimo de 70% de cobertura de código.
* A cobertura deve focar exclusivamente nas regras de negócio, utilitários e rotas principais do framework FastAPI.
* Não há exigência de 100% de cobertura no MVP para manter a agilidade de desenvolvimento.
* O pipeline completo de testes de CI deve rodar em menos de 5 minutos.

---

## 2. Design dos Componentes de Mock (Dublês de Teste)

Para economizar recursos computacionais nas esteiras rápidas de CI, as integrações pesadas serão substituídas por Mocks determinísticos.

### API do Ollama (Fake Server)

* O Harness levantará um servidor local simulado para a API do Ollama.
* O mock responderá imediatamente com um texto estático formatado em Markdown padrão.
* Esta abordagem previne o alto consumo de hardware durante testes unitários regulares.

### Faster-Whisper e MediaPipe (JSON Spitting)

* Os modelos pesados de IA serão isolados por dublês fakes.
* O mock do MediaPipe não processará frames reais, mas retornará em milissegundos um JSON fixo de coordenadas pré-aprovadas.
* O mock do Faster-Whisper interceptará as chamadas de áudio e retornará blocos de texto predefinidos para validar as rotas.

---

## 3. Estruturação do Teste de Integração Ponta a Ponta (E2E)

A simulação completa é projetada para rodar localmente no Harness com parâmetros altamente controlados.

### Vídeo Padrão de Teste

* O arquivo de vídeo mock terá a duração exata de 10 segundos.
* O formato exigido é MP4 com um frame rate constante de 24 FPS.
* A resolução fixada do arquivo de simulação será de 640x480.
* A faixa de áudio conterá a frase em português: "Gostei do produto, mas precisamos discutir as condições de preço na próxima semana".

### Conversão de Tempo

* A biblioteca de medição calculará a sincronia dos eventos utilizando a fórmula nativa baseada nos metadados extraídos do arquivo:
$Timestamp\ (ms) = \left( \frac{Frame\ Index}{FPS} \right) \times 1000$

### Asserções do Algoritmo (`pytest`)

* O teste validará se o pipeline consegue gerar fisicamente o arquivo `.wav` de áudio.
* O teste garantirá que o retorno simulado do Whisper contenha estritamente as palavras-chave "produto" e "preço".
* O teste assegurará que o JSON do MediaPipe produziu pelo menos um evento rotulado com a chave `signal_type`.
* O teste confirmará que o relatório final simulado exibe um Markdown estruturado sob títulos, não vazio.
* O Harness gravará um arquivo JSON de referência e abortará o build por regressão se as saídas divergirem do esperado.
* Todo o pipeline de teste integrado deve finalizar seu processamento em menos de 3 minutos.

---

## 4. Políticas da Sandbox de Execução dos Agentes

Os agentes autônomos trabalharão em um ambiente Docker estrito e restrito.

### Restrições de Hardware (`docker-compose.harness.yml`)

* Os agentes executarão dentro de um container Docker controlado.
* A flag `mem_limit` será configurada para um limite rígido de 4 GB (`mem_limit: 4g`).
* A flag `cpus` fixará o acesso a no máximo 2 núcleos de processamento (`cpus: 2`).

### Isolamento e Telemetria

* O Harness vetará adições não aprovadas no `requirements.txt` ou `pyproject.toml`, bloqueando imediatamente o commit do agente.
* O acesso externo à internet de dentro da Sandbox será monitorado ou completamente bloqueado.
* O script de inicialização embrulhará a execução no utilitário de terminal `mprof` da biblioteca Python `memory_profiler`.
* O build será permanentemente reprovado se o pico de memória RAM cruzar o limiar de 2.5 GB durante a simulação.

---

## 5. Contrato OpenAPI e Critérios de Aceite de Merge (Gatekeeper)

A comunicação entre agentes e integrações será norteada pela veracidade técnica da documentação automática da API.

### Validação de Contratos

* O documento gerado nativamente pelo FastAPI na rota `/openapi.json` será a fonte única de verdade dos contratos.
* Os schemas serão validados estritamente pelo Pydantic, lançando erro 422 Unprocessable Entity para dados inválidos.
* Para manter a retrocompatibilidade, novos campos deverão utilizar instâncias de valores nulos padrão (ex: `Optional[str] = None`).
* A documentação viva `/docs` e o prefixo explicito `/api/v1/` garantirão a estabilidade das chamadas do front-end.

### Matriz Binária de Aprovação de Build (Go/No-Go)

| Critério de Validação do Harness | Condição de Aprovação (Go) | Ação em Caso de Falha (No-Go) |
| --- | --- | --- |
| **Checagem Estática de Tipagem** | Zero erros encontrados via comando `mypy --strict .` | Falha no Build. |
| **Cobertura de Código** | `>= 70%` de coverage nas pastas essenciais do FastAPI | Falha no Build. |
| **Testes Unitários / Mocks** | 100% de passagem nos testes com tempo total inferior a 5 minutos | Falha no Build. |
| **Teste End-to-End (E2E)** | O script detecta as palavras "preço" e "produto" usando o mock video | Rejeição por Regressão Semântica. |
| **Desempenho (CPU / Tempo)** | Simulação do vídeo mock executada em `< 3 minutos` | Falha por Timeout de Pipeline. |
| **Consumo de Memória (OOM)** | Telemetria `mprof` acusa consumo de RAM máximo `< 2.5 GB` | Rejeição por Risco de Out of Memory. |
| **Controle de Dependências** | Arquivo `requirements.txt` intocado sem pacotes externos não autorizados | Commit bloqueado imediatamente. |
----
Este documento estabelece o **Tech-Assessment & Implementation Roadmap** definitivo. Ele atua como uma especificação de requisitos executável, desenhada para guiar agentes de IA (como Devin ou AutoGPT) através de ciclos de desenvolvimento iterativos, garantindo a validação de cada componente contra as regras estritas do Harness Engineering.

---

# Tech-Assessment: Plano de Execução para Agentes Autônomos

## Visão Geral da Arquitetura de Implementação

O sistema será construído em uma arquitetura de orquestração local (Local-First), separada rigorosamente entre um servidor web assíncrono (FastAPI) e um pool de workers isolados em nível de sistema operacional (ProcessPoolExecutor).

### Cronograma de Sprints

| Sprint | Foco da Implementação | Objetivo Principal |
| --- | --- | --- |
| **Sprint 1** | Infraestrutura, Banco e Rotas Base | Estabelecer os contratos OpenAPI, banco SQLite e fila de processamento. |
| **Sprint 2** | Visão, Áudio e Processamento em Background | Integrar Mocks e bibliotecas reais (MediaPipe/Whisper) em processos isolados. |
| **Sprint 3** | Sincronização Temporal e Integração LLM | Construir a timeline JSON e gerar o relatório final em Markdown via Ollama. |
| **Sprint 4** | Frontend, Integração e Refinamento E2E | Implementar a interface Next.js e realizar testes finais no pipeline de testes E2E. |

---

## Sprint 1: Infraestrutura, Banco de Dados e Rotas Base

**Objetivo:** Construir o esqueleto do backend com FastAPI, configurar o controle de estado e garantir que a documentação OpenAPI reflita os contratos finais.

**Passos de Implementação (Agent Directives):**

* Configurar o ambiente restrito criando o arquivo `docker-compose.yml` com os limites exatos da Sandbox (máximo de 4 GB de RAM e 2 CPUs).
* Inicializar o projeto FastAPI mapeando todas as rotas sob o prefixo `/api/v1/`.
* Configurar a conexão nativa com SQLite utilizando SQLAlchemy ou SQLModel.
* Criar a tabela `jobs` com as colunas obrigatórias: `id`, `meeting_id`, `status` (aceitando apenas 'pending', 'processing', 'completed', 'failed'), `created_at`, `updated_at` e `error_log`.
* Implementar os schemas do Pydantic para validação de entrada (Upload de vídeo) e saída (Status e Relatório), garantindo que novos campos utilizem valores padrão para retrocompatibilidade.

**Validações do Harness (Gatekeeper):**

* O comando `mypy --strict .` deve retornar zero erros.
* As rotas devem retornar HTTP 422 para payloads inválidos automaticamente.
* O arquivo `/openapi.json` deve estar acessível e refletir os schemas implementados.

---

## Sprint 2: Workers de Processamento e Modelos de Visão/Áudio

**Objetivo:** Isolar o processamento de CPU pesada fora do loop principal do FastAPI, garantindo que a API não congele durante a análise.

**Passos de Implementação (Agent Directives):**

* Implementar o gerenciador de fila assíncrona utilizando `ProcessPoolExecutor` do Python, fixando a concorrência rígida em 1 job por vez (`concurrency=1`).
* Configurar a prioridade do worker no sistema operacional utilizando `nice -n 10` para evitar disputa de CPU com a API web.
* Criar o script de normalização de vídeo com `ffmpeg` para forçar a taxa de quadros a 24 FPS constantes (CFR) e codec H.264.
* Implementar a extração iterativa de frames utilizando geradores de streaming com `cv2.VideoCapture` do OpenCV, descartando o frame da memória logo após a análise.
* Instanciar o modelo Faster-Whisper (tamanho `base`) de forma global/singleton na inicialização do Worker, e configurar o MediaPipe para ser instanciado a cada novo job.

**Validações do Harness (Gatekeeper):**

* A cobertura de código (Code Coverage) nos diretórios `/app/core` e `/app/services` deve ser igual ou superior a 70%.
* O utilitário `mprof` deve confirmar que o processamento do vídeo padrão não ultrapassa o limite de 2.5 GB de RAM em nenhum momento.

---

## Sprint 3: Sincronização Temporal e Integração LLM

**Objetivo:** Agrupar os sinais faciais e a transcrição em uma timeline lógica, compactar o contexto e gerar o relatório Markdown final.

**Passos de Implementação (Agent Directives):**

* Implementar o algoritmo de conversão de tempo absoluto cruzando o índice do frame e o FPS nativo: $Timestamp\ (ms) = \left( \frac{Frame\ Index}{FPS} \right) \times 1000$.
* Construir a lógica heurística em Python que agrupa os sinais extraídos pelo MediaPipe (ex: `olhar_desviado`, `afastamento_da_tela`) dentro dos blocos de segmentos temporais gerados pelo Whisper.
* Criar o contador de tokens com bibliotecas como `tiktoken`. Se a união do prompt estruturado, transcrição e JSON de sinais ultrapassar 7.500 tokens, o agente deve engatilhar a sumarização hierárquica por blocos.
* Implementar a comunicação HTTP com a API local do Ollama (`llama3:8b`), instruindo o modelo via prompt a retornar exclusivamente texto estruturado em Markdown.

**Validações do Harness (Gatekeeper):**

* O sistema deve realizar o parse via Regex (ex: `re.search`) para validar se a resposta gerada contém obrigatoriamente os subtítulos exigidos, como `## 2. Objeções Identificadas`.
* Se a validação falhar estruturalmente, o código deve executar um retry automático reduzindo a temperatura do LLM para `temperature=0.2`.

---

## Sprint 4: Frontend, Integração e Refinamento E2E

**Objetivo:** Construir a interface de consumo e garantir que o ciclo completo de comunicação entre o cliente e o pipeline ocorra perfeitamente.

**Passos de Implementação (Agent Directives):**

* Levantar a aplicação Next.js utilizando TailwindCSS para estilização.
* Implementar a lógica de upload multipart via endpoint `POST /api/v1/meetings/upload`.
* Criar o mecanismo de consulta assíncrona (Polling) no front-end, realizando requisições GET a cada 5 segundos na rota `/api/v1/meetings/{id}/status` até receber o status `completed`.
* Implementar a biblioteca `react-markdown` para renderizar esteticamente a string Markdown devolvida pela rota `/api/v1/meetings/{id}/report`.
* Adicionar tratamento de erros globais com blocos `try/except` no backend, gravando tracebacks completos na coluna `error_log` para falhas.

**Validações do Harness (Gatekeeper):**

* A execução completa do script de teste End-to-End (E2E) com o vídeo padrão de 10 segundos deve durar menos de 3 minutos e retornar as palavras "preço" e "produto" na transcrição.
* Nenhuma biblioteca não autorizada deve constar no `requirements.txt` ou `pyproject.toml`.