# Taradutor de Legendas

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Xaxadox/TradutorDeLegendas/tests.yml?style=flat-square&label=Testes%20CI)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-green?style=flat-square)

O **Taradutor de Legendas** é uma ferramenta de automação para extração, tradução e multiplexação de legendas em arquivos de vídeo MKV, bem como legendas avulsas nos formatos SRT e ASS. O sistema emprega processamento assíncrono para garantir alto desempenho, acompanhado por tolerância a falhas, cache persistente local e proteção de contexto via glossário dinâmico.

---

## Funcionalidades Principais

- **Tradução em Lote Concorrente:** Utiliza `asyncio` e `ThreadPoolExecutor` para particionar e traduzir legendas em paralelo, respeitando a cadência da API.
- **Cache Local Inteligente (SQLite):** Sistema `CacheTraducoes` que armazena assinaturas SHA-256 das frases traduzidas. Reduz requisições repetidas e permite retomar execuções interrompidas de forma instantânea.
- **Escudo Anti-Alucinação (Tokenização Isolada):** Substitui nomes próprios e termos específicos por tokens protegidos antes do envio ao motor de tradução e restaura os valores originais após a resposta.
- **Dicionários Específicos e Integração AniList:** Suporta glossários customizados por obra na pasta `glossarios/` e rotina opcional de extração automática de personagens (`auto_alimentar`).
- **Automação MKV de Ponta a Ponta:** Extrai trilhas de legenda do vídeo original, traduz preservando estilizações e embute a nova faixa traduzida no arquivo final (`<nome>_<DESTINO>.mkv`) via MKVToolNix.
- **Detecção e Mapeamento de Idiomas:** Varre faixas disponíveis em contêineres MKV e mapeia códigos ISO-639-2 para códigos ISO-639-1 do Google Translate, mitigando vazamentos de língua intermediária ("língua pivô").

---

## Tolerância a Falhas e Resiliência

- **Circuit Breaker (Disjuntor de Rede):** O motor de tradução monitora falhas consecutivas da API. Se o limiar configurado for atingido, o circuito abre temporariamente para evitar banimentos de IP e bloqueios de thread.
- **Fallback Sequencial:** Se a tradução em lote apresentar discrepância na contagem de linhas retornadas, o sistema comuta automaticamente para tradução individual item a item com consulta ao cache.
- **Auditoria Estruturada de Logs:** Toda a operação do sistema é gravada em arquivos rotativos na pasta `logs/`, contendo níveis de severidade, contexto e timestamps detalhados.

---

## Arquitetura (Padrão MVC e Strategy)

O projeto é estruturado segundo os princípios de separação de responsabilidades (MVC e Design Patterns):

- **View (`tradutor/interface.py`):** Interface gráfica responsiva desenvolvida com CustomTkinter, com suporte a Drag and Drop (arrastar e soltar arquivos).
- **Controller (`tradutor/controlador.py`):** Camada mediadora que processa comandos do usuário e sincroniza eventos entre a interface e as regras de negócio.
- **Model / Orquestrador (`tradutor/orquestrador.py`):** Gerenciador de pipeline que coordena o fluxo em lote de forma desacoplada da interface gráfica.
- **Estratégias (`tradutor/estrategias/`):** Aplicação do Strategy Pattern via `FabricaProcessadores`, delegando a lógica especializada para `ProcessadorMkv` ou `ProcessadorSrt`.
- **Serviço de Tradução (`tradutor/servico_traducao.py`):** Motor assíncrono que abstrai provedores de tradução através da interface `ITradutor`.

---

## Instalação e Execução

### Pré-requisitos
- Python 3.11 ou superior.
- MKVToolNix (necessário para processar arquivos `.mkv`):
  - **Opção 1 (Portátil):** Coloque os executáveis `mkvmerge.exe` e `mkvextract.exe` na pasta `mkvtoolnix/` na raiz do projeto.
  - **Opção 2 (Sistema):** Instale o MKVToolNix no caminho padrão (`C:\Program Files\MKVToolNix`).

### Execução Rápida (Windows)
Dê um duplo clique no arquivo **`iniciar.bat`**. O script configura automaticamente o ambiente virtual (`venv/`), valida as dependências e inicia a aplicação.

### Execução Manual
```bash
# Clone o repositório
git clone https://github.com/Xaxadox/TradutorDeLegendas.git

# Crie e ative o ambiente virtual
python -m venv venv
.\venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Inicie a aplicação
python TaradutorLegendas26.py
```

---

## Suíte de Testes e Qualidade

O repositório possui cobertura de testes unitários e de integração com pytest, além de integração contínua (CI) via GitHub Actions.

### Testes Unitários
Os testes rodam de forma offline, utilizando diretórios temporários na memória e injeção de mocks:
```bash
pytest tests/unit/ -v
```
Você também pode rodar os testes unitários diretamente pelo script auxiliar **`testar.bat`**.

**Cobertura dos testes:**
- `test_glossario.py`: Validação da tokenização reversível e proteção de capitalização.
- `test_cache.py`: Operações de leitura, escrita e isolamento por idioma no SQLite.
- `test_servico_traducao.py`: Simulação assíncrona da API, timeouts e mecanismo de fallback sequencial.
- `test_alimentar_glossario.py`: Sanitização de nomes de arquivo e chamadas mockadas à API AniList.
- `test_idiomas.py`: Conversão bidirecional entre códigos ISO-639-2 e códigos do Google Translate.

### Teste E2E (End-to-End)
Validação de pipelines completos de lote em ambiente controlado:
```bash
python tests/e2e/test_srt_lote.py
```

---

## Licença

Este projeto está licenciado sob os termos da licença MIT. Para mais detalhes, consulte o arquivo [LICENSE](LICENSE).
