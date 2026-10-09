import os
import sys
import pytest
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tradutor.cache import CacheTraducoes

@pytest.fixture
def cache_temporario(tmp_path):
    """
    Cria uma instância do Cache apontando para um banco de dados real 
    temporário criado pelo pytest (que será deletado ao fim do teste).
    Isso é necessário pois a classe abre e fecha conexões a cada operação,
    o que apagaria os dados se usássemos ":memory:".
    """
    # Como tmp_path é um caminho absoluto, o os.path.join dentro do cache
    # irá ignorar o diretório base do projeto e usar o caminho absoluto temporário.
    db_fake = str(tmp_path / "teste_cache.db")
    return CacheTraducoes(db_path=db_fake)


def test_criacao_implicita_tabela(cache_temporario):
    """Verifica se a tabela 'traducoes' é criada automaticamente no construtor."""
    # Acessa o banco diretamente para ver se a tabela existe
    with sqlite3.connect(cache_temporario.db_path) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='traducoes';")
        tabela = cursor.fetchone()
        
    assert tabela is not None
    assert tabela[0] == "traducoes"


def test_put_e_get_basico(cache_temporario):
    """Testa se o cache salva (put) e recupera (get) uma tradução (Hit)."""
    texto = "Hello World"
    traducao = "Olá Mundo"
    
    # Busca antes de inserir (Miss)
    assert cache_temporario.get(texto, "en", "pt") is None
    
    # Insere
    cache_temporario.put(texto, "en", "pt", traducao)
    
    # Busca depois de inserir (Hit)
    resultado = cache_temporario.get(texto, "en", "pt")
    assert resultado == traducao


def test_isolamento_por_idiomas(cache_temporario):
    """
    Garante que traduções do mesmo texto mas para idiomas 
    diferentes não se sobrescrevem (verificação do Hash).
    """
    texto = "Good Morning"
    
    cache_temporario.put(texto, "en", "pt", "Bom dia")
    cache_temporario.put(texto, "en", "es", "Buenos días")
    
    assert cache_temporario.get(texto, "en", "pt") == "Bom dia"
    assert cache_temporario.get(texto, "en", "es") == "Buenos días"
    # Miss para um destino não cacheado
    assert cache_temporario.get(texto, "en", "ja") is None


def test_sobrescrita_update(cache_temporario):
    """
    Se fizermos um PUT novamente com o mesmo texto e idiomas, 
    a tradução deve ser atualizada e não deve gerar erro de Unique Constraint.
    """
    texto = "Apple"
    
    cache_temporario.put(texto, "en", "pt", "Maca")
    assert cache_temporario.get(texto, "en", "pt") == "Maca"
    
    # Atualiza (corrigindo acento)
    cache_temporario.put(texto, "en", "pt", "Maçã")
    assert cache_temporario.get(texto, "en", "pt") == "Maçã"
