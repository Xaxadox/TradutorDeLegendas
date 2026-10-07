import os
from .processador_base import ProcessadorArquivoBase
from ..manipulador_mkv import ManipuladorMkv
from ..config import GerenciadorConfig

class ProcessadorMkv(ProcessadorArquivoBase):
    """Estratégia específica para arquivos de vídeo MKV."""

    def prepare(self, origem, idioma_origem):
        if not GerenciadorConfig.check_dependencies():
            self.log("[AVISO] Processamento abortado. MKVToolNix não encontrado.")
            return None, None
            
        self.log(f"[Etapa 1/3] Extração de Mídia via MKVToolNix (Idioma: {idioma_origem or 'Qualquer'})")
        destino_dir = os.path.dirname(origem)
        return ManipuladorMkv.extrair_legenda(origem, destino_dir, idioma_origem, self.log)

    def should_skip_if_same_language(self) -> bool:
        return True

    def cleanup_temporary(self, arq_trabalho):
        if os.path.exists(arq_trabalho) and "_ORIGINAL" in arq_trabalho:
            os.remove(arq_trabalho)

    def get_output_paths(self, origem, idioma_destino, arq_trabalho) -> dict:
        destino_dir = os.path.dirname(origem)
        nome_base = os.path.basename(arq_trabalho)
        extensao = nome_base.rsplit('.', 1)[-1]
        nome_sem_ext = nome_base.rsplit('.', 1)[0].replace("_ORIGINAL", "")
        
        return {
            'legenda': os.path.join(destino_dir, f"{nome_sem_ext}_{idioma_destino.upper()}.{extensao}"),
            'video': os.path.join(destino_dir, f"{nome_sem_ext}_{idioma_destino.upper()}.mkv")
        }

    def get_translation_message(self) -> str:
        return "[Etapa 2/3] Tradução via Motor Injetado (Pysubs2)"

    def finalize(self, origem, legenda_traduzida, caminhos_saida, idioma_destino, arq_trabalho, manter_legenda):
        self.log("[Etapa 3/3] Multiplexação e Limpeza")
        caminho_mkv_saida = caminhos_saida['video']
        
        ManipuladorMkv.embutir_legenda(origem, legenda_traduzida, caminho_mkv_saida, idioma_destino, self.log)

        try:
            self.cleanup_temporary(arq_trabalho)
            if not manter_legenda:
                if os.path.exists(legenda_traduzida):
                    os.remove(legenda_traduzida)
                self.log("Lixo temporário de legendas limpo com sucesso.")
            else:
                self.log("Legenda traduzida mantida na pasta.")
        except Exception as e:
            self.log(f"Aviso: Falha na limpeza: {e}")
