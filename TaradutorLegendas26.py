import re
import os
import time
import asyncio
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog, messagebox
from googletrans import Translator
from tqdm import tqdm
import winsound

# ─── Configurações ────────────────────────────────────────────────────────────
TAMANHO_LOTE     = 40  # Linhas por lote enviado à API
MAX_CONCORRENTE  = 5   # Trabalhadores/Lotes em paralelo ao mesmo tempo
MAX_RETENTATIVAS = 3   # Tentativas antes de considerar falha de rede

# Caminhos padrão do MKVToolNix no Windows
MKVTOOLNIX_PATH  = r"C:\Program Files\MKVToolNix"
MKVMERGE_EXE     = os.path.join(MKVTOOLNIX_PATH, "mkvmerge.exe")
MKVEXTRACT_EXE   = os.path.join(MKVTOOLNIX_PATH, "mkvextract.exe")
# ──────────────────────────────────────────────────────────────────────────────

padrao_dialogo = re.compile(r'(Dialogue:.*,,)(.*)')

def extrair_legenda_mkv(caminho_mkv, pasta_destino):
    """Lê o arquivo MKV usando mkvmerge, identifica a legenda ASS e a extrai."""
    tqdm.write(f"\nAnalisando MKV: {os.path.basename(caminho_mkv)}")
    
    comando_info = [MKVMERGE_EXE, "-J", caminho_mkv]
    try:
        resultado = subprocess.run(comando_info, capture_output=True, text=True, check=True, encoding='utf-8')
        info = json.loads(resultado.stdout)
    except Exception as e:
        raise RuntimeError(f"Erro ao ler MKV (Verifique se o MKVToolNix está instalado em {MKVTOOLNIX_PATH}): {e}")

    track_id = None
    for track in info.get("tracks", []):
        if track.get("type") == "subtitles":
            codec = track.get("codec", "").lower()
            codec_id = track.get("properties", {}).get("codec_id", "").lower()
            
            if "ass" in codec or "substation" in codec or "s_text/ass" in codec_id:
                track_id = track["id"]
                break

    if track_id is None:
        raise ValueError("Nenhuma legenda no formato .ass (SubStation Alpha) foi encontrada neste MKV.")

    nome_ass = os.path.basename(caminho_mkv).rsplit('.', 1)[0] + "_ORIGINAL.ass"
    caminho_ass = os.path.join(pasta_destino, nome_ass)

    tqdm.write(f"Extraindo trilha de legenda {track_id} para: {nome_ass}...")
    comando_extrair = [MKVEXTRACT_EXE, "tracks", caminho_mkv, f"{track_id}:{caminho_ass}"]
    subprocess.run(comando_extrair, check=True, capture_output=True)
    
    return caminho_ass

def embutir_legenda_mkv(caminho_mkv_original, caminho_ass_traduzido, pasta_destino):
    """Mescla o vídeo original com a nova legenda traduzida em um novo arquivo MKV."""
    nome_saida = os.path.basename(caminho_mkv_original).rsplit('.', 1)[0] + "_PTBR.mkv"
    caminho_saida = os.path.join(pasta_destino, nome_saida)
    
    tqdm.write(f"\nCriando novo contêiner MKV com a legenda embutida: {nome_saida}")
    
    comando_mux = [
        MKVMERGE_EXE,
        "-o", caminho_saida,
        caminho_mkv_original,
        "--language", "0:por",
        "--track-name", "0:Português (Brasil)",
        caminho_ass_traduzido
    ]
    
    try:
        subprocess.run(comando_mux, check=True, capture_output=True)
        tqdm.write(f"Novo arquivo de vídeo gerado com sucesso.")
        return caminho_saida
    except Exception as e:
        raise RuntimeError(f"Erro ao embutir a legenda traduzida no MKV final: {e}")

def _traduzir_sync(translator: Translator, texto: str, retries: int = MAX_RETENTATIVAS) -> str:
    """Chamada síncrona à API com Exponential Backoff e Detecção Automática."""
    for tentativa in range(retries):
        try:
            return translator.translate(texto, src="auto", dest="pt").text
        except Exception as e:
            if tentativa == retries - 1:
                raise RuntimeError(f"Falha na API do Google após {retries} tentativas: {e}")
            time.sleep(2 ** tentativa)

async def _traduzir_lote(executor, semaforo, lote_indices, linhas, pbar):
    """Processa blocos de diálogos em paralelo respeitando o semáforo."""
    loop = asyncio.get_running_loop()
    translator = Translator()

    textos = [padrao_dialogo.match(linhas[idx]).group(2).strip() for idx in lote_indices]
    bloco = "\n".join(textos)

    async with semaforo:
        try:
            traduzido = await loop.run_in_executor(
                executor, _traduzir_sync, translator, bloco
            )
            
            frases = [f.strip() for f in traduzido.split("\n") if f.strip()]

            if len(frases) == len(lote_indices):
                pares = [(lote_indices[j], frases[j]) for j in range(len(lote_indices))]
            else:
                tqdm.write(f"[Aviso] Dessincronia no lote (esperado {len(lote_indices)}, recebido {len(frases)}). Executando fallback sequencial...")
                pares = []
                for idx, texto in zip(lote_indices, textos):
                    r = await loop.run_in_executor(executor, _traduzir_sync, translator, texto)
                    pares.append((idx, r))
                    await asyncio.sleep(0.5)

        except Exception as e:
            tqdm.write(f"\n[Erro Crítico] Lote ignorado. Motivo: {e}")
            pares = [(idx, textos[i]) for i, idx in enumerate(lote_indices)]

    pbar.update(len(lote_indices))
    return pares

async def _pipeline(origem: str) -> list[str]:
    """Gerencia a leitura do arquivo de trabalho, divisão em lotes e coleta de resultados."""
    with open(origem, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    indices_map = [
        i for i, l in enumerate(linhas)
        if padrao_dialogo.match(l) and padrao_dialogo.match(l).group(2).strip()
    ]
    total = len(indices_map)
    print(f"\nTotal de diálogos encontrados: {total}")
    print(f"Estratégia: Lotes de {TAMANHO_LOTE} | {MAX_CONCORRENTE} threads | Máx {MAX_RETENTATIVAS} retries\n")

    lotes = [indices_map[i : i + TAMANHO_LOTE] for i in range(0, total, TAMANHO_LOTE)]
    semaforo = asyncio.Semaphore(MAX_CONCORRENTE)

    with ThreadPoolExecutor(max_workers=MAX_CONCORRENTE) as executor:
        with tqdm(total=total, desc="Traduzindo", unit="linha", colour="green",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} linhas [{elapsed}<{remaining}]") as pbar:

            tasks = [_traduzir_lote(executor, semaforo, lote, linhas, pbar) for lote in lotes]
            resultados = await asyncio.gather(*tasks)

    for pares in resultados:
        for idx, texto_pt in pares:
            prefixo = padrao_dialogo.match(linhas[idx]).group(1)
            linhas[idx] = f"{prefixo}{texto_pt.strip()}\n"

    return linhas

def traduzir_legenda():
    """Interface gráfica e orquestração do fluxo do programa."""
    root = tk.Tk()
    root.withdraw()

    origem = filedialog.askopenfilename(
        title="Selecione o vídeo MKV ou arquivo de legenda",
        filetypes=[
            ("Todos os formatos suportados", "*.mkv;*.ass;*.txt"),
            ("Vídeo MKV", "*.mkv"),
            ("Legenda ASS", "*.ass"),
            ("Texto Plano", "*.txt")
        ]
    )
    if not origem: return

    destino = filedialog.askdirectory(title="Escolha a pasta onde salvar")
    if not destino: return

    try:
        inicio = time.time()
        eh_mkv = origem.lower().endswith('.mkv')
        
        if eh_mkv:
            arquivo_trabalho = extrair_legenda_mkv(origem, destino)
        else:
            arquivo_trabalho = origem

        caminho_final_ass = os.path.join(
            destino,
            os.path.basename(arquivo_trabalho).replace(".ass", "_FIXED_PTBR.ass").replace(".txt", "_FIXED_PTBR.txt").replace("_ORIGINAL", "")
        )

        linhas_traduzidas = asyncio.run(_pipeline(arquivo_trabalho))

        with open(caminho_final_ass, "w", encoding="utf-8") as f_out:
            f_out.writelines(linhas_traduzidas)

        if eh_mkv:
            caminho_video_final = embutir_legenda_mkv(origem, caminho_final_ass, destino)
            mensagem_final = f"Processo concluído com sucesso!\n\nVídeo gerado: {caminho_video_final}\nLegenda gerada: {caminho_final_ass}"
        else:
            mensagem_final = f"Tradução da legenda concluída!\n\nSalvo em: {caminho_final_ass}"

        elapsed = int(time.time() - inicio)
        print(f"\nProcesso completo finalizado em {elapsed}s")
        winsound.Beep(1000, 500)
        messagebox.showinfo("Sucesso", f"{mensagem_final}\n\nTempo total: {elapsed}s")

    except Exception as e:
        messagebox.showerror("Erro Crítico", str(e))
        raise

if __name__ == "__main__":
    traduzir_legenda()