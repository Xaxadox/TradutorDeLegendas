import os
import time
import threading

from .estrategias import FabricaProcessadores
from .logger import app_logger

class OrquestradorTraducoes:
    """Model layer: Orquestra o pipeline completo de tradução de arquivos.

    Não conhece a interface gráfica. Comunica-se exclusivamente
    através de callbacks injetados via set_callbacks().
    """

    def __init__(self):
        self._callbacks = {}
        self._is_running = False

    def set_callbacks(self, log_cb, progress_cb, ask_overwrite_cb, finish_cb):
        """Registra os callbacks de comunicação com a camada de apresentação."""
        def custom_log(msg):
            # Salva silenciosamente em arquivo
            app_logger.info(msg)
            # Envia para a interface gráfica
            log_cb(msg)

        self._callbacks['log'] = custom_log
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

                # Devolvemos a responsabilidade de saber COMO processar para o Factory/Strategy
                processador = FabricaProcessadores.get_processor(
                    origem, log, update_progress, ask_overwrite, lambda: self._is_running
                )
                resultado = processador.process(origem, idioma_origem, idioma_destino, manter_legenda)

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
