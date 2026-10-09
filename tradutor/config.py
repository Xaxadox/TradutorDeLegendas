import os


class GerenciadorConfig:
    """Configurações globais e detecção de dependências do projeto."""

    TAMANHO_LOTE = 40
    MAX_CONCORRENTE = 5
    MAX_RETENTATIVAS = 3

    # Raiz do projeto = diretório pai de tradutor/
    DIRETORIO_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOCAL_MKVTOOLNIX = os.path.join(DIRETORIO_PROJETO, "mkvtoolnix")
    SYSTEM_MKVTOOLNIX = r"C:\Program Files\MKVToolNix"
    ARQUIVO_GLOSSARIO_PADRAO = os.path.join(DIRETORIO_PROJETO, "glossario.txt")
    DIRETORIO_GLOSSARIOS = os.path.join(DIRETORIO_PROJETO, "glossarios")

    @classmethod
    def get_mkvtoolnix_path(cls):
        """Retorna o caminho do MKVToolNix, priorizando a cópia local."""
        if os.path.exists(os.path.join(cls.LOCAL_MKVTOOLNIX, "mkvmerge.exe")):
            return cls.LOCAL_MKVTOOLNIX
        return cls.SYSTEM_MKVTOOLNIX

    @classmethod
    def get_mkv_bins(cls):
        """Retorna tupla (mkvmerge, mkvextract) com caminhos absolutos."""
        path = cls.get_mkvtoolnix_path()
        return os.path.join(path, "mkvmerge.exe"), os.path.join(path, "mkvextract.exe")

    @classmethod
    def check_dependencies(cls):
        """Verifica se mkvmerge e mkvextract existem no sistema."""
        mkvmerge, mkvextract = cls.get_mkv_bins()
        return os.path.exists(mkvmerge) and os.path.exists(mkvextract)
