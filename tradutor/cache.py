import sqlite3
import hashlib
import os

class CacheTraducoes:
    """
    Sistema de Caching em Banco de Dados (SQLite) para traduções.
    Previne que o mesmo bloco exato de texto seja enviado ao Google duas vezes,
    economizando tempo e protegendo contra rate-limits.
    Funciona como Checkpoint: se uma tradução grande cair aos 90%,
    a próxima tentativa vai pular os primeiros 90% instantaneamente.
    """
    def __init__(self, db_path="cache_traducoes.db"):
        # Salva o banco de dados na raiz do projeto
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path)
        self._init_db()
        
    def _init_db(self):
        """Cria a tabela de cache se ela não existir."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS traducoes (
                    hash_origem TEXT PRIMARY KEY,
                    src_lang TEXT,
                    dest_lang TEXT,
                    texto_traduzido TEXT,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
    def _gerar_hash(self, texto, src_lang, dest_lang):
        """Gera uma assinatura única (SHA-256) para o bloco de texto + idiomas."""
        raw = f"{src_lang}_{dest_lang}_{texto}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()
        
    def get(self, texto, src_lang, dest_lang):
        """Busca uma tradução no cache. Retorna None se não existir."""
        h = self._gerar_hash(texto, src_lang, dest_lang)
        # Context manager fecha a conexão automaticamente, thread-safe
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT texto_traduzido FROM traducoes WHERE hash_origem=?", (h,))
            row = cursor.fetchone()
            if row:
                return row[0]
        return None
        
    def put(self, texto, src_lang, dest_lang, texto_traduzido):
        """Salva uma nova tradução no cache."""
        h = self._gerar_hash(texto, src_lang, dest_lang)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO traducoes 
                (hash_origem, src_lang, dest_lang, texto_traduzido) 
                VALUES (?, ?, ?, ?)
            ''', (h, src_lang, dest_lang, texto_traduzido))
