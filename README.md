# Taradutor de Legendas 🎬

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Xaxadox/TradutorDeLegendas/tests.yml?style=flat-square&label=Testes%20CI)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square)

O **Taradutor de Legendas** é um tradutor automático e assíncrono projetado para lidar com arquivos MKV, SRT e ASS. Focado em alta performance e consistência, ele preserva contextos específicos de obras (animes, filmes) através de estratégias anti-alucinação e otimiza a velocidade usando cache e paralelismo avançado.

---

## 🚀 Principais Funcionalidades

- **Tradução em Lote Altamente Concorrente**: Usa `asyncio` e `ThreadPoolExecutor` para fatiar as legendas e traduzi-las paralelamente respeitando os limites da API do Google.
- **Cache Local Inteligente (SQLite)**: Conta com o sistema `CacheTraducoes` que grava *hashes* das frases já traduzidas. Reduz o consumo de API e permite continuar traduções interrompidas de forma instantânea.
- **Escudo Anti-Alucinação (Glossário Dinâmico)**: Mecanismo avançado de "Tokenização Isolada" que protege termos próprios.
- **Integração com AniList (`auto_alimentar`)**: O sistema busca automaticamente online os personagens do vídeo processado e constrói o dicionário de proteção dinamicamente antes da tradução iniciar!
- **Multiplexador MKV nativo**: Extração e embutimento nativo de faixas de legenda sem perda de qualidade, utilizando o `mkvtoolnix`.

## 🏗️ Arquitetura (Padrão MVC)

O código foi projetado seguindo as melhores práticas de Engenharia de Software, separando inteiramente a interface (View) da Lógica de Negócio (Model):
- `interface.py`: Interface Gráfica Responsiva via Tkinter.
- `controlador.py`: O mediador que delega as ações.
- `orquestrador.py`: O maestro da aplicação, utilizando o Design Pattern **Strategy** para saber como tratar arquivos de diferentes formatos.
- `servico_traducao.py`: Motor assíncrono que abstrai o provedor (permitindo trocar o Google Translate pela DeepL facilmente no futuro).

## 🛠️ Instalação e Execução

### Pré-requisitos
- Python 3.11+
- `mkvtoolnix` na raiz do projeto (se desejar suporte nativo a MKVs com embutimento).

### Rodando o projeto
```bash
# Clone o repositório
git clone https://github.com/Xaxadox/TradutorDeLegendas.git

# Crie e ative um ambiente virtual
python -m venv venv
.\venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Inicie a aplicação
python TaradutorLegendas26.py
```

---

## 🧪 Suíte de Testes e Qualidade (Padrão Comercial)

O repositório é coberto por testes unitários e de integração utilizando o `pytest`, blindado por uma esteira de **Integração Contínua (CI) via GitHub Actions**.

### Rodando os Testes Unitários
Os testes rodam 100% offline e não consomem internet nem manipulam seus arquivos reais (tudo é feito via injeção de `Mock` e diretórios `tmp_path` simulados na RAM).
```bash
pytest tests/unit/ -v
```

**O que o pytest cobre?**
- `test_glossario.py`: Lógica de tokenização reversível, protegendo capitalizações do Google Translate.
- `test_cache.py`: Operações do banco de dados SQLite sem corromper seu arquivo local de verdade.
- `test_servico_traducao.py`: Simulador assíncrono de API. Força "Timeouts" e "Dessincronias" na resposta do Google para validar se o sistema aciona com sucesso o Fallback Sequencial.
- `test_alimentar_glossario.py`: Regex de sanitização de arquivos e mock do requests para validar extrações da API AniList.

### Rodando o Teste E2E
Possuímos scripts de validação de rotinas "End-to-End". Eles testam pastas inteiras e lidam com MKVs.
```bash
python tests/e2e/test_srt_lote.py
```
> **Nota de Arquitetura E2E**: O `test_srt_lote` possui um interceptador embutido que "falsifica" a resposta do Google Translate. Isso permite que você rode milhares de legendas em poucos segundos sem ser bloqueado pela API (Rate Limit)!
