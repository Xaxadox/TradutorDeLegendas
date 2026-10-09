import os
import asyncio
from abc import ABC, abstractmethod

from ..config import GerenciadorConfig
from ..servico_traducao import ServicoTraducao
from ..tradutores import MotorTraducaoGoogle
from ..idiomas import Idiomas

class ProcessadorArquivoBase(ABC):
    """
    Template Method Pattern: Define o esqueleto (esqueleto) do processamento
    de qualquer arquivo (MKV, SRT, MP4 no futuro). Delega os detalhes
    específicos para as subclasses (Estratégias).
    """

    def __init__(self, log_cb, progress_cb, ask_overwrite_cb, is_running_cb):
        self.log = log_cb
        self.update_progress = progress_cb
        self.ask_overwrite = ask_overwrite_cb
        self.is_running = is_running_cb

    def process(self, origem, idioma_origem, idioma_destino, manter_legenda) -> bool:
        """Executa o pipeline padrão para um arquivo."""
        
        # 1. Preparação Específica (Extracao MKV ou Bypass SRT)
        arq_trabalho, idioma_real = self.prepare(origem, idioma_origem)
        if not arq_trabalho:
            return False

        # 2. Verificações de Idioma
        src_google = Idiomas.para_google(idioma_real)
        if src_google == "auto":
            self.log(f"[AVISO] Idioma de origem indefinido. Usando autodetecção.")
        else:
            self.log(f"Idioma de origem: {idioma_real} (Google: {src_google})")

        if src_google == idioma_destino.lower():
            if self.should_skip_if_same_language():
                self.log(f"-> Origem e destino iguais ({src_google}). Arquivo pulado.")
                self.cleanup_temporary(arq_trabalho)
                return False
            else:
                self.log(f"[AVISO] Origem e destino iguais ({src_google}). Prosseguindo (avulso).")

        # 3. Resolução de Caminhos de Saída
        caminhos_saida = self.get_output_paths(origem, idioma_destino, arq_trabalho)
        
        # 4. Verificação de Conflitos (Arquivos Existentes)
        if not self._check_conflicts(caminhos_saida, arq_trabalho):
            return False

        try:
            # 5. Tradução (Core)
            self.log(self.get_translation_message())
            engine = MotorTraducaoGoogle(max_retries=GerenciadorConfig.MAX_RETENTATIVAS)
            translator_svc = ServicoTraducao(
                logger=self.log, 
                progress_callback=self.update_progress, 
                is_cancelled_callback=lambda: not self.is_running(),
                engine=engine,
                video_filename=os.path.basename(origem)
            )
            
            caminho_legenda_final = caminhos_saida['legenda']
            asyncio.run(translator_svc.pipeline(arq_trabalho, caminho_legenda_final, idioma_real, idioma_destino))
            
            if not self.is_running():
                return False

            # 6. Finalização Específica (Muxing MKV ou Bypass SRT)
            self.finalize(origem, caminho_legenda_final, caminhos_saida, idioma_destino, arq_trabalho, manter_legenda)
            return True
        finally:
            if not self.is_running():
                self.cleanup_temporary(arq_trabalho)

    def _check_conflicts(self, caminhos_saida, arq_trabalho) -> bool:
        """Lógica comum para perguntar ao usuário sobre arquivos existentes."""
        conflitos = [os.path.basename(p) for p in caminhos_saida.values() if p and os.path.exists(p)]
        if not conflitos:
            return True

        nomes = ", ".join(conflitos)
        self.log(f"[AVISO] Arquivo(s) já existente(s): {nomes}")

        if not self.ask_overwrite(nomes):
            self.log("-> Arquivo pulado pelo usuário.")
            self.cleanup_temporary(arq_trabalho)
            return False

        for path in caminhos_saida.values():
            if path and os.path.exists(path):
                os.remove(path)
        self.log("Arquivo(s) antigo(s) removido(s). Prosseguindo...")
        return True

    # ---- MÉTODOS ABSTRATOS PARA AS SUBCLASSES ----
    
    @abstractmethod
    def prepare(self, origem, idioma_origem):
        """Retorna (caminho_arquivo_trabalho, idioma_real)."""
        pass

    @abstractmethod
    def should_skip_if_same_language(self) -> bool:
        pass

    @abstractmethod
    def cleanup_temporary(self, arq_trabalho):
        pass

    @abstractmethod
    def get_output_paths(self, origem, idioma_destino, arq_trabalho) -> dict:
        """Retorna dict com chaves como 'legenda' e 'video'."""
        pass

    @abstractmethod
    def get_translation_message(self) -> str:
        pass

    @abstractmethod
    def finalize(self, origem, legenda_traduzida, caminhos_saida, idioma_destino, arq_trabalho, manter_legenda):
        pass
