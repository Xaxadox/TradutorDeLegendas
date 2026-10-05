import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk

try:
    import winsound
except ImportError:
    winsound = None


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class AppGui(ctk.CTk):
    """View layer: Interface gráfica pura.

    Responsável exclusivamente por renderizar widgets, capturar
    inputs do usuário e exibir feedback. Toda lógica de negócio
    é delegada ao Controller.
    """

    def __init__(self):
        super().__init__()
        self.title("Tradutor Automático de Legendas (MKV/ASS/SRT)")
        self.geometry("750x550")

        self._controller = None
        self.files = []

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_closing_request)

    def set_controller(self, controller):
        """Injeta o controller após construção."""
        self._controller = controller

    # ── Construção de Widgets ──────────────────────────────────────────────

    def _build_ui(self):
        self.lbl_title = ctk.CTkLabel(
            self, text="Tradutor de Legendas", font=("Roboto", 24, "bold")
        )
        self.lbl_title.pack(pady=(20, 10))

        self.btn_select = ctk.CTkButton(
            self, text="Selecionar Vídeos ou Legendas",
            command=self._select_files, width=250
        )
        self.btn_select.pack(pady=10)

        self.lbl_files = ctk.CTkLabel(
            self, text="Nenhum arquivo selecionado", text_color="gray"
        )
        self.lbl_files.pack(pady=5)

        self._build_options_frame()

        self.progressbar = ctk.CTkProgressBar(self, width=600)
        self.progressbar.set(0)
        self.progressbar.pack(pady=10)

        self.textbox = ctk.CTkTextbox(self, width=650, height=250, state="disabled")
        self.textbox.pack(pady=10)

        self._build_action_buttons()

    def _build_options_frame(self):
        self.frame_options = ctk.CTkFrame(self)
        self.frame_options.pack(pady=10, padx=20)

        ctk.CTkLabel(
            self.frame_options, text="Idioma Preferido p/ MKV (ex: eng, jpn):"
        ).pack(side="left", padx=(10, 5), pady=5)

        self.combo_lang = ctk.CTkOptionMenu(self.frame_options, values=["auto"], width=100)
        self.combo_lang.pack(side="left", padx=(0, 10), pady=5)

        self.var_manter_legenda = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.frame_options, text="Manter legenda externa",
            variable=self.var_manter_legenda
        ).pack(side="left", padx=(10, 0), pady=5)

    def _build_action_buttons(self):
        self.frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botoes.pack(pady=10)

        self.btn_run = ctk.CTkButton(
            self.frame_botoes, text="INICIAR TRADUÇÃO",
            command=self._on_start_clicked, state="disabled",
            fg_color="green", hover_color="darkgreen", width=250
        )
        self.btn_run.pack()

        self.btn_novos = ctk.CTkButton(
            self.frame_botoes, text="🔄 Traduzir Outros Arquivos",
            command=self._voltar_para_selecao,
            fg_color="#2980b9", hover_color="#1f6da0", width=220
        )
        self.btn_encerrar = ctk.CTkButton(
            self.frame_botoes, text="✖ Encerrar Aplicativo",
            command=self._on_closing_request,
            fg_color="#c0392b", hover_color="#96281b", width=220
        )

    # ── Ações do Usuário ──────────────────────────────────────────────────

    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="Selecione os vídeos MKV ou arquivos de legenda",
            filetypes=[
                ("Todos Suportados", "*.mkv *.ass *.srt *.txt"),
                ("Vídeo MKV", "*.mkv"),
                ("Legenda", "*.ass *.srt *.txt")
            ]
        )
        if files:
            self.files = files
            self.lbl_files.configure(
                text=f"{len(self.files)} arquivo(s) selecionado(s)", text_color="white"
            )
            self.btn_run.configure(state="normal")
            if self._controller:
                self._controller.on_files_selected(self.files)

    def _on_start_clicked(self):
        if self._controller:
            idioma = self.combo_lang.get().strip()
            manter = self.var_manter_legenda.get()
            self._controller.start_translation(self.files, idioma, manter)

    def _on_closing_request(self):
        if self._controller:
            self._controller.on_closing()
        else:
            self.destroy()

    # ── Métodos Públicos (chamados pelo Controller/Model via callbacks) ────

    def prepare_for_processing(self):
        """Prepara a UI para o início do processamento."""
        self.btn_run.configure(state="disabled")
        self.btn_select.configure(state="disabled")
        self.progressbar.set(0)
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        self.textbox.configure(state="disabled")

    def update_language_options(self, langs):
        """Atualiza a lista de idiomas após varredura dos MKVs."""
        def _update():
            opcoes = ["auto"] + langs
            self.combo_lang.configure(values=opcoes)
            if len(langs) == 1:
                self.combo_lang.set(langs[0])
            else:
                self.combo_lang.set("auto")
        self.after(0, _update)

    def log(self, msg):
        """Adiciona uma mensagem ao log da interface (thread-safe)."""
        def _update():
            self.textbox.configure(state="normal")
            self.textbox.insert("end", str(msg) + "\n")
            self.textbox.see("end")
            self.textbox.configure(state="disabled")
        self.after(0, _update)

    def update_progress(self, current, total):
        """Atualiza a barra de progresso (thread-safe)."""
        if total > 0:
            self.after(0, lambda: self.progressbar.set(current / total))

    def ask_overwrite(self, nomes_arquivos):
        """Pergunta ao usuário se deseja sobrescrever arquivos existentes (thread-safe)."""
        evento = threading.Event()
        resposta = [False]

        def _ask():
            r = messagebox.askyesno(
                "Arquivo já existe",
                f"O(s) arquivo(s) abaixo já existe(m):\n\n{nomes_arquivos}\n\nDeseja sobrescrever?"
            )
            resposta[0] = r
            evento.set()

        self.after(0, _ask)
        evento.wait()
        return resposta[0]

    def on_processing_finished(self):
        """Atualiza a UI após o término do processamento."""
        def _update_ui():
            self.btn_run.pack_forget()
            self.btn_novos.pack(side="left", padx=10)
            self.btn_encerrar.pack(side="left", padx=10)
            self.btn_select.configure(state="normal")
            self.files = []
            self.lbl_files.configure(
                text="✅ Concluído! Escolha uma opção abaixo.", text_color="#2ecc71"
            )
            if winsound:
                try:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except Exception:
                    pass
        self.after(0, _update_ui)

    def _voltar_para_selecao(self):
        """Reseta a interface para o estado inicial e abre o seletor de arquivos."""
        self.btn_novos.pack_forget()
        self.btn_encerrar.pack_forget()
        self.btn_run.pack()
        self.btn_run.configure(state="disabled")
        self.lbl_files.configure(text="Nenhum arquivo selecionado", text_color="gray")
        self.progressbar.set(0)
        self.combo_lang.configure(values=["auto"])
        self.combo_lang.set("auto")
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        self.textbox.configure(state="disabled")
        self._select_files()
