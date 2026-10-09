import os
import sys
import pytest
from unittest.mock import MagicMock, mock_open

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from alimentar_glossario import limpar_nome_anime, auto_alimentar

@pytest.mark.parametrize("nome_arquivo, nome_esperado", [
    ("[SubsPlease] Bleach - Thousand-Year Blood War - 30 (1080p).mkv", "Bleach Thousand Year Blood War"),
    ("[Erai-raws] One Piece - 1098 [1080p][Multiple Subtitle].mkv", "One Piece"),
    ("Jujutsu Kaisen S2 - 05.mkv", "Jujutsu Kaisen S2"),
    ("[Crunchyroll] Tensei Shitara Slime Datta Ken 3rd Season - 48 (1080p).mkv", "Tensei Shitara Slime Datta Ken 3rd Season"),
    ("Naruto Shippuden_15.mp4", "Naruto Shippuden"),
    ("Shingeki no Kyojin - The Final Season Part 2 - 01v2 (1080p).mkv", "Shingeki no Kyojin The Final Season Part 2")
])
def test_limpar_nome_anime(nome_arquivo, nome_esperado):
    """Garante que a regex de limpeza funciona para diversos padrões comuns de fansubs."""
    assert limpar_nome_anime(nome_arquivo) == nome_esperado


def test_auto_alimentar_api_falha(mocker):
    """Garante que se a API do AniList falhar, a função retorna None sem crachar."""
    mock_post = mocker.patch('alimentar_glossario.requests.post')
    mock_post.side_effect = Exception("Erro de conexão simulado")
    
    resultado = auto_alimentar("[SubsPlease] Anime Inexistente - 01 (1080p).mkv")
    assert resultado is None


def test_auto_alimentar_sucesso(mocker):
    """Testa o fluxo feliz: encontra o anime, busca personagens e cria o arquivo no disco mockado."""
    mock_post = mocker.patch('alimentar_glossario.requests.post')
    
    mock_response_anime = MagicMock()
    mock_response_anime.json.return_value = {
        'data': {'Page': {'media': [{'id': 1234, 'title': {'romaji': 'Teste Anime', 'english': 'Test Anime'}}]}}
    }
    
    mock_response_chars = MagicMock()
    mock_response_chars.json.return_value = {
        'data': {'Media': {'characters': {'nodes': [
            {'name': {'first': 'John', 'last': 'Doe', 'full': 'John Doe'}},
            {'name': {'first': 'Jane', 'last': None, 'full': 'Jane'}}
        ]}}}
    }
    
    mock_post.side_effect = [mock_response_anime, mock_response_chars]
    
    # Isola o sistema de arquivos
    mocker.patch('os.makedirs')
    mocked_open = mocker.patch('builtins.open', mock_open())
    
    resultado = auto_alimentar("[Teste] Teste Anime - 01.mkv")
    
    assert resultado is not None
    assert resultado.endswith('Teste Anime.txt')
    
    mocked_open.assert_called_with(resultado, "w", encoding="utf-8")
    
    # Verifica o que foi gravado
    handle = mocked_open()
    calls = [call.args[0] for call in handle.write.mock_calls]
    conteudo_escrito = "".join(calls)
    
    assert "John Doe\n" in conteudo_escrito
    assert "Jane\n" in conteudo_escrito
    assert "John\n" in conteudo_escrito
    assert "Doe\n" in conteudo_escrito
