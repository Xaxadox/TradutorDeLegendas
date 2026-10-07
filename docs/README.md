# Tradutor Automatico de Legendas MKV/ASS/SRT

Uma ferramenta automatizada em Python com arquitetura MVC, Strategy Pattern e interface grafica moderna para extracao, traducao e multiplexacao de legendas em arquivos de video `.mkv`, com suporte a arquivos avulsos `.ass` e `.srt`. O script utiliza a API do Google Translate de forma assincrona para garantir alta performance e possui mecanismos robustos de tolerancia a falhas, cache local e protecao de rede.

## Funcionalidades

* **Arquitetura Escalavel (MVC e Strategy):** Codigo organizado sob o padrao MVC na pasta `tradutor/`. A logica de execucao utiliza o padrao Strategy (via `FabricaProcessadores`), o que permite extender o suporte a novos arquivos sem modificar o orquestrador principal (`OrquestradorTraducoes`).
* **Deteccao Inteligente de Idiomas:** Ao selecionar arquivos `.mkv`, o sistema varre de forma assincrona as faixas de legenda disponiveis e preenche automaticamente o menu suspenso com os idiomas originais presentes no video.
* **Mitigacao de "Lingua Pivo":** Converte automaticamente codigos ISO-639-2 do MKV para ISO-639-1 do Google Translate. Isso informa forcosamente ao Google o idioma de origem, evitando o "vazamento" de palavras em ingles ao traduzir de idiomas estrangeiros complexos.
* **Idioma Real da Faixa:** O idioma enviado ao Google e o da faixa realmente extraida de cada video, mesmo com a opcao `auto` ou quando o idioma preferido nao existe no arquivo.
* **Injecao de Dependencias (Motores de Traducao):** O sistema isola a dependencia do `googletrans` em uma classe especialista (`MotorTraducaoGoogle`) que respeita uma interface comum (`ITradutor`). Isso permite acoplar facilmente motores alternativos (ex: DeepL) no futuro.
* **Automacao MKV de Ponta a Ponta:** Extrai silenciosamente a trilha de legenda do video original, traduz preservando formatacoes e embute o arquivo traduzido em um novo video `<nome>_<DESTINO>.mkv`.
* **Alta Performance (Async/Concorrencia):** Utiliza `asyncio`, e `ThreadPoolExecutor` para paralelizar as chamadas a API.

## Tolerancia a Falhas e Resiliencia

* **Checkpointing e Caching Local (SQLite):** Cada frase traduzida com sucesso e salva em um banco de dados local (`cache_traducoes.db`) utilizando Hashes SHA-256. Se o programa fechar no meio de um arquivo gigante ou a internet cair, a proxima execucao retomara exatamente de onde parou em milissegundos.
* **Circuit Breaker (Disjuntor de Rede):** O motor de traducao possui um desarme de seguranca. Se a API falhar 5 vezes seguidas (ex: bloqueio de IP/Captcha), o sistema abre o circuito e suspende as chamadas por 60 segundos, evitando travamentos e banimentos permanentes.
* **Auditoria de Logs:** Toda a saida do programa e gravada silenciosamente em arquivos `.log` padronizados na pasta `logs/` contendo niveis de severidade e timestamps exatos.

## Como Usar (Instalacao Facil)

A ferramenta e "Plug and Play" no Windows.

1. Baixe o repositorio para o seu computador.
2. Certifique-se de ter o **Python 3.8+** instalado no sistema.
3. De um duplo-clique no arquivo **`iniciar.bat`**.

O `iniciar.bat` criara automaticamente um ambiente virtual (`venv/`), instalara as dependencias (`requirements.txt`) e abrira a interface grafica.

### Pre-requisitos (MKVToolNix)
Necessario apenas para videos embutidos (.mkv).
* Opcao 1 (Sistema): Instale o MKVToolNix (`C:\Program Files\MKVToolNix`).
* Opcao 2 (Portatil): Coloque os executaveis (`mkvmerge.exe` e `mkvextract.exe`) dentro da pasta `mkvtoolnix/` na raiz do projeto.

## Ambiente de Testes Massivos

O projeto conta com uma suite de testes isolada (`tests/`) focada em testes end-to-end e testes de unidade orientados a dados (Data-Driven Testing).

* **Como testar Unitarios:** Execute `python -m unittest discover -s tests\unit -p "test_*.py"`.
* **Como testar E2E:** Execute os scripts de lote dentro de `tests/e2e/`, como `test_mkv.py` ou `test_srt_lote.py`. O sistema consome diretamente a logica do `OrquestradorTraducoes` para bater as traducoes contra o cache local sem necessidade da interface grafica.
