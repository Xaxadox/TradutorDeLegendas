import os
from .processador_base import ProcessadorArquivoBase

class ProcessadorSrt(ProcessadorArquivoBase):
    """Estratégia específica para legendas avulsas (SRT, ASS)."""

    def prepare(self, origem, idioma_origem):
        # Para SRT, o arquivo de trabalho é ele mesmo
        return origem, idioma_origem

    def should_skip_if_same_language(self) -> bool:
        # Legendas soltas não pulam, pois o menu pode estar errado
        return False

    def cleanup_temporary(self, arq_trabalho):
        pass # Não há arquivos "_ORIGINAL" para SRT avulso

    def get_output_paths(self, origem, idioma_destino, arq_trabalho) -> dict:
        destino_dir = os.path.dirname(origem)
        nome_base = os.path.basename(origem)
        extensao = nome_base.rsplit('.', 1)[-1]
        nome_sem_ext = nome_base.rsplit('.', 1)[0]
        
        return {
            'legenda': os.path.join(destino_dir, f"{nome_sem_ext}_{idioma_destino.upper()}.{extensao}"),
            'video': None
        }

    def get_translation_message(self) -> str:
        return "[Etapa 1/1] Tradução via Motor Injetado (Pysubs2)"

    def finalize(self, origem, legenda_traduzida, caminhos_saida, idioma_destino, arq_trabalho, manter_legenda):
        # Para legendas avulsas, não há multiplexação, apenas sucesso!
        pass
