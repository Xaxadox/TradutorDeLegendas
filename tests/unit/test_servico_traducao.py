import pytest
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tradutor.servico_traducao import ServicoTraducao

class EventoLegendaDummy:
    """Mock básico para simular eventos de legenda do pysubs2."""
    def __init__(self, text):
        self.text = text

@pytest.fixture
def servico_setup(mocker):
    """
    Fixture que cria uma instância de ServicoTraducao isolada:
    - Sem Banco de Dados Real (Cache mockado)
    - Sem Acesso a Disco (Glossario mockado)
    - Com Callbacks de log e progresso falsos.
    """
    mocker.patch('tradutor.servico_traducao.CacheTraducoes')
    mocker.patch('tradutor.servico_traducao.GerenciadorGlossario')
    
    mock_logger = MagicMock()
    mock_progress = MagicMock()
    mock_engine = MagicMock()
    
    servico = ServicoTraducao(
        logger=mock_logger,
        progress_callback=mock_progress,
        engine=mock_engine,
        video_filename="fake_video.mkv"
    )
    
    # Mockando o comportamento padrão do glossario injetado
    servico._glossary.apply_shield.side_effect = lambda text: (text, {})
    servico._glossary.remove_shield.side_effect = lambda text, map: text
    
    # Mockando o comportamento do cache
    servico._cache.get.return_value = None
    
    return servico, mock_engine, mock_logger, mock_progress


@pytest.mark.asyncio
async def test_traduzir_lote_happy_path(servico_setup):
    """
    Cenário A: O motor traduz perfeitamente um lote.
    A quantidade de linhas retornadas bate com a enviada.
    """
    servico, mock_engine, _, _ = servico_setup
    
    # Configura o retorno do Engine para ser idêntico em quantidade de linhas
    mock_engine.translate.return_value = "Linha 1 traduzida\nLinha 2 traduzida\nLinha 3 traduzida"
    
    subs = [
        EventoLegendaDummy("Line 1"),
        EventoLegendaDummy("Line 2"),
        EventoLegendaDummy("Line 3")
    ]
    lote_indices = [0, 1, 2]
    
    semaforo = asyncio.Semaphore(1)
    pbar_lock = threading.Lock()
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        await servico._traduzir_lote(executor, semaforo, lote_indices, subs, pbar_lock)
        
    # Verifica se o motor foi chamado exatamente 1 vez (em lote)
    assert mock_engine.translate.call_count == 1
    
    # Verifica se os objetos originais foram atualizados
    assert subs[0].text == "Linha 1 traduzida"
    assert subs[1].text == "Linha 2 traduzida"
    assert subs[2].text == "Linha 3 traduzida"


@pytest.mark.asyncio
async def test_traduzir_lote_fallback_sequencial(servico_setup):
    """
    Cenário B: O motor "alucina" e retorna menos linhas do que o lote continha.
    O sistema DEVE detectar a dessincronia e enviar cada linha individualmente.
    """
    servico, mock_engine, mock_logger, _ = servico_setup
    
    # O motor foi mandado traduzir 3 linhas, mas devolve 2 (dessincronia).
    # Como ele vai rodar sequencial depois, usamos um side_effect para a primeira vez devolver erro de lote
    # E as 3 vezes subsequentes devolverem traduções singulares.
    mock_engine.translate.side_effect = [
        "Linha única e errada, o google comeu o resto",  # Lote quebrado
        "Linha 1 fallback",                              # Fallback 1
        "Linha 2 fallback",                              # Fallback 2
        "Linha 3 fallback"                               # Fallback 3
    ]
    
    subs = [
        EventoLegendaDummy("Line 1"),
        EventoLegendaDummy("Line 2"),
        EventoLegendaDummy("Line 3")
    ]
    lote_indices = [0, 1, 2]
    
    semaforo = asyncio.Semaphore(1)
    pbar_lock = threading.Lock()
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        await servico._traduzir_lote(executor, semaforo, lote_indices, subs, pbar_lock)
        
    # Deve ter chamado 4 vezes: 1 para a tentativa em lote + 3 para o fallback sequencial
    assert mock_engine.translate.call_count == 4
    
    # Deve registrar no logger o aviso do fallback
    mock_logger.assert_any_call("[Aviso] Dessincronia no lote. Executando fallback sequencial...")
    
    # Verifica se a tradução final recuperou com os fallbacks
    assert subs[0].text == "Linha 1 fallback"
    assert subs[1].text == "Linha 2 fallback"
    assert subs[2].text == "Linha 3 fallback"


@pytest.mark.asyncio
async def test_traduzir_lote_excecao(servico_setup):
    """
    Cenário C: A API cai, ou o banco recusa a conexão (Erro Crítico).
    O lote deve ser ignorado de forma segura, mantendo o texto original.
    """
    servico, mock_engine, mock_logger, _ = servico_setup
    
    # Força um erro crítico na API
    mock_engine.translate.side_effect = Exception("Internal Server Error")
    
    subs = [
        EventoLegendaDummy("Keep me 1"),
        EventoLegendaDummy("Keep me 2")
    ]
    lote_indices = [0, 1]
    
    semaforo = asyncio.Semaphore(1)
    pbar_lock = threading.Lock()
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        await servico._traduzir_lote(executor, semaforo, lote_indices, subs, pbar_lock)
        
    # O logger deve reportar erro crítico
    logger_calls = [call.args[0] for call in mock_logger.call_args_list]
    assert any("[Erro Crítico] Lote ignorado" in call for call in logger_calls)
    
    # As legendas originais não podem ter sido apagadas
    assert subs[0].text == "Keep me 1"
    assert subs[1].text == "Keep me 2"
