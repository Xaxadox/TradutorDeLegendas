import re
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import pysubs2
from googletrans import Translator

from .config import ConfigManager


class TranslatorService:
    """Serviço de tradução assíncrona de legendas via Google Translate.

    Processa legendas em lotes concorrentes, com fallback sequencial
    quando a API retorna quantidade inconsistente de linhas.
    """

    def __init__(self, logger, progress_callback):
        self._logger = logger
        self._progress_callback = progress_callback
        self._linhas_processadas = 0
        self._total_linhas = 0

    def _traduzir_sync(self, translator, texto, src_lang="auto", retries=ConfigManager.MAX_RETENTATIVAS):
        """Traduz um bloco de texto de forma síncrona, com retentativas exponenciais."""
        for tentativa in range(retries):
            try:
                return translator.translate(texto, src=src_lang, dest="pt").text
            except (TypeError, ValueError, AttributeError) as e:
                # Erros estruturais ou de parsing do googletrans costumam ser permanentes
                # (ex: IP bloqueado retornando HTML em vez de JSON ou dados inválidos)
                raise RuntimeError(f"Erro permanente detectado. Tradução abortada para este lote: {e}")
            except Exception as e:
                # Erros transientes (Timeout, ConnectionError, etc.)
                if tentativa == retries - 1:
                    raise RuntimeError(f"Falha na API do Google após {retries} tentativas: {e}")
                time.sleep(2 ** tentativa)

    @staticmethod
    def _limpar_quebras(texto):
        """Restaura marcadores de quebra de linha \\N e \\n removendo espaços injetados."""
        texto = re.sub(r'\s*\\\s*N\s*', r'\\N', texto)
        texto = re.sub(r'\s*\\\s*n\s*', r'\\n', texto)
        return texto

    @staticmethod
    def _map_lang(iso_639_2):
        """Mapeia os códigos de idioma do MKV para o Google Translate."""
        if not iso_639_2 or iso_639_2 == "auto" or iso_639_2 == "und":
            return "auto"
        # Mapeamento dos mais comuns de 3 letras para 2 letras
        mapa = {
            "eng": "en", "fra": "fr", "fre": "fr", "jpn": "ja", 
            "spa": "es", "ger": "de", "ita": "it", "por": "pt",
            "rus": "ru", "chi": "zh-cn"
        }
        return mapa.get(iso_639_2.lower(), "auto")

    async def _traduzir_lote(self, executor, semaforo, lote_indices, subs, pbar_lock, src_lang="auto"):
        """Traduz um lote de linhas de legenda de forma assíncrona."""
        loop = asyncio.get_running_loop()
        translator = Translator()

        textos_preparados = []
        for idx in lote_indices:
            texto = subs[idx].text
            texto = texto.replace(r"\N", " \\N ").replace(r"\n", " \\n ")
            textos_preparados.append(texto)

        bloco = "\n".join(textos_preparados)

        async with semaforo:
            try:
                traduzido = await loop.run_in_executor(executor, self._traduzir_sync, translator, bloco, src_lang)
                frases = [f.strip() for f in traduzido.split("\n") if f.strip()]
                frases_limpas = [self._limpar_quebras(f) for f in frases]

                if len(frases_limpas) == len(lote_indices):
                    for i, idx in enumerate(lote_indices):
                        subs[idx].text = frases_limpas[i]
                else:
                    self._logger("[Aviso] Dessincronia no lote. Executando fallback sequencial...")
                    for idx, texto in zip(lote_indices, textos_preparados):
                        r = await loop.run_in_executor(executor, self._traduzir_sync, translator, texto, src_lang)
                        subs[idx].text = self._limpar_quebras(r)
                        await asyncio.sleep(0.5)
            except Exception as e:
                self._logger(f"[Erro Crítico] Lote ignorado. Motivo: {e}")
                for i, idx in enumerate(lote_indices):
                    subs[idx].text = self._limpar_quebras(textos_preparados[i])

        with pbar_lock:
            self._linhas_processadas += len(lote_indices)
            self._progress_callback(self._linhas_processadas, self._total_linhas)

    async def pipeline(self, origem, destino, idioma_preferido="auto"):
        """Pipeline completo: carrega legenda, traduz todos os lotes e salva.

        Args:
            origem: Caminho do arquivo de legenda original.
            destino: Caminho do arquivo de legenda traduzida.
            idioma_preferido: Idioma de origem (ex: 'eng', 'fra').
        """
        src_lang = self._map_lang(idioma_preferido)
        
        self._logger(f"Carregando legendas de {__import__('os').path.basename(origem)}...")
        try:
            subs = pysubs2.load(origem)
        except Exception as e:
            self._logger(f"Erro ao carregar legenda com pysubs2: {e}")
            raise

        indices_map = [i for i, event in enumerate(subs) if event.text.strip()]
        self._total_linhas = len(indices_map)
        self._linhas_processadas = 0

        self._logger(f"Total de diálogos encontrados: {self._total_linhas}")
        self._progress_callback(0, self._total_linhas)

        lotes = [
            indices_map[i : i + ConfigManager.TAMANHO_LOTE]
            for i in range(0, self._total_linhas, ConfigManager.TAMANHO_LOTE)
        ]
        semaforo = asyncio.Semaphore(ConfigManager.MAX_CONCORRENTE)
        pbar_lock = threading.Lock()

        with ThreadPoolExecutor(max_workers=ConfigManager.MAX_CONCORRENTE) as executor:
            tasks = [self._traduzir_lote(executor, semaforo, lote, subs, pbar_lock, src_lang) for lote in lotes]
            await asyncio.gather(*tasks)

        self._logger("Salvando arquivo de legendas traduzido...")
        subs.save(destino)
