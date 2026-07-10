# Tradutor Automático de Legendas MKV/ASS

Uma ferramenta automatizada em Python para extração, tradução e multiplexação de legendas em arquivos de vídeo `.mkv`, com suporte a arquivos avulsos `.ass` e `.txt`. O script utiliza a API do Google Translate de forma assíncrona para garantir alta performance e possui mecanismos robustos de tolerância a falhas para evitar bloqueios de rede.

## 🚀 Funcionalidades

* **Automação MKV de Ponta a Ponta:** Extrai silenciosamente a trilha de legenda (`.ass` / SubStation Alpha) do vídeo original, traduz e embute (muxing) o arquivo traduzido em um novo contêiner de vídeo sem perda de qualidade.
* **Processamento em Lote (Batch Processing):** Permite selecionar múltiplos vídeos ou arquivos de legenda simultaneamente, processando-os em uma fila contínua à prova de falhas (um erro em um arquivo não interrompe os demais).
* **Alta Performance (Async/Concorrência):** Utiliza `asyncio` e `ThreadPoolExecutor` para enviar lotes de texto (até 40 linhas por vez) em 5 threads simultâneas, reduzindo drasticamente o tempo de tradução.
* **Tolerância a Falhas e Anti-Ban:**
    * *Exponential Backoff:* Tenta reconectar automaticamente em caso de falha temporária da API.
    * *Fallback Sequencial:* Se a API do Google dessincronizar o lote (aglutinar falas), o script detecta o erro e reprocessa o lote linha a linha de forma segura.
* **Detecção Automática de Idioma:** A tradução não está engessada no inglês. O parâmetro `src="auto"` identifica automaticamente o idioma de origem da legenda (Japonês, Inglês, Espanhol, etc.) e traduz para o Português do Brasil.
* **Modo Portátil (Portable):** O script procura automaticamente pelas ferramentas do MKVToolNix (`mkvmerge.exe` e `mkvextract.exe`) na pasta local do projeto. Se encontradas, roda sem necessidade de instalação no sistema do usuário.
* **Limpeza Inteligente:** Exclui automaticamente os arquivos `.ass` temporários gerados durante o processo caso a multiplexação do vídeo seja bem-sucedida.

## 🛠️ Pré-requisitos

* **Python 3.8+**
* **MKVToolNix:** Necessário para manipulação de contêineres de vídeo.
    * *Opção 1 (Sistema):* Instale o [MKVToolNix](https://mkvtoolnix.download/) no caminho padrão (`C:\Program Files\MKVToolNix`).
    * *Opção 2 (Portátil):* Use a pasta chamada `mkvtoolnix` na mesma pasta do script.

### Dependências Python
Instale as bibliotecas necessárias executando o comando abaixo. 
> **Atenção:** É estritamente necessário usar a versão `4.0.0-rc1` do `googletrans` para evitar erros de limite de requisição.

```bash
pip install googletrans==4.0.0-rc1 tqdm
