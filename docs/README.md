# Tradutor Automático de Legendas MKV/ASS/SRT

Uma ferramenta automatizada em Python com interface gráfica moderna para extração, tradução e multiplexação de legendas em arquivos de vídeo `.mkv`, com suporte a arquivos avulsos `.ass` e `.srt`. O script utiliza a API do Google Translate de forma assíncrona para garantir alta performance e possui mecanismos robustos de tolerância a falhas para evitar bloqueios de rede.

## 🚀 Funcionalidades

* **Interface Gráfica Moderna:** Desenvolvida com `customtkinter`, oferecendo tema escuro nativo, acompanhamento visual de progresso e log de operações em tempo real.
* **Automação MKV de Ponta a Ponta:** Extrai silenciosamente a trilha de legenda (`.ass` ou `.srt`) do vídeo original, traduz preservando todas as formatações e embute (muxing) o arquivo traduzido em um novo contêiner de vídeo sem perda de qualidade.
* **Seletor de Idioma Preferido:** Ao processar vídeos com múltiplas faixas de legenda (ex: Inglês, Espanhol, Japonês), permite que você escolha qual idioma específico (ex: `eng`) deve ser extraído e traduzido.
* **Preservação Opcional de Legendas:** Checkbox na interface que permite manter o arquivo da legenda traduzida externa (em `.ass` ou `.srt`) junto ao vídeo final, em vez de excluí-lo como lixo temporário.
* **Parsing Robusto com Pysubs2:** A leitura das legendas é feita de forma segura utilizando a biblioteca oficial `pysubs2`, garantindo que tags de efeitos complexos (cores, posições na tela) de arquivos `.ass` não sejam corrompidas durante a tradução.
* **Processamento em Lote (Batch Processing):** Permite selecionar múltiplos vídeos ou arquivos simultaneamente, processando-os em uma fila contínua à prova de falhas.
* **Alta Performance (Async/Concorrência):** Utiliza `asyncio` e `ThreadPoolExecutor` para enviar lotes de texto em 5 threads simultâneas, reduzindo drasticamente o tempo de tradução.
* **Tolerância a Falhas e Anti-Ban:**
    * *Exponential Backoff:* Tenta reconectar automaticamente em caso de falha da API.
    * *Fallback Sequencial:* Reprocessa o lote linha a linha de forma segura caso o Google dessincronize o resultado.
* **Modo Portátil (Portable):** O script procura automaticamente pelas ferramentas do MKVToolNix (`mkvmerge.exe` e `mkvextract.exe`) na pasta local do projeto. Se encontradas, roda sem necessidade de instalação no sistema.

## 🛠️ Como Usar (Instalação Fácil)

A ferramenta foi preparada para ser "Plug and Play" no Windows.

1. Baixe os arquivos para o seu computador.
2. Certifique-se de ter o **Python 3.8+** instalado no seu sistema.
3. Dê um duplo-clique no arquivo **`iniciar.bat`**.

> O `iniciar.bat` cuidará de tudo automaticamente: ele vai criar um ambiente virtual isolado, baixar todas as dependências requeridas e abrir a interface gráfica para você. Nas próximas vezes, a abertura será quase instantânea!

### Pré-requisitos (MKVToolNix)
Necessário **apenas** se você for traduzir vídeos embutidos (.mkv). Não é necessário para traduzir arquivos soltos de legenda.
* *Opção 1 (Sistema):* Instale o [MKVToolNix](https://mkvtoolnix.download/) no caminho padrão (`C:\Program Files\MKVToolNix`).
* *Opção 2 (Portátil):* Coloque os executáveis dentro da pasta `mkvtoolnix` junto ao script.
