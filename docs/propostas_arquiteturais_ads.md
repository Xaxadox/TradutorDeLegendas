# Propostas Arquiteturais: Tópicos Especiais (ADS)

Este documento foi criado para preservar o escopo e o brainstorming de arquitetura para a expansão do projeto **Tradutor Automático de Legendas**. O foco é elevar o grau de maturidade do software injetando **Segurança da Informação** e **Inteligência Artificial**, fornecendo material robusto para avaliação em bancas de graduação (Análise e Desenvolvimento de Sistemas).

---

## Caminho 1: O Híbrido (Google Motor + IA de Transcrição Ocasional)

### 📌 Visão Geral
Manter a espinha dorsal do projeto atual (que usa o motor gratuito do Google Translate otimizado e blindado contra bans). A Inteligência Artificial será acionada como um sistema de "Socorro" (Fallback) exclusivamente quando o usuário inserir um vídeo RAW (sem nenhuma legenda embutida).

### 🛠️ Tecnologias e Implementação
1. **Módulo de Segurança (Sanitização de Arquivos):**
   * **Objetivo:** Impedir que arquivos `.mkv` ou `.srt` forjados executem scripts maliciosos (via *buffer overflow* nos players ou extratores).
   * **Stack Técnica:** Usar a biblioteca `pymediainfo` ou `python-magic` para verificar os *magic bytes* e validar a assinatura real do arquivo antes que o nosso extrator (`pysubs2` ou `mkvmerge`) ouse abrir a faixa.
2. **Módulo de Inteligência Artificial (STT - Speech-to-Text):**
   * **Objetivo:** Gerar um arquivo `.srt` a partir das ondas sonoras do vídeo.
   * **Stack Técnica:** Integração com a **OpenAI Whisper API** (via web) ou biblioteca offline. O programa extrai a trilha de áudio (formato MP3/WAV) invisivelmente, envia para a IA, que devolve um `.srt` com as falas e os milissegundos perfeitos de cada frase.
   * **Integração MVC:** O Controller aciona a IA, salva o `.srt` na pasta temporária e o injeta no `TranslatorService` que já temos pronto para traduzir para PT-BR.

### 🚀 Expansão de Escopo (Trabalho Futuro para a Banca)
* **Reconciliação Auditiva (IA vs Legenda):** Se um arquivo já possui legenda embutida, o sistema pode rodar a IA ouvindo o áudio em background e cruzar as duas informações. Exemplo de TCC: Usar algoritmos matemáticos como o *Cosine Similarity* para validar se a legenda existente está faltando falas e usar a IA apenas para "preencher os buracos" da legenda existente.

---

## Caminho 2: IA "On-Edge" (100% Local) + Segurança Ativa de Extinção Web

### 📌 Visão Geral
Transformar o software num bastião tecnológico **Open-Source**. Essa é a abordagem favorita da academia, pois não exige que o software converse com empresas terceiras (Google, OpenAI) via internet. O modelo de Inteligência Artificial roda inteiramente na GPU/CPU da própria máquina (*Edge Computing*).

### 🛠️ Tecnologias e Implementação
1. **Módulo de Inteligência Artificial (Inferência Local):**
   * **Tecnologia:** Instalação da biblioteca `faster-whisper`.
   * **Implementação:** O usuário baixaria um modelo de Machine Learning pequeno (o modelo `small` pesa cerca de 240MB). Diferente do Caminho 1, o código chamará o modelo para carregar os "pesos" na memória RAM e processará o áudio localmente.
   * **Tradução Local Opcional:** Caso queira abandonar o Google Translate de vez, o `TranslatorService` pode usar bibliotecas da Hugging Face (como os modelos de NLP `Helsinki-NLP/opus-mt`) para traduzir textos off-line, gerando uma arquitetura 100% privada.
2. **Módulo de Segurança e Otimização Avançada:**
   * **Segurança (*Sandboxing*):** Como estaremos lidando com manipulação binária massiva localmente (extraindo áudios para alimentar a IA), o sistema de segurança incluirá o uso restrito de processos (Sandboxing). O comando do `ffmpeg` roda em uma bolha do SO (isolamento de subprocessos com flag `creationflags=CREATE_NO_WINDOW`) evitando injeções de *shell*.
   * **Segurança de Threading:** Essa escolha desafiará fortemente o conhecimento de paralelismo. Modelos locais pesam na execução. O aluno deve demonstrar como aplicou `Multiprocessing` no Python para que a IA rode num núcleo separado da CPU, impedindo que a Interface Gráfica (GUI) "congele" durante as horas de transcrição.

### 🎯 Diferenciais para Argumentação em Banca
* **Privacidade de Dados (LGPD):** O Caminho 2 garante que nenhum byte do áudio/texto saia do computador do usuário. Uma resposta corporativa muito procurada no mercado moderno.
* **Escalabilidade "Zero-Cost":** Elimina qualquer barreira financeira, chaves de API pagas ou limites diários do Google. Funciona no deserto, desde que o PC tenha energia.
