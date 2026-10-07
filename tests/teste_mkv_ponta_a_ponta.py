import os
import sys
import time

# Adicionar raiz do projeto ao path para conseguir importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradutor.orchestrator import TranslationOrchestrator

def rodar_teste_mkv(caminho_mkv, idioma_origem_menu="auto", idioma_destino="pt"):
    """
    Testa o fluxo completo para um arquivo MKV.
    Valida extração, delegação de idioma, tradução e multiplexação.
    """
    if not os.path.exists(caminho_mkv):
        print(f"[ERRO] Arquivo não encontrado: {caminho_mkv}")
        print("Por favor, coloque um arquivo de vídeo (ex: video_teste.mkv) neste caminho para rodar o teste.")
        return

    print("="*60)
    print(f" INICIANDO TESTE E2E PARA MKV: {os.path.basename(caminho_mkv)}")
    print("="*60)
    
    model = TranslationOrchestrator()
    
    # Mockando a interface gráfica para ver os logs no console
    def mock_log(msg):
        print(f"[LOG] {msg}")
        
    def mock_progress(current, total):
        print(f"[PROGRES] {current}/{total}", end='\r')
        
    def mock_overwrite(nomes):
        print(f"\n[OVERWRITE] Conflito detectado para: {nomes}")
        # Retorna True simulando que o usuário aceitou sobrescrever
        return True 
        
    def mock_finish():
        print("\n[SUCESSO] Pipeline do Orquestrador Concluído.")
        model.stop()
        
    model.set_callbacks(
        log_cb=mock_log,
        progress_cb=mock_progress,
        ask_overwrite_cb=mock_overwrite,
        finish_cb=mock_finish
    )
    
    print(f"\n=> Enviando para o Orquestrador (Menu Src: {idioma_origem_menu} | Destino: {idioma_destino})\n")
    
    # Iniciando processamento
    model._is_running = True
    model.start([caminho_mkv], idioma_origem=idioma_origem_menu, idioma_destino=idioma_destino, manter_legenda=True)
    
    while model._is_running:
        time.sleep(1)
        
    # Validando o arquivo de saída
    nome_base = os.path.splitext(caminho_mkv)[0]
    saida_esperada = f"{nome_base}_{idioma_destino.upper()}.mkv"
    
    print("\n" + "="*60)
    print(" RESULTADO DO TESTE")
    print("="*60)
    
    if os.path.exists(saida_esperada):
        print(f"[PASS] Arquivo final gerado com o nome correto: {os.path.basename(saida_esperada)}")
        print("-> Verifique acima se o LOG detectou o idioma correto da faixa e se não usou o idioma do menu!")
    else:
        print(f"[FAIL] Arquivo final NÃO foi encontrado onde era esperado:")
        print(f"       Esperado: {saida_esperada}")
        
        # Verifica se o bug antigo voltou
        saida_antiga = f"{nome_base}_PTBR.mkv"
        if os.path.exists(saida_antiga):
            print(f"[AVISO] O arquivo foi gerado com o sufixo ANTIGO (_PTBR.mkv)!")

    # --- Limpeza Final ---
    print("\n[INFO] Limpando arquivos gerados pelo teste...")
    if os.path.exists(saida_esperada): os.remove(saida_esperada)
    # Tenta remover a legenda traduzida que sobra se manter_legenda=True
    legenda_trad = f"{nome_base}_{idioma_destino.upper()}.srt"
    if os.path.exists(legenda_trad): os.remove(legenda_trad)
    print("[INFO] Pasta de testes limpa.")

if __name__ == "__main__":
    diretorio_teste = os.path.dirname(os.path.abspath(__file__))
    # Defina o caminho para o seu MKV de teste aqui
    # Exemplo: um episódio de anime com legenda embutida
    caminho_teste = os.path.join(diretorio_teste, "VideoForTest.mkv")
    
    # Executa forçando a "preferência" errada no menu para ver se a inteligência de extração corrige
    rodar_teste_mkv(caminho_teste, idioma_origem_menu="eng", idioma_destino="pt")
