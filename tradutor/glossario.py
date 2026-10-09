import os
import re
from .config import GerenciadorConfig

class GerenciadorGlossario:
    """Gerenciador do Dicionário Anti-Tradução (Glossário).
    
    Implementa a técnica de Tokenização Isolada:
    Substitui termos protegidos por tokens alienígenas antes de enviar ao Google,
    e restaura os termos originais após a tradução, impedindo alucinações da API.
    """
    
    def __init__(self, filepath=None, video_filename=None, habilitar_auto_alimentar=False):
        self.filepath = filepath or GerenciadorConfig.ARQUIVO_GLOSSARIO_PADRAO
        self.video_filename = video_filename
        self.habilitar_auto_alimentar = habilitar_auto_alimentar
        self.glossario_map = {}
        self.load()

    def _load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        src, tgt = line.split('=', 1)
                        self.glossario_map[src.strip()] = tgt.strip()
                    else:
                        self.glossario_map[line] = line
        except Exception:
            pass

    def load(self):
        """Carrega os termos do arquivo de glossário global e específicos."""
        if not os.path.exists(self.filepath):
            # Cria um arquivo de exemplo se não existir
            try:
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    f.write("# Dicionário / Glossário de Proteção\n")
                    f.write("# Adicione as palavras que você NÃO quer que o Google traduza errado.\n")
                    f.write("# Formato 1: Palavra Original = Palavra Destino\n")
                    f.write("# Formato 2: Apenas a Palavra (protege contra qualquer mudança)\n")
                    f.write("# Exemplos:\n")
                    f.write("# The Force=A Força\n")
                    f.write("# Hogwarts\n")
                    f.write("# Goku\n")
            except Exception:
                pass
        else:
            self._load_file(self.filepath)
            
        # Carrega dicionários específicos baseados no nome do vídeo
        dir_especificos = GerenciadorConfig.DIRETORIO_GLOSSARIOS
        if not os.path.exists(dir_especificos):
            try:
                os.makedirs(dir_especificos, exist_ok=True)
                with open(os.path.join(dir_especificos, 'LEIA_ME.txt'), 'w', encoding='utf-8') as f:
                    f.write("Coloque aqui dicionários específicos de animes (ex: Bleach.txt, One Piece.txt).\n")
                    f.write("Se o nome do vídeo que está sendo traduzido contiver o nome do arquivo, este dicionário será carregado automaticamente junto com o global.\n")
            except Exception:
                pass
                
        encontrou_especifico = False
        if self.video_filename and os.path.exists(dir_especificos):
            video_name_lower = self.video_filename.lower()
            for arquivo in os.listdir(dir_especificos):
                if arquivo.lower().endswith(".txt") and arquivo.lower() != "leia_me.txt":
                    nome_anime = arquivo[:-4].lower() # remove .txt
                    if nome_anime in video_name_lower:
                        self._load_file(os.path.join(dir_especificos, arquivo))
                        encontrou_especifico = True
            
            # Se não encontrou na pasta e a busca automática estiver ativada, roda o extrator
            if not encontrou_especifico and self.habilitar_auto_alimentar:
                try:
                    import sys
                    raiz_projeto = GerenciadorConfig.DIRETORIO_PROJETO
                    if raiz_projeto not in sys.path:
                        sys.path.insert(0, raiz_projeto)
                    
                    from alimentar_glossario import auto_alimentar
                    novo_arquivo = auto_alimentar(self.video_filename)
                    if novo_arquivo and os.path.exists(novo_arquivo):
                        self._load_file(novo_arquivo)
                except Exception:
                    pass

    def apply_shield(self, text):
        """Aplica o escudo substituindo termos por tokens."""
        mapping = {}
        if not self.glossario_map:
            return text, mapping
            
        shielded_text = text
        counter = 0
        # Substitui os termos mais longos primeiro para evitar conflitos parciais
        sorted_keys = sorted(self.glossario_map.keys(), key=len, reverse=True)
        
        for key in sorted_keys:
            escaped_key = re.escape(key)
            pattern = re.compile(rf'(?i)\b{escaped_key}\b')
            
            def repl(match):
                nonlocal counter
                token = f"TKGLOSS{counter}T"
                mapping[token] = self.glossario_map[key]
                counter += 1
                return f" {token} "

            shielded_text, _ = pattern.subn(repl, shielded_text)
            
        return shielded_text, mapping

    def remove_shield(self, text, mapping):
        """Remove o escudo restaurando os termos traduzidos."""
        if not mapping:
            return text
            
        final_text = text
        for token, tgt in mapping.items():
            # O token sempre começa com TKGLOSS e termina com T
            # Essa regex captura se o Google tentar quebrar, minuscular ou espaçar o token.
            num = token[7:-1]
            pattern = re.compile(r'(?i)\bT\s*K\s*G\s*L\s*O\s*S\s*S\s*' + str(num) + r'\s*T\b')
            final_text = pattern.sub(lambda _: tgt, final_text)
            
        # Limpa espaços duplos que possam ter sido injetados
        final_text = re.sub(r' +', ' ', final_text).strip()
        return final_text
