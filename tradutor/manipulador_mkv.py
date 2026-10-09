import os
import json
import subprocess

from .config import GerenciadorConfig
from .idiomas import Idiomas


class ManipuladorMkv:
    """Encapsula operações de extração e multiplexação de legendas em arquivos MKV."""

    @staticmethod
    def _detectar_formato(codec, codec_id):
        """Retorna a extensão do formato de legenda ou None se não for suportado."""
        # Tabela Data-Driven: Extensão -> Lista de identificadores
        formatos = {
            ".ass": ["ass", "substation", "s_text/ass"],
            ".srt": ["srt", "s_text/utf8"]
        }
        
        texto_busca = f"{codec} {codec_id}".lower()
        for ext, palavras_chave in formatos.items():
            if any(palavra in texto_busca for palavra in palavras_chave):
                return ext
        return None

    @staticmethod
    def listar_idiomas_legendas(caminhos_mkv):
        """Retorna uma lista de idiomas únicos encontrados nos arquivos MKV fornecidos."""
        if not GerenciadorConfig.check_dependencies():
            return []
            
        mkvmerge, _ = GerenciadorConfig.get_mkv_bins()
        idiomas = set()
        
        for mkv in caminhos_mkv:
            try:
                comando = [mkvmerge, "-J", mkv]
                resultado = subprocess.run(
                    comando, capture_output=True, text=True,
                    check=True, encoding='utf-8', errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                info = json.loads(resultado.stdout)
                
                for track in info.get("tracks", []):
                    if track.get("type") == "subtitles":
                        codec = track.get("codec", "").lower()
                        codec_id = track.get("properties", {}).get("codec_id", "").lower()
                        if ManipuladorMkv._detectar_formato(codec, codec_id):
                            lang = track.get("properties", {}).get("language", "und").lower()
                            idiomas.add(lang)
            except Exception:
                continue
                
        return sorted(list(idiomas))


    @staticmethod
    def extrair_legenda(caminho_mkv, pasta_destino, idioma_preferido, logger):
        """Extrai a trilha de legenda preferida de um arquivo MKV.

        Args:
            caminho_mkv: Caminho absoluto do arquivo MKV.
            pasta_destino: Diretório onde salvar a legenda extraída.
            idioma_preferido: Código de idioma (ex: 'eng', 'jpn') ou string vazia.
            logger: Callable para registrar mensagens de progresso.

        Returns:
            Tupla (caminho do arquivo de legenda extraído, idioma real da trilha extraída).
            O idioma real pode diferir do preferido quando ocorre fallback.

        Raises:
            RuntimeError: Se não conseguir ler o MKV.
            ValueError: Se nenhuma legenda suportada for encontrada.
        """
        mkvmerge, mkvextract = GerenciadorConfig.get_mkv_bins()
        logger("Analisando estrutura do vídeo MKV...")

        comando_info = [mkvmerge, "-J", caminho_mkv]
        try:
            resultado = subprocess.run(
                comando_info, capture_output=True, text=True,
                check=True, encoding='utf-8', errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            info = json.loads(resultado.stdout)
        except Exception as e:
            raise RuntimeError(f"Erro ao ler MKV (Verifique dependências): {e}")

        track_id, selected_ext, idioma_real = ManipuladorMkv._selecionar_trilha(info, idioma_preferido)

        if track_id is None:
            raise ValueError("Nenhuma legenda (.ass ou .srt) encontrada neste MKV.")

        pref = (idioma_preferido or "").strip().lower()
        if pref and pref != "auto" and pref != idioma_real:
            logger(f"[AVISO] Idioma '{pref}' ausente neste vídeo; usando a faixa '{idioma_real}'.")

        nome_base = os.path.basename(caminho_mkv).rsplit('.', 1)[0]
        caminho_extraido = os.path.join(pasta_destino, f"{nome_base}_ORIGINAL{selected_ext}")

        logger("Extraindo trilha original para processamento...")
        comando_extrair = [mkvextract, "tracks", caminho_mkv, f"{track_id}:{caminho_extraido}"]
        resultado_extrair = subprocess.run(
            comando_extrair, check=False, capture_output=True, text=True,
            encoding='utf-8', errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        if resultado_extrair.returncode not in (0, 1):
            erro_msg = resultado_extrair.stderr.strip() or f"Código de saída {resultado_extrair.returncode}"
            raise RuntimeError(f"Erro ao extrair trilha do MKV: {erro_msg}")
        return caminho_extraido, idioma_real

    @staticmethod
    def _selecionar_trilha(info, idioma_preferido):
        """Seleciona a melhor trilha de legenda do MKV com base no idioma preferido.

        Returns:
            Tupla (track_id, extensão, idioma). Se nenhuma trilha suportada existir,
            track_id é None.
            O idioma é o da trilha efetivamente selecionada (ou 'und' se não marcado).
        """
        track_id = None
        fallback_track_id = None
        selected_ext = ".ass"
        fallback_ext = ".ass"
        selected_lang = "und"
        fallback_lang = "und"

        for track in info.get("tracks", []):
            if track.get("type") != "subtitles":
                continue

            codec = track.get("codec", "").lower()
            codec_id = track.get("properties", {}).get("codec_id", "").lower()
            lang = track.get("properties", {}).get("language", "und").lower() or "und"

            ext = ManipuladorMkv._detectar_formato(codec, codec_id)
            if ext is None:
                continue

            if fallback_track_id is None:
                fallback_track_id = track["id"]
                fallback_ext = ext
                fallback_lang = lang

            if idioma_preferido and lang == idioma_preferido.lower():
                track_id = track["id"]
                selected_ext = ext
                selected_lang = lang
                break

        if track_id is None:
            return fallback_track_id, fallback_ext, fallback_lang

        return track_id, selected_ext, selected_lang

    @staticmethod
    def embutir_legenda(caminho_mkv_original, caminho_legenda_traduzida, caminho_saida, idioma_destino, logger):
        """Embutir legenda traduzida no MKV original, gerando um novo arquivo.

        Args:
            caminho_mkv_original: MKV de origem.
            caminho_legenda_traduzida: Legenda já traduzida a ser embutida.
            caminho_saida: Caminho completo do MKV de saída.
            idioma_destino: Código do idioma de destino no padrão do Google (ex: 'pt', 'en').
            logger: Callable para registrar mensagens de progresso.

        Returns:
            Caminho do arquivo MKV de saída.

        Raises:
            RuntimeError: Se o mkvmerge falhar.
        """
        mkvmerge, _ = GerenciadorConfig.get_mkv_bins()
        codigo_mkv, nome_trilha = Idiomas.destino_para_mkv(idioma_destino)

        logger(f"Criando novo contêiner de vídeo ({os.path.basename(caminho_saida)})...")
        comando_mux = [
            mkvmerge,
            "-o", caminho_saida,
            caminho_mkv_original,
            "--language", f"0:{codigo_mkv}",
            "--track-name", f"0:{nome_trilha}",
            caminho_legenda_traduzida
        ]

        try:
            resultado_mux = subprocess.run(
                comando_mux, check=False, capture_output=True, text=True,
                encoding='utf-8', errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if resultado_mux.returncode not in (0, 1):
                erro_detalhe = resultado_mux.stderr.strip() or f"Código de saída {resultado_mux.returncode}"
                raise RuntimeError(f"Erro ao embutir a legenda traduzida no MKV final: {erro_detalhe}")
            if resultado_mux.returncode == 1:
                logger("[AVISO] mkvmerge concluiu a multiplexação com alertas (warnings).")
            return caminho_saida
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Erro ao executar mkvmerge: {e}")
