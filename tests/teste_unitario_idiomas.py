import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradutor.idiomas import Idiomas

class TestIdiomas(unittest.TestCase):
    """
    Testes unitários para o módulo de mapeamento de idiomas.
    """
    
    def test_para_google(self):
        # Mapeamentos diretos ISO -> Google
        self.assertEqual(Idiomas.para_google("jpn"), "ja")
        self.assertEqual(Idiomas.para_google("eng"), "en")
        self.assertEqual(Idiomas.para_google("por"), "pt")
        self.assertEqual(Idiomas.para_google("fra"), "fr")
        
        # Códigos sem tag no MKV ou desconhecidos vão para "auto"
        self.assertEqual(Idiomas.para_google("und"), "auto")
        self.assertEqual(Idiomas.para_google("mul"), "auto")
        self.assertEqual(Idiomas.para_google("zzz"), "auto")
        self.assertEqual(Idiomas.para_google(""), "auto")
        
        # Códigos que já estão no padrão do Google passam direto
        self.assertEqual(Idiomas.para_google("pt"), "pt")
        self.assertEqual(Idiomas.para_google("ja"), "ja")
        self.assertEqual(Idiomas.para_google("auto"), "auto")

    def test_destino_para_mkv(self):
        # Google -> Tupla (ISO, Nome Legível) para o MKV
        self.assertEqual(Idiomas.destino_para_mkv("pt"), ("por", "Português (Brasil)"))
        self.assertEqual(Idiomas.destino_para_mkv("ja"), ("jpn", "日本語"))
        self.assertEqual(Idiomas.destino_para_mkv("en"), ("eng", "English"))
        
        # Destinos que não mapeamos com nome bonitinho devem ter fallback genérico
        self.assertEqual(Idiomas.destino_para_mkv("xyz"), ("xyz", "XYZ"))

if __name__ == "__main__":
    unittest.main()
