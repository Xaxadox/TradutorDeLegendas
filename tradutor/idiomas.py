class Idiomas:
    """Mapeamento centralizado de códigos de idioma.

    Converte os códigos ISO-639-2 do MKV (ex: 'jpn') para os códigos do
    Google Translate (ex: 'ja') e os códigos de destino do Google de volta
    para os metadados exigidos pelo mkvmerge.
    """

    _MKV_PARA_GOOGLE = {
        "eng": "en", "fra": "fr", "fre": "fr", "jpn": "ja", "spa": "es",
        "ger": "de", "deu": "de", "ita": "it", "por": "pt", "rus": "ru",
        "chi": "zh-cn", "zho": "zh-cn", "kor": "ko", "ara": "ar", "tha": "th",
        "pol": "pl", "nld": "nl", "dut": "nl", "tur": "tr", "ces": "cs",
        "cze": "cs", "swe": "sv", "hin": "hi", "vie": "vi", "ind": "id",
        "ukr": "uk", "ell": "el", "gre": "el", "hun": "hu", "ron": "ro",
        "rum": "ro", "dan": "da", "fin": "fi", "nor": "no", "bul": "bg",
    }

    # Códigos que significam "idioma desconhecido" e devem usar a autodetecção.
    _INDEFINIDOS = {"auto", "und", "mis", "mul", "zxx"}

    # Destino (código Google) -> (código ISO-639-2 do mkvmerge, nome da trilha).
    _DESTINO_PARA_MKV = {
        "pt": ("por", "Português (Brasil)"),
        "en": ("eng", "English"),
        "es": ("spa", "Español"),
        "fr": ("fra", "Français"),
        "de": ("ger", "Deutsch"),
        "it": ("ita", "Italiano"),
        "ru": ("rus", "Русский"),
        "ja": ("jpn", "日本語"),
        "ko": ("kor", "한국어"),
        "zh-cn": ("chi", "中文 (简体)"),
    }

    @staticmethod
    def para_google(codigo):
        """Converte um código de idioma (MKV ou Google) para o código do Google Translate.

        Retorna 'auto' quando o idioma é desconhecido ou não mapeado.
        """
        if not codigo:
            return "auto"
        codigo = codigo.strip().lower()
        if codigo in Idiomas._INDEFINIDOS:
            return "auto"
        if codigo in Idiomas._MKV_PARA_GOOGLE.values():
            return codigo
        return Idiomas._MKV_PARA_GOOGLE.get(codigo, "auto")

    @staticmethod
    def destino_para_mkv(codigo_google):
        """Retorna (código ISO-639-2, nome da trilha) para embutir a legenda no MKV."""
        codigo = (codigo_google or "").strip().lower()
        return Idiomas._DESTINO_PARA_MKV.get(codigo, (codigo or "und", codigo.upper() or "Legenda"))
