# Specification Discovery Questionnaire — Harness Engineering
## SaaS Lean de Análise Comportamental de Vendas (Local-First)

**Objetivo:** Extrair decisões arquiteturais definitivas antes da criação do Specification for Harness Engineering, permitindo que agentes de IA implementem, validem e evoluam o sistema com segurança.

---

# Bloco 1 — Visão Arquitetural e Limites do Sistema

## Decisões Fundamentais

1. O backend será oficialmente padronizado em FastAPI ou existe alguma possibilidade futura de coexistência com NestJS? deve existir um sistema mínimo de AI com FastAPI e um microserviço central em NestJS, que deve ser o responsável pelas lógicas de negócio e comunicação com o banco de dados. O FastAPI deve ser utilizado exclusivamente para orquestração de agentes e processamento de vídeo, atuando como um sistema de workers dedicado a essas tarefas específicas. Essa divisão clara de responsabilidades entre os dois frameworks permitirá uma melhor organização do código, facilitando a manutenção e evolução do sistema ao longo do tempo.

2. Qual componente será considerado o orquestrador principal do pipeline? O microserviço central em NestJS deve ser o orquestrador principal do pipeline, coordenando as diferentes etapas do processamento de vídeo, desde o upload até a geração do relatório final. Ele será responsável por gerenciar o fluxo de dados entre os componentes, garantindo que cada etapa seja executada na ordem correta e que os resultados sejam armazenados adequadamente no banco de dados. O FastAPI atuará como um sistema de workers dedicado a tarefas específicas, mas a lógica de orquestração geral ficará a cargo do NestJS. Toda a arquitetura deve ser simplificada para ser o mais ágil possível, evitando complexidades desnecessárias e garantindo que o sistema seja fácil de entender e evoluir, mas também perfomatico. por exemplo, depois do upload do vídeo no microservice nestjs, o FASTAPI atua com links diretos para o processamento do vídeo, e o NestJS apenas monitora o status do processamento e recebe os resultados para armazenar no banco de dados e seguir com as próximas etapas do pipeline.
3. O processamento de vídeo será síncrono dentro do backend ou sempre executado por workers? Sempre workers e async.
4. Existe requisito para GPU ou todo o MVP deve funcionar em CPU? todo o sistema deve funcionar em CPU, podendo ser otimizado por GPU metal ou CUDA.
5. Qual a configuração mínima suportada da máquina local do desenvolvedor? Não especificado.
6. Qual a configuração mínima suportada da VPS? Não especificado.
7. O sistema deve continuar operacional caso o Ollama esteja indisponível? Em primeiro momento, não, mas anotar como tech debt
8. Qual SLA aceitável para geração de relatório? SLA de 10 minutos para geração de relatório.
9. Quais componentes podem falhar sem derrubar o sistema inteiro? Componentes não críticos como análise de áudio ou transcrição podem falhar sem impactar a disponibilidade do sistema.
10. Qual componente é considerado crítico para disponibilidade? O microserviço central em NestJS é considerado crítico para a disponibilidade do sistema, pois coordena todas as etapas do pipeline.

---

# Bloco 2 — Pipeline de Processamento de Vídeo

## Organização do Pipeline

11. O pipeline será executado em uma única etapa ou dividido em estágios independentes? Divida em estágios para monitoramento e resiliência, mas mantenha a simplicidade. Cada estágio deve ser responsável por uma tarefa específica, como extração de áudio, transcrição, análise facial, construção da timeline e análise pelo LLM. Essa abordagem modular permitirá uma melhor organização do código e facilitará a identificação de gargalos ou falhas em etapas específicas do pipeline, sem comprometer a simplicidade geral do sistema.

Exemplo:

- extract-audio
- transcribe
- face-analysis
- timeline-builder
- llm-analysis

12. Cada estágio deve persistir resultados intermediários? Sim.
13. O vídeo original será mantido após processamento? Não, a menos que seja necessário para reprocessamento.
14. O áudio extraído será armazenado ou descartado? Armazenado temporariamente para análise, mas descartado após a geração do relatório final para economizar espaço.
15. Qual formato canônico de vídeo será adotado internamente? MP4 com codec H.264, para garantir compatibilidade e eficiência no processamento, além
16. Haverá transcodificação automática? Sim, para garantir que todos os vídeos estejam no formato canônico, mas deve ser otimizada para evitar consumo excessivo de recursos. A transcodificação deve ser realizada apenas quando necessário, ou seja, quando o vídeo enviado não estiver no formato MP4 com codec H.264. O sistema deve ser capaz de detectar o formato do vídeo e decidir se a transcodificação é necessária, evitando processamento desnecessário e garantindo uma experiência mais rápida para o usuário.
17. Qual tamanho máximo de vídeo permitido? 200MB
18. Qual duração máxima de vídeo permitida? 30 minutos
19. Como impedir uploads que consumam memória excessiva? Débito para ser validado pós MVP
20. Como validar vídeos corrompidos? Débito para ser validado pós MVP

---

Bloco 3 — Integração Faster-Whisper + MediaPipe
21. Whisper e MediaPipe rodarão:
Múltiplos processos (via ProcessPoolExecutor do Python ou Worker em segundo plano).
Por quê? O Python possui o GIL (Global Interpreter Lock), que impede que múltiplas threads executem código Python simultaneamente em mais de um núcleo de CPU. Como o MediaPipe processa frames de vídeo intensamente e o Whisper faz processamento pesado de áudio, rodá-los no mesmo processo (mesmo com threads) causaria travamento total da API do FastAPI. Containers separados adicionariam complexidade de rede desnecessária para o MVP. Múltiplos processos isolam a carga perfeitamente no nível do Sistema Operacional.
22. Como evitar disputa por CPU?
Configurando a prioridade do processo (niceness) dos workers de processamento de vídeo para um nível mais baixo (ex: nice -n 10) em relação ao processo principal do FastAPI. Assim, a API HTTP continua respondendo prontamente aos usuários na web (< 2 segundos) enquanto a CPU processa os vídeos em segundo plano quando houver ciclos disponíveis.
23. Como evitar gargalos de memória?
Processando o vídeo via geradores de streaming (ex: lendo frame a frame com cv2.VideoCapture do OpenCV) em vez de carregar o vídeo inteiro na memória RAM. Após o MediaPipe processar o frame, ele é descartado imediatamente da memória.
24. Existe limite simultâneo de jobs?
Sim. Limite rígido de 1 job por vez (concurrency=1). Em uma VPS barata, processar duas reuniões simultaneamente causará estouro de memória (OOM Killer) ou congelamento da máquina. Os jobs subsequentes aguardam na fila.
25. Qual modelo Whisper será utilizado?
base (ou base.en / base multilingue).
Justificativa: O modelo tiny tem uma taxa de erro de transcrição (WER) muito alta para português de negócios. O modelo small é bom, mas o base oferece o melhor balanço entre velocidade de processamento em CPU e precisão aceitável para o MVP.
26. O modelo Whisper será carregado uma única vez?
Sim. Ele será instanciado na inicialização do Worker de processamento em segundo plano como uma variável global/singleton. Carregar o modelo do disco a cada novo job adicionaria de 10 a 30 segundos de atraso desnecessário por reunião.
27. O MediaPipe será inicializado por job ou mantido residente?
Por job. O MediaPipe Face Mesh é leve para inicializar (menos de 1 segundo). Inicializá-lo por job garante que todos os recursos de memória de vídeo e contexto sejam liberados de forma limpa pelo coletor de lixo do Python ao final de cada reunião.
28. Como medir consumo de CPU por componente?
Utilizando a biblioteca padrão psutil do Python dentro do processo worker, capturando psutil.Process().cpu_percent() no início e no fim de cada etapa.
29. Como medir tempo por estágio?
Utilizando um decorador simples de medição de tempo (time.perf_counter()) ao redor das funções principais: extract_audio(), run_whisper(), run_mediapipe() e run_ollama().
30. Como identificar gargalos automaticamente?
Salvando os tempos medidos no item 29 em uma coluna de metadados (telemetry) na tabela do próprio banco de dados ao final de cada job. Se run_whisper demorar mais que 1.5× a duração real do vídeo, um log de aviso é gerado.
Bloco 4 — Sincronização Temporal dos Eventos
31. Qual será a fonte oficial do timestamp?
Timestamp do vídeo (em milissegundos).
Justificativa: O áudio extraído e os frames de vídeo compartilham exatamente a mesma linha do tempo nativa do arquivo de mídia. O timestamp do arquivo evita desvios cumulativos de sincronia.
32. Como converter frame para tempo absoluto?
Utilizando a fórmula matemática:
Timestamp (ms)=( 
FPS
Frame Index
​	
 )×1000
33. Qual FPS será considerado para cálculos?
O FPS nativo extraído dos metadados do vídeo via OpenCV (cv2.CAP_PROP_FPS). Não fixaremos um valor padrão (como 30), pois os usuários farão upload de vídeos gravados em diferentes plataformas com taxas variadas (ex: 15, 24, 25, 30 ou 60 FPS).
34. Como lidar com vídeos em FPS variáveis?
No MVP, utilizaremos o ffmpeg em um passo prévio de normalização para forçar o vídeo a uma taxa de quadros constante (CFR) de 24 FPS durante a extração do áudio. O comando técnico padrão será:
ffmpeg -i input.mp4 -r 24 -vcodec libx264 output.mp4.
35. Como garantir sincronização após transcodificação?
Ao aplicar o comando do item 34, o ffmpeg reconstrói a matriz de frames mantendo o alinhamento estrito com a faixa de áudio original. Toda a análise subsequente (MediaPipe e Whisper) lerá este arquivo normalizado.
36. O Whisper retornará segmentos ou palavras individuais?
Segmentos (Frases).
Justificativa: Palavras individuais geram um volume massivo de dados JSON desnecessários para o MVP, além de exigir o uso do parâmetro word_timestamps=True, que aumenta o consumo de CPU e o tempo de processamento do Whisper.
37. Qual granularidade mínima desejada?
Bloco/Frase (Segmento padrão do Whisper). Geralmente blocos de 2 a 7 segundos de fala.
38. Como associar sinais faciais a trechos da transcrição?
O algoritmo fará um cruzamento por intervalo de tempo. Se um segmento do Whisper ocorreu de 00:10.000 a 00:15.000, o sistema buscará todos os sinais faciais gerados pelo MediaPipe cujos timestamps estejam contidos nesse intervalo e os agrupará.
39. Como representar múltiplos sinais simultâneos?
Através de uma lista de sinais dentro do mesmo timestamp ou bloco de tempo na estrutura do JSON.
40. Qual será o schema definitivo da timeline consolidada?
JSON
[
  {
    "start_time": "00:05:12",
    "end_time": "00:05:18",
    "speaker": "Cliente",
    "text": "O preço está um pouco acima do nosso orçamento para este trimestre.",
    "signals": [
      {"type": "queda_engajamento", "confidence": 0.82},
      {"type": "afastamento_da_tela", "confidence": 0.70}
    ]
  }
]
Bloco 5 — Schema de Sinais Comportamentais
41. Quais sinais serão suportados no MVP?
Para manter o custo computacional baixo e evitar falsos positivos de expressões complexas, o MVP focará em 3 sinais estruturais fáceis de extrair via coordenadas de pontos (landmarks):
olhar_desviado: O cliente não está olhando na direção da câmera/tela por mais de 3 segundos consecutivos.
aceno_cabeca_positivo / negativo: Movimentos verticais ou horizontais contínuos do rosto.
afastamento_da_tela: Redução súbita do tamanho relativo da face detectada no frame (indica recuo físico na cadeira).
42. Quem define um evento de interesse?
Uma heurística programada em Python no backend. Exemplo: Se o cliente faz um aceno positivo com a cabeça enquanto o vendedor está apresentando um slide.
43. Quem define um evento de resistência?
Uma heurística baseada no acúmulo de sinais de olhar_desviado ou afastamento_da_tela coincidindo com momentos em que palavras-chave como "preço", "contrato", "prazo" ou "concorrente" aparecem na transcrição do áudio.
44. Os sinais serão heurísticos ou estatísticos?
Heurísticos. Regras baseadas em limites de distância geométrica simples (limiares de pixels entre pontos faciais do MediaPipe). São extremamente rápidas de executar, usam zero IA pesada e não demandam treinamento de modelos.
45. Como versionar mudanças nos sinais?
Adicionando um campo numérico simples "schema_version": 1 no topo do JSON exportado pelo pipeline de visão computacional.
46. Como rastrear a origem de cada sinal?
Cada sinal conterá um metadado indicando a regra de origem. Exemplo: {"source": "mediapipe_mesh_v1_eye_tracking"}.
47. Como armazenar confiança dos sinais?
Utilizando o score de confiança nativo que o próprio MediaPipe retorna para a detecção da face no frame atual (um valor de 0.0 a 1.0).
48. Como armazenar múltiplas evidências?
Se múltiplos frames dentro do mesmo segundo dispararem a heurística de olhar_desviado, o sistema consolida o evento salvando a contagem de frames afetados como evidência (ex: "evidence": {"frames_triggered": 18, "total_frames": 24}).
49. Qual formato oficial dos eventos?
JSON
{
  "timestamp_ms": 312000,
  "signal_type": "olhar_desviado",
  "confidence": 0.91,
  "meta": {"duration_seconds": 3.5}
}
50. Qual formato oficial da timeline?
Uma lista ordenada cronologicamente contendo os objetos de eventos do item 49 intercalados ou embutidos nas frases do item 40.
Bloco 6 — Persistência e Banco de Dados
51. SQLite e PostgreSQL compartilharão exatamente o mesmo schema?
Sim. Utilizando tipos de dados padronizados compatíveis com ambos (como Text mapeando para strings longas e salvando dados de JSON complexos como Strings de texto puro em vez de usar o tipo específico JSONB, garantindo portabilidade imediata do SQLite local para o PostgreSQL em produção).
52. Qual ORM será utilizado?
SQLAlchemy (em conjunto com o SQLModel ou as definições nativas do FastAPI). Ele abstrai as diferenças sintáticas entre SQLite e PostgreSQL com perfeição.
53. O banco armazenará:
Vídeos: Não (armazenará apenas o caminho do arquivo de texto apontando para o disco).
Transcrições: Sim (em formato texto ou JSON embutido).
Sinais: Sim (JSON serializado em string).
Prompts: Não (ficam salvos diretamente no código do repositório para facilitar o versionamento via Git).
Respostas do LLM: Sim (armazenará o relatório final em Markdown gerado pelo Ollama).
54. O vídeo ficará no banco ou filesystem?
Strictly Filesystem. Gravar arquivos binários de vídeo no banco de dados degrada gravemente a performance das queries. Os vídeos salvos via upload irão para uma pasta dedicada local (ex: /var/data/uploads/), e o banco de dados guardará apenas a string com o caminho absoluto do arquivo.
55. Como será feita retenção?
Uma tarefa programada simples no backend Python (cron job interno via FastAPI-utils ou script separado) rodando uma vez por dia que apaga do disco arquivos de vídeo cujo status do job associado seja superior a 7 dias.
56. Qual política de exclusão?
Quando um usuário clica em "Excluir Reunião", o sistema executa um Hard Delete: apaga o registro do banco de dados e remove imediatamente o arquivo de vídeo correspondente do Filesystem usando os.remove().
57. Como versionar relatórios?
Para o MVP, não haverá histórico de edições do mesmo relatório. A tabela meetings terá apenas uma coluna chamada report_markdown. Se o usuário solicitar reprocessamento, o texto antigo é sobrescrito.
58. Como rastrear reprocessamentos?
A tabela de jobs conterá uma relação de 1-para-muitos com a tabela de meetings. Cada tentativa de processamento gera uma nova linha na tabela de jobs com as colunas created_at, status e error_log.
59. Como auditar falhas?
Através de um bloco estruturado try/except global no Worker. Qualquer exceção captura o traceback completo do erro via biblioteca traceback.format_exc() e o grava na coluna error_log do job com status failed.
60. Como reconstruir uma análise completa?
Lendo o arquivo JSON consolidado (transcrição + sinais) que opcionalmente pode ficar salvo em cache no disco ao lado do ID da reunião. Se o relatório falhar ou o prompt mudar, basta ler este arquivo JSON do disco e reenviar para o Ollama, sem gastar CPU reprocessando o vídeo e o áudio do zero.
Bloco 7 — Lean Queue Architecture
61. Banco ou Redis? Por quê?
Banco de Dados (SQLite em desenvolvimento, PostgreSQL em produção).
Justificativa: Elimina a necessidade de instalar, configurar e monitorar um serviço extra (Redis) no ambiente do MVP. Uma tabela estruturada de controle de jobs é extremamente confiável para cenários de baixa concorrência e o setup inicial cai para zero.
62. Existe necessidade real de Redis no MVP?
Não. O processamento é de baixa volumetria (limite de 500 reuniões por mês significa uma média de menos de 20 reuniões por dia). O banco de dados lida com essa carga de escrita de forma trivial.
63. Qual schema da tabela jobs?
SQL
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_log TEXT
);
64. Estados possíveis: pending, processing, completed, failed são suficientes?
Sim. São perfeitamente suficientes para cobrir o ciclo de vida completo de uma tarefa assíncrona de MVP.
65. Existe estado retry?
Não no nível do status do banco. O controle de tentativas é feito em memória pelo Worker. Se falhar após 3 tentativas internas no código, o status vai direto para failed.
66. Existe estado cancelled?
Não no MVP. Se o usuário deletar a reunião enquanto processa, o worker intercepta no próximo passo do loop e marca como failed.
67. Existe timeout por job?
Sim. Timeout rígido de 30 minutos. Se uma reunião demorar mais do que isso para rodar localmente no pipeline de CPU, o worker encerra o subprocesso preventivamente para evitar o travamento infinito da fila.
68. Como detectar worker travado?
O servidor web do FastAPI checa periodicamente se existem jobs com status processing cuja coluna updated_at não foi modificada nos últimos 30 minutos. Se encontrar, assume-se que o processo travou ou morreu por falta de memória e o job é marcado automaticamente como failed.
69. Como evitar processamento duplicado?
Utilizando uma transação atômica de banco de dados com lock de linha (ex: SELECT FOR UPDATE no PostgreSQL ou isolamento simples de escrita no SQLite) ao buscar o próximo item da fila, alterando imediatamente seu status de pending para processing na mesma operação.
70. Como implementar lock distribuído futuramente?
Migrando a fila do banco de dados para a biblioteca padrão Celery com broker em Redis quando o SaaS atingir a marca de mais de 30 usuários simultâneos ativos pagantes.
Bloco 8 — Recuperação de Falhas
71. Se o Ollama cair durante análise, o que acontece?
O pipeline captura uma exceção de conexão HTTP (httpx.ConnectError ou similar). O job tenta novamente essa etapa específica até o limite configurado de retries. Se persistir, o job muda para o status failed e exibe um aviso amigável na interface do usuário para "Tentar Novamente".
72. Reprocessar do zero ou continuar?
Continuar a partir do estágio de geração do relatório. Como o áudio e o vídeo já foram extraídos e processados com sucesso nas etapas anteriores, os dados consolidados em formato JSON estarão salvos no disco. O sistema não gastará CPU processando o vídeo novamente.
73. Existe checkpointing?
Sim, baseado em arquivos físicos no disco de trabalho.
74. Em quais etapas?
Ao final de cada uma destas 3 etapas críticas:
audio.wav gerado com sucesso.
transcript.json gerado com sucesso pelo Whisper.
signals.json gerado com sucesso pelo MediaPipe.
75. Qual estágio tem maior custo?
O processamento de vídeo pelo MediaPipe, seguido de perto pela transcrição do Whisper. A etapa mais barata e rápida é o envio do texto consolidado para o Ollama.
76. O sistema deve salvar artefatos intermediários?
Sim. Conforme respondido na questão 74, os arquivos JSON intermediários são mantidos no diretório do job até que o relatório final do Ollama seja concluído com sucesso e persistido no banco de dados.
77. Quantas tentativas automáticas?
3 tentativas com recuo exponencial simples (aguardando 2, 5 e 10 segundos entre elas) antes de desistir definitivamente e marcar o job como falhado.
78. Como distinguir erro temporário de erro definitivo?
Erros temporários: Falhas de rede HTTP ao falar com a API local do Ollama ou timeouts leves de leitura de arquivo.
Erros definitivos: Arquivo de vídeo corrompido que o OpenCV não consegue abrir, falta de codecs adequados ou falta de espaço físico em disco (armazenamento cheio).
79. Como evitar loops infinitos?
Garantindo que o contador de retries seja armazenado rigidamente em uma variável local de controle dentro do loop de execução do Worker. Ele nunca incrementa o status de volta para pending de forma automática sem intervenção humana (sem botões de retry automático em loop infinito).
80. Como gerar evidências para debugging?
Ao capturar qualquer exceção, o sistema grava o traceback do erro e salva uma cópia do estado atual das variáveis de ambiente e o nome do arquivo que gerou o erro diretamente no campo error_log do banco de dados.
Bloco 9 — Estratégia de Contexto para Ollama
81. Qual modelo será oficial do MVP?
llama3:8b (ou mistral:7b / qwen2.5:7b dependendo da preferência por suporte a português). O llama3:8b apresenta excelente raciocínio analítico para relatórios comerciais estruturados.
82. Qual contexto máximo suportado?
Por padrão, a janela nativa desses modelos em ambiente local via Ollama é configurada em 8.192 tokens (8k).
83. Qual tamanho médio esperado da transcrição?
Uma reunião comercial focada de 30 minutos em ritmo normal de fala gera em média cerca de 3.500 a 4.500 palavras, o que se traduz em aproximadamente 4.500 a 5.500 tokens de texto.
84. Qual tamanho médio esperado do JSON?
O JSON bruto de coordenadas seria gigantesco. Porém, utilizando a nossa estratégia de agrupar por segmentos de frases (descrita nas questões 38 e 40), o JSON de telemetria consolidado e limpo ocupará menos de 1.000 tokens.
85. Qual tamanho máximo aceitável de prompt?
O prompt estruturado do sistema consumirá cerca de 1.000 tokens. Portanto, o total somado (Prompt + Transcrição + Sinais JSON) ficará em torno de 6.500 a 7.500 tokens, encaixando-se perfeitamente dentro do limite seguro da janela de 8k sem estourar.
86. Como medir tokens antes do envio?
Utilizando uma biblioteca utilitária ultraleve de contagem de tokens em Python, como o tiktoken (usando a codificação do GPT-4 como aproximação matemática muito próxima) ou o tokenizador nativo do HuggingFace para o Llama3.
87. Como evitar estouro de contexto?
Se o cálculo feito no item 86 ultrapassar a marca de 7.500 tokens (indicando uma reunião muito longa, ex: 1 hora de conversa), o backend interceptará o fluxo e acionará o algoritmo de compressão de contexto antes de disparar a requisição ao Ollama.
88. Qual estratégia será adotada?
Summarization (Sumarização hierárquica por blocos).
Justificativa: Dividiremos a transcrição em duas metades (Metade A e Metade B), pediremos para o Ollama gerar um resumo condensado dos pontos chaves e falas de cada metade separadamente, e depois uniremos esses resumos compactados com o JSON de sinais para gerar a análise estratégica final de vendas.
89. Qual informação nunca pode ser removida?
Os trechos da transcrição de áudio que contêm números monetários (valores de propostas, descontos sugeridos), prazos específicos de fechamento e as objeções verbais explícitas do comprador.
90. Como priorizar sinais importantes?
O algoritmo de filtragem em Python descartará sinais redundantes ou de baixa confiança (ex: se o cliente desviou o olhar por apenas 1 segundo enquanto o vendedor não estava falando nada importante, esse sinal é limpo do JSON antes do envio ao Ollama).
Bloco 10 — Engenharia de Prompts
91. O Ollama deve responder em Markdown ou JSON?
Markdown.
Justificativa: O relatório pós-reunião gerado para o vendedor é um documento textual de leitura humana direta. Forçar o Ollama a estruturar a análise em blocos complexos de JSON frequentemente causa quebras de caracteres, aspas mal formatadas ou respostas incompletas devido à rigidez sintática. O formato Markdown nativo é muito mais robusto e pode ser renderizado diretamente na tela do frontend.
92. O frontend consumirá JSON puro?
Não para a seção do relatório em si. O frontend receberá uma string contendo o texto formatado em Markdown padrão e usará um componente de visualização leve (ex: react-markdown no Next.js) para exibi-lo esteticamente para o usuário.
93. Qual schema oficial de saída?
O Ollama será instruído via prompt de sistema a seguir rigidamente títulos padronizados em Markdown:
Markdown
# Relatório de Análise Comercial

## 1. Resumo Executivo
[Texto aqui]

## 2. Objeções Identificadas
* **[Objeção Comercial]**: [Evidência verbal + sinal temporal]

## 3. Momentos de Alto Engajamento
1. [Timestamp] - [Fato ocorrido]

## 4. Próximos Passos Recomendados
* [Ação sugerida]
94. Quais campos são obrigatórios?
Os blocos descritos no item 93: Resumo Executivo, Objeções Identificadas e Próximos Passos Recomendados.
95. Como validar saída inválida?
O backend Python checará se as strings de cabeçalho obrigatórias (ex: ## 2. Objeções Identificadas) existem na string de resposta gerada pelo Ollama utilizando expressões regulares simples (re.search).
96. Como corrigir JSON malformado?
Como adotamos o formato Markdown (item 91), o problema de JSON quebrado foi totalmente mitigado da camada de geração de relatórios. Se o prompt for alterado no futuro para retornar JSON, usaremos a biblioteca Python json-repair para sanitizar as aspas automaticamente antes do parseamento pelo Pydantic.
97. Haverá retries automáticos?
Se a validação do item 95 falhar (ex: resposta incompleta ou cortada por falta de tokens), o sistema descarta a resposta e realiza automaticamente uma única nova tentativa com uma temperatura ligeiramente mais baixa (temperature=0.2) para forçar o modelo a ser mais determinista.
98. Haverá validação via Pydantic?
Sim. Utilizaremos uma classe Pydantic para validar o empacotamento dos metadados da reunião que vão para o banco, mas a resposta textual do relatório bruto em Markdown será armazenada como uma string limpa validada pelas regras Regex (item 95).
99. Qual percentual de erro aceitável?
Definimos um threshold de Menos de 5% de falhas estruturais nas respostas em Markdown durante a fase de testes do Harness.
100. Como medir qualidade dos relatórios?
No MVP, a qualidade será avaliada indiretamente através da telemetria da interface do usuário: medindo se o vendedor passou mais de 45 segundos com a tela do relatório aberta (indicativo claro de leitura e engajamento) e através de um botão simples de feedback de polegar para cima / polegar para baixo (✓/×) posicionado no rodapé do relatório.
Bloco 11 — Contratos e APIs
101. Qual será o contrato oficial entre pipeline e frontend?
O contrato padrão será um modelo de comunicação assíncrona HTTP REST tradicional:
O frontend envia o arquivo via POST /api/v1/meetings/upload. Recebe de volta um ID de reunião e o status pending.
O frontend realiza um mecanismo de consulta periódica leve (polling) a cada 5 segundos disparando requisições GET /api/v1/meetings/{id}/status.
Quando o status retornar completed, o frontend faz um disparo final para GET /api/v1/meetings/{id}/report para buscar o texto em Markdown e a timeline.
102. Quais endpoints são necessários?
POST /api/v1/auth/login (Acesso básico do vendedor).
POST /api/v1/meetings/upload (Upload do arquivo de vídeo).
GET /api/v1/meetings/ (Listagem de reuniões do usuário).
GET /api/v1/meetings/{id}/status (Status do processamento da fila).
GET /api/v1/meetings/{id}/report (Visualização dos resultados consolidados).
DELETE /api/v1/meetings/{id} (Exclusão física dos dados).
103. Como versionar APIs?
Utilizando prefixação explícita de rota diretamente na URL base do FastAPI: /api/v1/....
104. Como validar compatibilidade?
Os esquemas de dados de entrada e saída de todos os endpoints listados no item 102 serão estritamente amarrados a classes de validação do Pydantic. O FastAPI rejeitará requisições fora do padrão automaticamente com o erro 422 Unprocessable Entity.
105. Como agentes de IA descobrirão contratos?
Através do arquivo JSON de especificação gerado automaticamente pelo FastAPI na rota padrão /openapi.json. Seus agentes de desenvolvimento lerão esse arquivo de metadados para entender os exatos tipos de parâmetros aceitos pelo backend.
106. OpenAPI será fonte única da verdade?
Sim. A documentação viva gerada nativamente pelo FastAPI no endpoint /docs (Swagger UI) será o ponto central de referência absoluta para o desenvolvimento das integrações.
107. Quais schemas precisam de versionamento?
O schema do payload da rota de retorno do relatório (GET /api/v1/meetings/{id}/report), garantindo que alterações na estrutura interna do JSON de sinais faciais não quebrem as versões antigas da interface visual do frontend.
108. Como tratar breaking changes?
Se houver uma modificação drástica de estrutura que quebre a compatibilidade da interface, a nova rota será criada sob o prefixo /api/v2/. A rota /api/v1/ será mantida intocada e funcional durante todo o ciclo de vida do MVP.
109. Como documentar mudanças?
Utilizando as Docstrings nativas do Python diretamente nas funções de rota do FastAPI. O framework lê esses blocos de documentação e atualiza a interface do Swagger automaticamente em tempo real.
110. Como garantir retrocompatibilidade?
Garantindo que qualquer novo campo adicionado aos schemas de resposta do Pydantic possua obrigatoriamente um valor padrão atribuído (ex: field: Optional[str] = None). Isso evita que o frontend Next.js falhe ao processar objetos que venham sem a nova propriedade.
Bloco 12 — Harness Engineering
111. Qual será a definição oficial de "build aprovado"?
O código modificado por um agente de IA só será elegível para Merge na branch principal se cumprir cumulativamente 3 requisitos:
Passar em 100% dos testes unitários e de integração locais.
Não apresentar erros de checagem estática de tipos (verificado via comando mypy ou ruff).
Executar o pipeline de simulação ponta a ponta com o vídeo de teste padrão (Mock) em menos de 3 minutos, sem exceder o consumo máximo estipulado de memória.
112. O agente pode fazer merge sem passar no harness?
Não, nunca. O pipeline do Harness é um guardião automatizado bloqueante configurado diretamente nas regras do repositório de código.
113. Qual cobertura mínima exigida?
Mínimo de 70% de cobertura de código (Code Coverage) focado exclusivamente nas regras de negócio, utilitários e rotas principais do FastAPI. Não exigiremos 100% de cobertura no MVP para acelerar o desenvolvimento, evitando testes redundantes em arquivos de configuração simples.
114. Quais testes são obrigatórios?
Testes Unitários: Validação das funções isoladas de manipulação de timestamps e das regras lógicas de heurística comportamental do MediaPipe.
Testes de Integração: Simulação de chamadas HTTP reais disparadas contra as rotas da API usando a classe utilitária TestClient nativa do FastAPI, injetando um banco SQLite mockado em memória.
115. Qual tempo máximo aceitável do pipeline de testes?
Menos de 5 minutos. Como os modelos pesados de IA (Whisper e Ollama) serão totalmente substituídos por dublês de testes (Mocks/Fakes) rápidos durante os testes unitários da esteira de CI, o pipeline rodará em poucos segundos. O teste ponta a ponta com IA real será executado de forma isolada e agendada.
116. Como medir regressão?
O Harness guardará um arquivo JSON de referência contendo a saída esperada exata para o cenário de teste padrão. Se uma alteração de código modificar a estrutura ou o fluxo lógico esperado de uma rota sem alteração correspondente no teste, o Harness acusa a divergência e reprova o build.
117. Como validar performance?
O script de teste monitorará se a resposta do endpoint HTTP de listagem de reuniões e renderização do relatório executa em menos de 200 milissegundos sob simulação de concorrência simples.
118. Como validar consumo de memória?
O Harness executará o script de processamento embrulhado no utilitário de terminal mprof (da biblioteca memory_profiler do Python). Se o pico máximo de consumo de memória RAM do processo ultrapassar o limite rígido de 2.5 GB durante o processamento do vídeo de teste padrão, o build é rejeitado por risco de OOM (Out of Memory) em produção.
119. Como validar consumo de CPU?
Monitorando através do psutil se o processo web principal do FastAPI permanece livre e sem picos de 100% de uso sustentados enquanto o processo em segundo plano executa a extração do MediaPipe.
120. Como impedir que agentes introduzam dependências desnecessárias?
O Harness verificará o arquivo requirements.txt ou pyproject.toml. Se o agente de IA adicionar qualquer biblioteca externa sem autorização prévia na lista de permissões configurada, o pipeline dispara um erro sintático e bloqueia o commit.
Testes de Integração e Sandbox (Blocos 13, 14, 15)
Bloco 13 — Testes de Integração Obrigatórios
Para garantir o determinismo e guiar os agentes de IA, criaremos um Vídeo Padrão de Teste (Mock) com duração exata de 10 segundos em formato MP4 (24 FPS, resolução 640x480). O vídeo conterá um rosto humano claro executando movimentos simples e uma faixa de áudio contendo uma frase limpa falada em português: "Gostei do produto, mas precisamos discutir as condições de preço na próxima semana".
Os testes de integração obrigatórios do Harness executarão o pipeline completo contra esse arquivo físico e validarão de forma estrita se:
O pipeline de áudio extrai o arquivo .wav com sucesso.
A transcrição retornada pelo Whisper contém as palavras-chave "produto" e "preço".
O JSON gerado pelo MediaPipe registra pelo menos um evento com a propriedade signal_type.
O relatório final simulado contém texto não vazio estruturado sob títulos em Markdown.
Bloco 14 — Sandbox dos Agentes
Para que os agentes de IA trabalhem com total segurança sem interferir no sistema hospedeiro, cada instância de agente executará isolada dentro de um container Docker controlado. Esse container terá limites físicos rígidos definidos diretamente nas flags de execução do runtime do Docker Compose: limite de memória fixado em no máximo 4 GB (mem_limit: 4g) e limite de uso de processador restrito a no máximo 2 núcleos de CPU (cpus: 2).
O acesso externo à internet de dentro da Sandbox será bloqueado ou monitorado, forçando o agente a instalar bibliotecas exclusivamente a partir de um cache local pré-aprovado de pacotes Python. Para economizar recursos computacionais durantes os ciclos repetitivos de refatoração, o Harness interceptará as requisições direcionadas ao Ollama e ao Whisper, respondendo imediatamente com dados estáticos salvos em cache (Mocking), acionando os modelos de IA reais instalados na máquina física apenas no estágio final de aprovação do código.
Bloco 15 — Observabilidade
A debugabilidade do sistema será baseada na especificação de Logs Estruturados em formato JSON emitidos diretamente para a saída padrão (stdout) através da biblioteca nativa logging do Python. Cada linha de log emitida conterá obrigatoriamente a estrutura de chaves: {"timestamp": "...", "level": "...", "job_id": "...", "component": "...", "message": "..."}.
JSON
{"timestamp": "2026-05-31T17:30:00Z", "level": "INFO", "job_id": "412", "component": "pipeline.mediapipe", "message": "Processing frame 240/1200. Face detected."}
Através do mapeamento estrito do job_id injetado no contexto de execução de cada tarefa, o engenheiro humano ou os próprios agentes de monitoramento conseguirão filtrar e rastrear toda a jornada de um arquivo — desde o upload inicial, passando pela geração de logs do MediaPipe e Whisper, até a string final devolvida pelo Ollama —, isolando falhas de processamento em questão de segundos.