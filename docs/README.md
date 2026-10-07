# Tradutor Automático de Legendas MKV/ASS/SRT

Uma ferramenta automatizada em Python com arquitetura MVC e interface gráfica moderna para extração, tradução e multiplexação de legendas em arquivos de vídeo `.mkv`, com suporte a arquivos avulsos `.ass` e `.srt`. O script utiliza a API do Google Translate de forma assíncrona para garantir alta performance e possui mecanismos robustos de tolerância a falhas para evitar bloqueios de rede.

## 🚀 Funcionalidades

* **Arquitetura Escalável (MVC):** Código organizado sob o padrão MVC na pasta `tradutor/`, garantindo alta coesão, modularidade e desacoplamento entre Interface (View), Lógica de Controle (Controller) e Processamento (Model).
* **Detecção Inteligente de Idiomas:** Ao selecionar arquivos `.mkv`, o sistema varre de forma assíncrona as faixas de legenda disponíveis e preenche automaticamente um menu suspenso (Dropdown) com os idiomas originais presentes no vídeo.
* **Mitigação de "Língua Pivô":** Converte automaticamente códigos ISO-639-2 do MKV (ex: `fra`) para ISO-639-1 (ex: `fr`) do Google Translate (cerca de 35 idiomas mapeados). Isso informa forçosamente ao Google o idioma de origem, evitando o "vazamento" de palavras em inglês ao traduzir de idiomas estrangeiros complexos.
* **Idioma Real da Faixa:** O idioma enviado ao Google é o da faixa realmente extraída de cada vídeo, mesmo com a opção `auto` ou quando o idioma preferido não existe no arquivo (nesse caso, o log avisa qual faixa foi usada). Idiomas desconhecidos usam a autodetecção do Google, com aviso. Se a faixa já estiver no idioma de destino, o vídeo é pulado.
* **Automação MKV de Ponta a Ponta:** Extrai silenciosamente a trilha de legenda do vídeo original, traduz preservando todas as formatações e embute (muxing) o arquivo traduzido em um novo vídeo `<nome>_<DESTINO>.mkv` (ex: `_PT.mkv`), com o idioma e o nome da trilha do destino escolhido, sem perda de qualidade.
* **Preservação Opcional de Legendas:** Checkbox na interface permite manter o arquivo `.ass` ou `.srt` final após a extração, em vez de excluí-lo como temporário.
* **Alta Performance (Async/Concorrência):** Utiliza `asyncio`, `Semaphores` e `ThreadPoolExecutor` para paralelizar as chamadas à API, mantendo a responsividade da interface gráfica.
* **Tolerância a Falhas e Anti-Ban:**
    * *Exponential Backoff:* Tenta reconectar automaticamente e adormece a thread em caso de falha de conexão com a API.
    * *Tratamento de Erros de IP:* Detecta proativamente bloqueios de Captcha do Google, interrompendo graciosamente lotes falhos sem travar a interface.
    * *Fallback Sequencial:* Reprocessa o lote linha a linha caso as traduções em bloco fiquem dessincronizadas.

## 🛠️ Como Usar (Instalação Fácil)

A ferramenta é "Plug and Play" no Windows.

1. Baixe o repositório para o seu computador.
2. Certifique-se de ter o **Python 3.8+** instalado no sistema.
3. Dê um duplo-clique no arquivo **`iniciar.bat`**.

> O `iniciar.bat` criará automaticamente um ambiente virtual (`venv/`), instalará as dependências (`requirements.txt`) e abrirá a interface.

### Pré-requisitos (MKVToolNix)
Necessário apenas para vídeos embutidos (.mkv).
* *Opção 1 (Sistema):* Instale o [MKVToolNix](https://mkvtoolnix.download/) (`C:\Program Files\MKVToolNix`).
* *Opção 2 (Portátil):* Coloque os executáveis (`mkvmerge.exe` e `mkvextract.exe`) dentro da pasta `mkvtoolnix/` na raiz do projeto.

## 🧪 Ambiente de Testes Massivos

O projeto conta com uma suíte de testes isolada (`tests/`) focada em testes de estresse de tradução.

* **Como testar:** Execute o arquivo `testar.bat` na raiz.
* **Como funciona:** O script carrega um Mock da Interface Gráfica e consome diretamente a lógica do `TranslationOrchestrator` de forma *Headless* (sem tela).
* **Massive Testing:** Ele lê dinamicamente todas as legendas brutas contidas em `tests/legendas/`, converte a origem baseado no nome do arquivo (ex: `Japones.srt`), aciona o limite máximo de concorrência e despeja um json gigante (`relatorio_teste_massivo.json`) contendo a **Estatística Percentual de Sucesso (%)** de cada linha modificada comparada à original.
