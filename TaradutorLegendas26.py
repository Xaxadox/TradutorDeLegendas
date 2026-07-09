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
    tqdm.write(f"Analisando estrutura do vídeo MKV...")
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

    tqdm.write(f"Extraindo trilha original para processamento...")
    comando_extrair = [MKVEXTRACT_EXE, "tracks", caminho_mkv, f"{track_id}:{caminho_ass}"]
    subprocess.run(comando_extrair, check=True, capture_output=True)
    return caminho_ass

def embutir_legenda_mkv(caminho_mkv_original, caminho_ass_traduzido, pasta_destino):
    nome_saida = os.path.basename(caminho_mkv_original).rsplit('.', 1)[0] + "_PTBR.mkv"
    caminho_saida = os.path.join(pasta_destino, nome_saida)
    
    tqdm.write(f"Criando novo contêiner de vídeo ({nome_saida})...")
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
        return caminho_saida
    except Exception as e:
        raise RuntimeError(f"Erro ao embutir a legenda traduzida no MKV final: {e}")

def _traduzir_sync(translator: Translator, texto: str, retries: int = MAX_RETENTATIVAS) -> str:
    for tentativa in range(retries):
        try:
            return translator.translate(texto, src="auto", dest="pt").text
        except Exception as e:
            if tentativa == retries - 1:
                raise RuntimeError(f"Falha na API do Google após {retries} tentativas: {e}")
            time.sleep(2 ** tentativa)

async def _traduzir_lote(executor, semaforo, lote_indices, linhas, pbar):
    loop = asyncio.get_running_loop()
    translator = Translator()
    textos = [padrao_dialogo.match(linhas[idx]).group(2).strip() for idx in lote_indices]
    bloco = "\n".join(textos)

    async with semaforo:
        try:
            traduzido = await loop.run_in_executor(executor, _traduzir_sync, translator, bloco)
            frases = [f.strip() for f in traduzido.split("\n") if f.strip()]

            if len(frases) == len(lote_indices):
                pares = [(lote_indices[j], frases[j]) for j in range(len(lote_indices))]
            else:
                tqdm.write(f"\n[Aviso] Dessincronia no lote (esperado {len(lote_indices)}, recebido {len(frases)}). Executando fallback sequencial...")
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
    with open(origem, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    indices_map = [i for i, l in enumerate(linhas) if padrao_dialogo.match(l) and padrao_dialogo.match(l).group(2).strip()]
    total = len(indices_map)
    print(f"Total de diálogos encontrados: {total}")
    print(f"Processamento paralelo iniciado...\n")

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
    root = tk.Tk()
    root.withdraw()

    origens = filedialog.askopenfilenames(
        title="Selecione os vídeos MKV ou arquivos de legenda",
        filetypes=[
            ("Mídia e Legendas", "*.mkv *.ass *.txt"),
            ("Vídeo MKV", "*.mkv"),
            ("Legenda ASS", "*.ass"),
            ("Texto Plano", "*.txt")
        ]
    )
    if not origens: return

    tempo_total_inicio = time.time()
    total_arquivos = len(origens)
    arquivos_sucesso = 0

    print("\n" + "="*60)
    print(f"INICIANDO PROCESSAMENTO EM LOTE: {total_arquivos} arquivo(s)")
    print("="*60)

    for index, origem in enumerate(origens, 1):
        destino = os.path.dirname(origem)
        eh_mkv = origem.lower().endswith('.mkv')
        
        try:
            inicio_arquivo = time.time()
            
            print(f"\n--- Arquivo [{index}/{total_arquivos}]: {os.path.basename(origem)} ---")
            
            if eh_mkv:
                print("[Etapa 1/3] Extração de Mídia")
                arquivo_trabalho = extrair_legenda_mkv(origem, destino)
            else:
                arquivo_trabalho = origem

            caminho_final_ass = os.path.join(
                destino,
                os.path.basename(arquivo_trabalho).replace(".ass", "_PTBR.ass").replace(".txt", "_PTBR.txt").replace("_ORIGINAL", "")
            )

            etapa_traducao = "2/3" if eh_mkv else "1/1"
            print(f"\n[Etapa {etapa_traducao}] Tradução via Google Translate API")
            linhas_traduzidas = asyncio.run(_pipeline(arquivo_trabalho))

            with open(caminho_final_ass, "w", encoding="utf-8") as f_out:
                f_out.writelines(linhas_traduzidas)

            if eh_mkv:
                print("\n[Etapa 3/3] Multiplexação e Limpeza")
                embutir_legenda_mkv(origem, caminho_final_ass, destino)
                
                try:
                    if os.path.exists(arquivo_trabalho): os.remove(arquivo_trabalho)
                    if os.path.exists(caminho_final_ass): os.remove(caminho_final_ass)
                    print("Lixo temporário (.ass) limpo com sucesso.")
                except Exception as lim_e:
                    print(f"Aviso: Falha na limpeza de arquivos temporários: {lim_e}")

            elapsed = int(time.time() - inicio_arquivo)
            print(f"-> Arquivo concluído com sucesso em {elapsed}s.")
            arquivos_sucesso += 1

        except Exception as e:
            print(f"\n[ERRO CRÍTICO] Falha no arquivo {os.path.basename(origem)}: {e}")
            print("Pulando para o próximo arquivo da fila...")
            continue # Impede que o erro em um arquivo derrube todo o processamento

    tempo_total_gasto = int(time.time() - tempo_total_inicio)
    
    print("\n" + "="*60)
    print(f"PROCESSAMENTO EM LOTE FINALIZADO")
    print(f"Sucesso: {arquivos_sucesso} de {total_arquivos} arquivos.")
    print(f"Tempo Total Gasto: {tempo_total_gasto}s")
    print("="*60)
    
    winsound.Beep(1000, 500)
    messagebox.showinfo("Operação Concluída", f"Lote finalizado!\n\nSucesso: {arquivos_sucesso}/{total_arquivos}\nTempo total: {tempo_total_gasto} segundos.")

if __name__ == "__main__":
    traduzir_legenda()