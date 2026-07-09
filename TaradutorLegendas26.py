
import re
import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog, messagebox
from googletrans import Translator
from tqdm import tqdm
import winsound

# ─── Configurações ────────────────────────────────────────────────────────────
TAMANHO_LOTE    = 40  # Linhas por lote enviado à API
MAX_CONCORRENTE = 5   # Trabalhadores em paralelo
MAX_RETENTATIVAS = 3  # Tentativas antes de considerar falha de rede
# ──────────────────────────────────────────────────────────────────────────────

padrao_dialogo = re.compile(r'(Dialogue:.*,,)(.*)')

def _traduzir_sync(translator: Translator, texto: str, retries: int = MAX_RETENTATIVAS) -> str:
    """
    Chamada síncrona com Exponential Backoff.
    Evita que instabilidades de rede ou bloqueios rápidos quebrem o script.
    """
    for tentativa in range(retries):
        try:
            return translator.translate(texto, src="en", dest="pt").text
        except Exception as e:
            if tentativa == retries - 1:
                raise RuntimeError(f"Falha na API do Google após {retries} tentativas: {e}")
            time.sleep(2 ** tentativa)  # Espera 1s, 2s, 4s... antes de tentar de novo

async def _traduzir_lote(executor, semaforo, lote_indices, linhas, pbar):
    """
    Processa um lote de legendas. Se houver dessincronização, realiza um
    fallback sequencial para não estourar o Rate Limit do Google.
    """
    loop = asyncio.get_running_loop()
    translator = Translator()

    textos = [padrao_dialogo.match(linhas[idx]).group(2).strip() for idx in lote_indices]
    bloco = "\n".join(textos)

    async with semaforo:
        try:
            traduzido = await loop.run_in_executor(
                executor, _traduzir_sync, translator, bloco
            )
            
            # Limpeza de quebras de linha fantasmas geradas pela API
            frases = [f.strip() for f in traduzido.split("\n") if f.strip()]

            # Caminho Feliz: Lote sincronizado
            if len(frases) == len(lote_indices):
                pares = [(lote_indices[j], frases[j]) for j in range(len(lote_indices))]
            
            # Caminho Alternativo: Dessincronizou (Google aglutinou frases ou removeu \n)
            else:
                tqdm.write(f"[Aviso] Dessincronia no lote (esperado {len(lote_indices)}, recebido {len(frases)}). Executando fallback sequencial...")
                pares = []
                # Fallback SEQUENCIAL: Evita banimento de IP disparando N requisições de uma vez
                for idx, texto in zip(lote_indices, textos):
                    r = await loop.run_in_executor(executor, _traduzir_sync, translator, texto)
                    pares.append((idx, r))
                    await asyncio.sleep(0.5) # Delay tático no fallback para "esfriar" a API

        except Exception as e:
            tqdm.write(f"\n[Erro Crítico] Lote ignorado. Motivo: {e}")
            pares = [(idx, textos[i]) for i, idx in enumerate(lote_indices)] # Mantém original em caso de falha absoluta

    pbar.update(len(lote_indices))
    return pares

async def _pipeline(origem: str) -> list[str]:
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

    # Reescrita in-memory das linhas
    for pares in resultados:
        for idx, texto_pt in pares:
            prefixo = padrao_dialogo.match(linhas[idx]).group(1)
            linhas[idx] = f"{prefixo}{texto_pt.strip()}\n"

    return linhas

def traduzir_legenda():
    root = tk.Tk()
    root.withdraw()

    origem = filedialog.askopenfilename(
        title="Selecione a legenda original",
        filetypes=[("Legendas", "*.ass *.txt")]
    )
    if not origem: return

    destino = filedialog.askdirectory(title="Escolha a pasta de destino")
    if not destino: return

    caminho_final = os.path.join(
        destino,
        os.path.basename(origem).replace(".ass", "_FIXED_PTBR.ass")
    )

    try:
        inicio = time.time()
        linhas_traduzidas = asyncio.run(_pipeline(origem))

        with open(caminho_final, "w", encoding="utf-8") as f_out:
            f_out.writelines(linhas_traduzidas)

        elapsed = int(time.time() - inicio)
        print(f"\nSalvo em: {caminho_final}")
        print(f"Concluído em {elapsed}s")
        winsound.Beep(1000, 500)
        messagebox.showinfo("Sucesso", f"Legenda traduzida em {elapsed}s!\n\nSalvo em: {caminho_final}")

    except Exception as e:
        messagebox.showerror("Erro Crítico", str(e))
        raise

if __name__ == "__main__":
    traduzir_legenda()