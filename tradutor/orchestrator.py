import os
import time
import asyncio
import threading

from .config import ConfigManager
from .mkv_wrapper import MkvWrapper
from .translator_service import TranslatorService


class TranslationOrchestrator:
    """Model layer: Orquestra o pipeline completo de tradução de arquivos.

    Não conhece a interface gráfica. Comunica-se exclusivamente
    através de callbacks injetados via set_callbacks().
    """

    def __init__(self):
        self._callbacks = {}
        self._is_running = False

    def set_callbacks(self, log_cb, progress_cb, ask_overwrite_cb, finish_cb):
        """Registra os callbacks de comunicação com a camada de apresentação."""
        self._callbacks['log'] = log_cb
        self._callbacks['progress'] = progress_cb
        self._callbacks['ask_overwrite'] = ask_overwrite_cb
        self._callbacks['finish'] = finish_cb

    def start(self, files, idioma_origem, idioma_destino, manter_legenda):
        """Inicia o processamento em lote em uma thread separada."""
        self._is_running = True
        threading.Thread(
            target=self._process_files,
            args=(files, idioma_origem, idioma_destino, manter_legenda),
            daemon=True
        ).start()

    def stop(self):
        """Sinaliza para interromper o processamento."""
        self._is_running = False

    def _process_files(self, files, idioma_origem, idioma_destino, manter_legenda):
        """Loop principal de processamento em lote."""
        log = self._callbacks.get('log', print)
        ask_overwrite = self._callbacks.get('ask_overwrite', lambda x: False)
        update_progress = self._callbacks.get('progress', lambda c, t: None)
        on_finish = self._callbacks.get('finish', lambda: None)

        tempo_total_inicio = time.time()
        total_arquivos = len(files)
        arquivos_sucesso = 0

        log("="*60)
        log(f"INICIANDO PROCESSAMENTO EM LOTE: {total_arquivos} arquivo(s)")
        log("="*60)

        for index, origem in enumerate(files, 1):
            if not self._is_running:
                break

            try:
                inicio_arquivo = time.time()
                log(f"\n--- Arquivo [{index}/{total_arquivos}]: {os.path.basename(origem)} ---")

                resultado = self._processar_arquivo(
                    origem, idioma_origem, idioma_destino, manter_legenda,
                    log, update_progress, ask_overwrite
                )

                if resultado:
                    elapsed = int(time.time() - inicio_arquivo)
                    log(f"-> Sucesso! Tempo gasto: {elapsed}s.")
                    arquivos_sucesso += 1

            except Exception as e:
                log(f"[ERRO CRÍTICO] Falha no arquivo {os.path.basename(origem)}: {e}")
                continue

        tempo_total_gasto = int(time.time() - tempo_total_inicio)
        log("\n" + "="*60)
        log("PROCESSAMENTO EM LOTE FINALIZADO")
        log(f"Sucesso: {arquivos_sucesso} de {total_arquivos} arquivos.")
        log(f"Tempo Total Gasto: {tempo_total_gasto}s")
        log("="*60)

        on_finish()

    def _processar_arquivo(self, origem, idioma_origem, idioma_destino, manter_legenda, log, update_progress, ask_overwrite):
        """Processa um único arquivo (legenda ou MKV).

        Returns:
            True se processado com sucesso, False se pulado pelo usuário.
        """
        destino_dir = os.path.dirname(origem)
        eh_mkv = origem.lower().endswith('.mkv')

        arquivo_trabalho = origem
        if eh_mkv:
            if not ConfigManager.check_dependencies():
                log("[AVISO] Processamento abortado. MKVToolNix não encontrado.")
                return False

            log(f"[Etapa 1/3] Extração de Mídia via MKVToolNix (Idioma: {idioma_origem or 'Qualquer'})")
            arquivo_trabalho = MkvWrapper.extrair_legenda(origem, destino_dir, idioma_origem, log)

        nome_base = os.path.basename(arquivo_trabalho)
        extensao = nome_base.rsplit('.', 1)[-1]
        nome_sem_ext = nome_base.rsplit('.', 1)[0].replace("_ORIGINAL", "")
        caminho_final_legenda = os.path.join(destino_dir, f"{nome_sem_ext}_{idioma_destino.upper()}.{extensao}")
        caminho_mkv_saida = os.path.join(destino_dir, f"{nome_sem_ext}_{idioma_destino.upper()}.mkv") if eh_mkv else None

        # Verificar conflito de nomes
        if not self._verificar_conflito(eh_mkv, caminho_final_legenda, caminho_mkv_saida,
                                         destino_dir, arquivo_trabalho, log, ask_overwrite):
            return False

        # Tradução
        etapa_trad = "2/3" if eh_mkv else "1/1"
        log(f"[Etapa {etapa_trad}] Tradução via Google Translate (Pysubs2)")

        translator_svc = TranslatorService(
            logger=log, 
            progress_callback=update_progress, 
            is_cancelled_callback=lambda: not self._is_running
        )
        asyncio.run(translator_svc.pipeline(arquivo_trabalho, caminho_final_legenda, idioma_origem, idioma_destino))
        
        if not self._is_running:
            return False

        # Multiplexação e limpeza (somente MKV)
        if eh_mkv:
            self._muxar_e_limpar(origem, caminho_final_legenda, destino_dir,
                                  arquivo_trabalho, manter_legenda, log)

        return True

    def _verificar_conflito(self, eh_mkv, caminho_legenda, caminho_mkv,
                              destino_dir, arquivo_trabalho, log, ask_overwrite):
        """Verifica se arquivos de saída já existem e pergunta ao usuário.

        Returns:
            True se pode prosseguir, False se o usuário optou por pular.
        """
        arquivos_conflito = []
        if not eh_mkv and os.path.exists(caminho_legenda):
            arquivos_conflito.append(os.path.basename(caminho_legenda))
        if caminho_mkv and os.path.exists(caminho_mkv):
            arquivos_conflito.append(os.path.basename(caminho_mkv))

        if not arquivos_conflito:
            return True

        nomes = ", ".join(arquivos_conflito)
        log(f"[AVISO] Arquivo(s) já existente(s): {nomes}")

        if not ask_overwrite(nomes):
            log("-> Arquivo pulado pelo usuário.")
            if eh_mkv and os.path.exists(arquivo_trabalho) and "_ORIGINAL" in arquivo_trabalho:
                os.remove(arquivo_trabalho)
            return False

        for arq in arquivos_conflito:
            caminho_arq = os.path.join(destino_dir, arq)
            if os.path.exists(caminho_arq):
                os.remove(caminho_arq)
        log("Arquivo(s) antigo(s) removido(s). Prosseguindo...")
        return True

    def _muxar_e_limpar(self, mkv_original, legenda_traduzida, destino_dir,
                          arquivo_trabalho, manter_legenda, log):
        """Embutir legenda no MKV e limpar arquivos temporários."""
        log("[Etapa 3/3] Multiplexação e Limpeza")
        MkvWrapper.embutir_legenda(mkv_original, legenda_traduzida, destino_dir, log)

        try:
            if os.path.exists(arquivo_trabalho) and "_ORIGINAL" in arquivo_trabalho:
                os.remove(arquivo_trabalho)

            if not manter_legenda:
                if os.path.exists(legenda_traduzida):
                    os.remove(legenda_traduzida)
                log("Lixo temporário de legendas limpo com sucesso.")
            else:
                log("Legenda traduzida mantida na pasta.")
        except Exception as e:
            log(f"Aviso: Falha na limpeza: {e}")
