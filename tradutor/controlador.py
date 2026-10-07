class ControladorApp:
    """Controller layer: Ponte entre a View (GUI) e o Model (Orchestrator).

    Traduz ações do usuário em operações de negócio e conecta
    os callbacks do Model aos métodos de atualização da View.
    """

    def __init__(self, view, model):
        self._view = view
        self._model = model

        self._view.set_controller(self)
        self._model.set_callbacks(
            log_cb=self._view.log,
            progress_cb=self._view.update_progress,
            ask_overwrite_cb=self._view.ask_overwrite,
            finish_cb=self._view.on_processing_finished
        )

    def start_translation(self, files, idioma_origem, idioma_destino, manter_legenda):
        """Prepara a interface e dispara o processamento."""
        self._view.prepare_for_processing()
        self._model.start(files, idioma_origem, idioma_destino, manter_legenda)

    def cancel_translation(self):
        """Pede ao orquestrador para interromper a fila de traduções."""
        self._model.stop()

    def on_files_selected(self, files):
        """Varre arquivos MKV de forma assíncrona em busca de idiomas."""
        import threading
        from .manipulador_mkv import ManipuladorMkv

        def _verificar():
            mkvs = [f for f in files if f.lower().endswith('.mkv')]
            if mkvs:
                langs = ManipuladorMkv.listar_idiomas_legendas(mkvs)
                if langs:
                    self._view.update_language_options(langs)

        threading.Thread(target=_verificar, daemon=True).start()


    def on_closing(self):
        """Encerra o processamento e fecha a aplicação."""
        self._model.stop()
        self._view.destroy()
