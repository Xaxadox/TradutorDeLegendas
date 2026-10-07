import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tradutor.idiomas import Idiomas

class TestIdiomas(unittest.TestCase):
    """
    Testes unitários para o módulo de mapeamento de idiomas.
    """
    
    def test_para_google(self):
        casos = {
            # ISO -> Google
            "jpn": "ja", "eng": "en", "por": "pt", "fra": "fr",
            # Fallbacks e vazios
            "und": "auto", "mul": "auto", "zzz": "auto", "": "auto",
            # Já estão no padrão do Google
            "pt": "pt", "ja": "ja", "auto": "auto"
        }
        for entrada, esperado in casos.items():
            with self.subTest(entrada=entrada):
                self.assertEqual(Idiomas.para_google(entrada), esperado)

    def test_destino_para_mkv(self):
        casos = {
            "pt": ("por", "Português (Brasil)"),
            "ja": ("jpn", "日本語"),
            "en": ("eng", "English"),
            "xyz": ("xyz", "XYZ") # Destino desconhecido
        }
        for entrada, esperado in casos.items():
            with self.subTest(entrada=entrada):
                self.assertEqual(Idiomas.destino_para_mkv(entrada), esperado)

if __name__ == "__main__":
    unittest.main()
