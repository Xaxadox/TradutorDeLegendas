import os
import subprocess
import sys

def preparar_video():
    diretorio_teste = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho_video = os.path.join(diretorio_teste, "data", "VideoForTest.mkv")
    
    if not os.path.exists(caminho_video):
        print(f"[ERRO] O vídeo '{caminho_video}' não foi encontrado.")
        return
        
    print("="*50)
    print(" ADICIONANDO MAIS IDIOMAS AO VÍDEO DE TESTE ")
    print("="*50)

    # Dicionário com código ISO e algumas falas simples
    novas_legendas = {
        "eng": ["This is a test subtitle.", "I hope it works!"],
        "spa": ["Este es un subtítulo de prueba.", "¡Espero que funcione!"],
        "ger": ["Dies ist ein Testuntertitel.", "Ich hoffe, es funktioniert!"],
        "rus": ["Это тестовый субтитр.", "Надеюсь, это сработает!"],
        "chi": ["这是一个测试字幕。", "希望它能起作用！"]
    }
    
    arquivos_srt = []
    comando_mkvmerge_args = []
    
    # 1. Gerar legendas temporárias
    for lang, frases in novas_legendas.items():
        srt_path = os.path.join(diretorio_teste, "data", f"temp_{lang}.srt")
        arquivos_srt.append(srt_path)
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(f"1\n00:00:01,000 --> 00:00:04,000\n{frases[0]}\n\n")
            f.write(f"2\n00:00:05,000 --> 00:00:08,000\n{frases[1]}\n\n")
            
        comando_mkvmerge_args.extend([
            "--language", f"0:{lang}",
            "--track-name", f"0:Teste {lang.upper()}",
            srt_path
        ])
        print(f"[INFO] Legenda temporária criada para: {lang}")
    
    # 2. Muxar as legendas no vídeo
    saida_video = os.path.join(diretorio_teste, "data", "VideoForTest_multi.mkv")
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from tradutor.config import GerenciadorConfig
    mkvmerge, _ = GerenciadorConfig.get_mkv_bins()

    comando = [mkvmerge, "-o", saida_video, caminho_video] + comando_mkvmerge_args
    
    print(f"\n[INFO] Rodando mkvmerge para embutir todas as {len(novas_legendas)} novas legendas...")
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=False)
        if resultado.returncode in [0, 1]:
            print("[SUCESSO] Legendas embutidas com sucesso no vídeo.")
            
            # Substituir o arquivo original
            os.remove(caminho_video)
            os.rename(saida_video, caminho_video)
            print(f"[SUCESSO] O arquivo 'VideoForTest.mkv' agora possui mais faixas ({', '.join(novas_legendas.keys())}).")
        else:
            print("[ERRO] Falha ao rodar mkvmerge:")
            print(resultado.stderr)
            print(resultado.stdout)
    except FileNotFoundError:
        print("[ERRO] mkvmerge não encontrado no sistema.")
    finally:
        # Limpeza
        for srt_path in arquivos_srt:
            if os.path.exists(srt_path):
                os.remove(srt_path)
        if os.path.exists(saida_video):
            os.remove(saida_video)

if __name__ == "__main__":
    preparar_video()
