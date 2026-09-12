import os
import re
import time
import asyncio
import json
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pysubs2
from googletrans import Translator
import winsound

# ─── 1. Configurações e Gerenciamento ─────────────────────────────────────────

class ConfigManager:
    TAMANHO_LOTE = 40
    MAX_CONCORRENTE = 5
    MAX_RETENTATIVAS = 3

    DIRETORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
    LOCAL_MKVTOOLNIX = os.path.join(DIRETORIO_SCRIPT, "mkvtoolnix")
    SYSTEM_MKVTOOLNIX = r"C:\Program Files\MKVToolNix"

    @classmethod
    def get_mkvtoolnix_path(cls):
        if os.path.exists(os.path.join(cls.LOCAL_MKVTOOLNIX, "mkvmerge.exe")):
            return cls.LOCAL_MKVTOOLNIX
        return cls.SYSTEM_MKVTOOLNIX

    @classmethod
    def get_mkv_bins(cls):
        path = cls.get_mkvtoolnix_path()
        return os.path.join(path, "mkvmerge.exe"), os.path.join(path, "mkvextract.exe")

    @classmethod
    def check_dependencies(cls):
        mkvmerge, mkvextract = cls.get_mkv_bins()
        return os.path.exists(mkvmerge) and os.path.exists(mkvextract)


# ─── 2. Wrapper do MKVToolNix ─────────────────────────────────────────────────

class MkvWrapper:
    @staticmethod
    def _detectar_formato(codec, codec_id):
        """Retorna a extensão do formato de legenda ou None se não for suportado."""
        if "ass" in codec or "substation" in codec or "s_text/ass" in codec_id:
            return ".ass"
        elif "srt" in codec or "s_text/utf8" in codec_id:
            return ".srt"
        return None

    @staticmethod
    def extrair_legenda(caminho_mkv, pasta_destino, idioma_preferido, logger):
        mkvmerge, mkvextract = ConfigManager.get_mkv_bins()
        logger("Analisando estrutura do vídeo MKV...")
        
        comando_info = [mkvmerge, "-J", caminho_mkv]
        try:
            # Forçar utf-8 explicitamente no env ou no subprocess para evitar decode errors no Windows
            resultado = subprocess.run(comando_info, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
            info = json.loads(resultado.stdout)
        except Exception as e:
            raise RuntimeError(f"Erro ao ler MKV (Verifique dependências): {e}")

        track_id = None
        fallback_track_id = None
        selected_ext = ".ass"
        fallback_ext = ".ass"

        for track in info.get("tracks", []):
            if track.get("type") == "subtitles":
                codec = track.get("codec", "").lower()
                codec_id = track.get("properties", {}).get("codec_id", "").lower()
                lang = track.get("properties", {}).get("language", "").lower()
                
                ext = MkvWrapper._detectar_formato(codec, codec_id)
                if ext is None:
                    continue
                
                if fallback_track_id is None:
                    fallback_track_id = track["id"]
                    fallback_ext = ext
                    
                if idioma_preferido and lang == idioma_preferido.lower():
                    track_id = track["id"]
                    selected_ext = ext
                    break

        if track_id is None:
            track_id = fallback_track_id
            selected_ext = fallback_ext

        if track_id is None:
            raise ValueError("Nenhuma legenda (.ass ou .srt) encontrada neste MKV.")

        nome_base = os.path.basename(caminho_mkv).rsplit('.', 1)[0]
        caminho_extraido = os.path.join(pasta_destino, f"{nome_base}_ORIGINAL{selected_ext}")

        logger("Extraindo trilha original para processamento...")
        comando_extrair = [mkvextract, "tracks", caminho_mkv, f"{track_id}:{caminho_extraido}"]
        subprocess.run(comando_extrair, check=True, capture_output=True)
        return caminho_extraido

    @staticmethod
    def embutir_legenda(caminho_mkv_original, caminho_legenda_traduzida, pasta_destino, logger):
        mkvmerge, _ = ConfigManager.get_mkv_bins()
        nome_saida = os.path.basename(caminho_mkv_original).rsplit('.', 1)[0] + "_PTBR.mkv"
        caminho_saida = os.path.join(pasta_destino, nome_saida)
        
        logger(f"Criando novo contêiner de vídeo ({nome_saida})...")
        comando_mux = [
            mkvmerge,
            "-o", caminho_saida,
            caminho_mkv_original,
            "--language", "0:por",
            "--track-name", "0:Português (Brasil)",
            caminho_legenda_traduzida
        ]
        
        try:
            subprocess.run(comando_mux, check=True, capture_output=True)
            return caminho_saida
        except Exception as e:
            raise RuntimeError(f"Erro ao embutir a legenda traduzida no MKV final: {e}")


# ─── 3. Serviço de Tradução ───────────────────────────────────────────────────

class TranslatorService:
    def __init__(self, logger, progress_callback):
        self.logger = logger
        self.progress_callback = progress_callback
        self.linhas_processadas = 0
        self.total_linhas = 0

    def _traduzir_sync(self, translator: Translator, texto: str, retries: int = ConfigManager.MAX_RETENTATIVAS) -> str:
        for tentativa in range(retries):
            try:
                return translator.translate(texto, src="auto", dest="pt").text
            except Exception as e:
                if tentativa == retries - 1:
                    raise RuntimeError(f"Falha na API do Google após {retries} tentativas: {e}")
                time.sleep(2 ** tentativa)

    async def _traduzir_lote(self, executor, semaforo, lote_indices, subs, pbar_lock):
        loop = asyncio.get_running_loop()
        translator = Translator()
        
        textos_preparados = []
        for idx in lote_indices:
            texto = subs[idx].text
            # Isolar quebras de linha para evitar aglutinação do Google Translate
            texto = texto.replace(r"\N", " \\N ").replace(r"\n", " \\n ")
            textos_preparados.append(texto)

        bloco = "\n".join(textos_preparados)

        async with semaforo:
            try:
                traduzido = await loop.run_in_executor(executor, self._traduzir_sync, translator, bloco)
                frases = [f.strip() for f in traduzido.split("\n") if f.strip()]

                frases_limpas = []
                for f in frases:
                    f = re.sub(r'\s*\\\s*N\s*', r'\\N', f)
                    f = re.sub(r'\s*\\\s*n\s*', r'\\n', f)
                    frases_limpas.append(f)

                if len(frases_limpas) == len(lote_indices):
                    for i, idx in enumerate(lote_indices):
                        subs[idx].text = frases_limpas[i]
                else:
                    self.logger(f"[Aviso] Dessincronia no lote. Executando fallback sequencial...")
                    for idx, texto in zip(lote_indices, textos_preparados):
                        r = await loop.run_in_executor(executor, self._traduzir_sync, translator, texto)
                        r = re.sub(r'\s*\\\s*N\s*', r'\\N', r)
                        r = re.sub(r'\s*\\\s*n\s*', r'\\n', r)
                        subs[idx].text = r
                        await asyncio.sleep(0.5)
            except Exception as e:
                self.logger(f"[Erro Crítico] Lote ignorado. Motivo: {e}")
                # Mantém o texto original restaurado
                for i, idx in enumerate(lote_indices):
                    restaurado = re.sub(r'\s*\\\s*N\s*', r'\\N', textos_preparados[i])
                    restaurado = re.sub(r'\s*\\\s*n\s*', r'\\n', restaurado)
                    subs[idx].text = restaurado

        with pbar_lock:
            self.linhas_processadas += len(lote_indices)
            self.progress_callback(self.linhas_processadas, self.total_linhas)

    async def pipeline(self, origem: str, destino: str):
        self.logger(f"Carregando legendas de {os.path.basename(origem)}...")
        try:
            subs = pysubs2.load(origem)
        except Exception as e:
            self.logger(f"Erro ao carregar legenda com pysubs2: {e}")
            raise

        indices_map = [i for i, event in enumerate(subs) if event.text.strip()]
        self.total_linhas = len(indices_map)
        self.linhas_processadas = 0
        
        self.logger(f"Total de diálogos encontrados: {self.total_linhas}")
        self.progress_callback(0, self.total_linhas)

        lotes = [indices_map[i : i + ConfigManager.TAMANHO_LOTE] for i in range(0, self.total_linhas, ConfigManager.TAMANHO_LOTE)]
        semaforo = asyncio.Semaphore(ConfigManager.MAX_CONCORRENTE)
        pbar_lock = threading.Lock()

        with ThreadPoolExecutor(max_workers=ConfigManager.MAX_CONCORRENTE) as executor:
            tasks = [self._traduzir_lote(executor, semaforo, lote, subs, pbar_lock) for lote in lotes]
            await asyncio.gather(*tasks)

        self.logger("Salvando arquivo de legendas traduzido...")
        subs.save(destino)


# ─── 4. Interface Gráfica (CustomTkinter) ─────────────────────────────────────

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AppGui(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Tradutor Automático de Legendas (MKV/ASS/SRT)")
        self.geometry("750x550")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.files = []
        self._is_running = False

        self._build_ui()

    def _build_ui(self):
        self.lbl_title = ctk.CTkLabel(self, text="Tradutor de Legendas", font=("Roboto", 24, "bold"))
        self.lbl_title.pack(pady=(20, 10))

        self.btn_select = ctk.CTkButton(self, text="Selecionar Vídeos ou Legendas", command=self.select_files, width=250)
        self.btn_select.pack(pady=10)

        self.lbl_files = ctk.CTkLabel(self, text="Nenhum arquivo selecionado", text_color="gray")
        self.lbl_files.pack(pady=5)

        self.frame_options = ctk.CTkFrame(self)
        self.frame_options.pack(pady=10, padx=20)
        
        self.lbl_lang = ctk.CTkLabel(self.frame_options, text="Idioma Preferido p/ MKV (ex: eng, jpn):")
        self.lbl_lang.pack(side="left", padx=(10, 5), pady=5)
        
        self.entry_lang = ctk.CTkEntry(self.frame_options, width=70)
        self.entry_lang.insert(0, "eng")
        self.entry_lang.pack(side="left", padx=(0, 10), pady=5)
        
        self.var_manter_legenda = ctk.BooleanVar(value=False)
        self.chk_manter_legenda = ctk.CTkCheckBox(self.frame_options, text="Manter legenda externa", variable=self.var_manter_legenda)
        self.chk_manter_legenda.pack(side="left", padx=(10, 0), pady=5)

        self.progressbar = ctk.CTkProgressBar(self, width=600)
        self.progressbar.set(0)
        self.progressbar.pack(pady=10)

        self.textbox = ctk.CTkTextbox(self, width=650, height=250, state="disabled")
        self.textbox.pack(pady=10)

        self.btn_run = ctk.CTkButton(self, text="INICIAR TRADUÇÃO", command=self.start_translation, state="disabled", fg_color="green", hover_color="darkgreen")
        self.btn_run.pack(pady=10)

    def select_files(self):
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
            self.lbl_files.configure(text=f"{len(self.files)} arquivo(s) selecionado(s)", text_color="white")
            self.btn_run.configure(state="normal")

    def log(self, msg):
        def _update(m=msg):
            self.textbox.configure(state="normal")
            self.textbox.insert("end", str(m) + "\n")
            self.textbox.see("end")
            self.textbox.configure(state="disabled")
        self.after(0, _update)

    def update_progress(self, current, total):
        if total > 0:
            self.after(0, lambda c=current, t=total: self.progressbar.set(c / t))

    def start_translation(self):
        self.btn_run.configure(state="disabled")
        self.btn_select.configure(state="disabled")
        self.progressbar.set(0)
        
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        self.textbox.configure(state="disabled")
        
        # Captura valores da UI na main thread antes de delegar para a thread de background
        idioma_preferido = self.entry_lang.get().strip()
        manter_legenda = self.var_manter_legenda.get()
        
        self._is_running = True
        threading.Thread(target=self._orchestrate, args=(idioma_preferido, manter_legenda), daemon=True).start()

    def _orchestrate(self, idioma_preferido, manter_legenda):
        tempo_total_inicio = time.time()
        total_arquivos = len(self.files)
        arquivos_sucesso = 0

        self.log("="*60)
        self.log(f"INICIANDO PROCESSAMENTO EM LOTE: {total_arquivos} arquivo(s)")
        self.log("="*60)

        for index, origem in enumerate(self.files, 1):
            if not self._is_running: break
            
            destino_dir = os.path.dirname(origem)
            eh_mkv = origem.lower().endswith('.mkv')
            
            try:
                inicio_arquivo = time.time()
                self.log(f"\n--- Arquivo [{index}/{total_arquivos}]: {os.path.basename(origem)} ---")
                
                arquivo_trabalho = origem
                if eh_mkv:
                    if not ConfigManager.check_dependencies():
                        self.log("[AVISO] Processamento abortado. MKVToolNix não encontrado.")
                        self.after(0, lambda: messagebox.showwarning("Erro", "O MKVToolNix não foi encontrado."))
                        break
                    
                    self.log(f"[Etapa 1/3] Extração de Mídia via MKVToolNix (Idioma: {idioma_preferido or 'Qualquer'})")
                    arquivo_trabalho = MkvWrapper.extrair_legenda(origem, destino_dir, idioma_preferido, self.log)

                # Definir caminhos
                nome_base = os.path.basename(arquivo_trabalho)
                extensao = nome_base.rsplit('.', 1)[-1]
                nome_sem_ext = nome_base.rsplit('.', 1)[0].replace("_ORIGINAL", "")
                caminho_final_legenda = os.path.join(destino_dir, f"{nome_sem_ext}_PTBR.{extensao}")

                # Tradução
                etapa_trad = "2/3" if eh_mkv else "1/1"
                self.log(f"[Etapa {etapa_trad}] Tradução via Google Translate (Pysubs2)")
                
                translator_svc = TranslatorService(logger=self.log, progress_callback=self.update_progress)
                asyncio.run(translator_svc.pipeline(arquivo_trabalho, caminho_final_legenda))

                # Multiplexação
                if eh_mkv:
                    self.log("[Etapa 3/3] Multiplexação e Limpeza")
                    MkvWrapper.embutir_legenda(origem, caminho_final_legenda, destino_dir, self.log)
                    
                    try:
                        if os.path.exists(arquivo_trabalho) and "_ORIGINAL" in arquivo_trabalho: 
                            os.remove(arquivo_trabalho)
                        
                        if not manter_legenda:
                            if os.path.exists(caminho_final_legenda): 
                                os.remove(caminho_final_legenda)
                            self.log("Lixo temporário de legendas limpo com sucesso.")
                        else:
                            self.log("Legenda traduzida mantida na pasta.")
                    except Exception as lim_e:
                        self.log(f"Aviso: Falha na limpeza: {lim_e}")

                elapsed = int(time.time() - inicio_arquivo)
                self.log(f"-> Sucesso! Tempo gasto: {elapsed}s.")
                arquivos_sucesso += 1

            except Exception as e:
                self.log(f"[ERRO CRÍTICO] Falha no arquivo {os.path.basename(origem)}: {e}")
                continue

        tempo_total_gasto = int(time.time() - tempo_total_inicio)
        self.log("\n" + "="*60)
        self.log("PROCESSAMENTO EM LOTE FINALIZADO")
        self.log(f"Sucesso: {arquivos_sucesso} de {total_arquivos} arquivos.")
        self.log(f"Tempo Total Gasto: {tempo_total_gasto}s")
        self.log("="*60)
        
        self.after(0, lambda: self.btn_run.configure(state="normal"))
        self.after(0, lambda: self.btn_select.configure(state="normal"))
        threading.Thread(target=lambda: winsound.Beep(1000, 500), daemon=True).start()

    def on_closing(self):
        self._is_running = False
        self.destroy()

if __name__ == "__main__":
    app = AppGui()
    app.mainloop()