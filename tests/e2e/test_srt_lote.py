import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tradutor.orquestrador import OrquestradorTraducoes
import pysubs2

def rodar_teste():
    print("="*50)
    print(" INICIANDO AMBIENTE DE TESTES MASSIVOS ")
    print("="*50)
    
    model = OrquestradorTraducoes()
    
    # -- INJEÇÃO E2E (FASE 4) --
    # Isola a API do Google e a API AniList para não gastar limites e rodar 100% offline
    from unittest.mock import patch
    patcher = patch('tradutor.tradutores.google.MotorTraducaoGoogle.translate')
    mock_translate = patcher.start()
    mock_translate.side_effect = lambda text, src_lang, dest_lang: f"[MOCK] {text}"

    patcher_anilist = patch('alimentar_glossario.auto_alimentar', return_value=None)
    patcher_anilist.start()
    # --------------------------
    
    # Mockando a interface gráfica
    def mock_log(msg):
        print(f"[LOG] {msg}")
        
    def mock_progress(current, total):
        print(f"[PROGRES] {current}/{total}", end='\r')
        
    def mock_overwrite(nomes):
        print(f"[OVERWRITE] Sobrescrevendo: {nomes}")
        return True # Aceita sobrescrever sempre no teste
        
    def mock_finish():
        print("\n[SUCESSO] Pipeline do Orquestrador Concluído.")
        model.stop()
        
    model.set_callbacks(
        log_cb=mock_log,
        progress_cb=mock_progress,
        ask_overwrite_cb=mock_overwrite,
        finish_cb=mock_finish
    )
    
    # Prepara caminhos
    diretorio_teste = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    diretorio_legendas = os.path.join(diretorio_teste, "data", "legendas")
    
    import re
    # Filtra apenas os arquivos originais (sem sufixos de idioma de destino)
    arquivos = [
        f for f in os.listdir(diretorio_legendas)
        if f.endswith('.srt') and not re.search(r'_[A-Za-z].*\.srt$', f)
    ]
    
    if not arquivos:
        print("[AVISO] Nenhuma legenda original encontrada na pasta 'legendas'.")
        return

    relatorio_geral = {}
    arquivos_gerados = []
    
    for arquivo in arquivos:
        origem = os.path.join(diretorio_legendas, arquivo)
        nome_base = arquivo.rsplit('.', 1)[0]
        destino = os.path.join(diretorio_legendas, f"{nome_base}_PT.srt")
        arquivos_gerados.append(destino)
        
        # O nome do arquivo agora diz o idioma (ex: Russo.srt, Chines.srt).
        # Vamos mapear o nome pro código do idioma preferido esperado pelo backend.
        mapa_idiomas_srt = {
            "Frances": "fra", "Alemao": "ger", "Russo": "rus",
            "Japones": "jpn", "Chines": "chi", "Coreano": "kor",
            "Ingles": "eng", "Portugues": "por"
        }
        
        idioma_pref = mapa_idiomas_srt.get(nome_base, "auto")
        
        try:
            original_subs = pysubs2.load(origem)
            textos_originais = [s.text for s in original_subs]
        except Exception as e:
            print(f"[ERRO] Falha ao ler {arquivo}: {e}")
            continue

        print(f"\n=> Enviando {arquivo} para o Orquestrador (src_esperado: {idioma_pref})\n")
        
        # Reinicia a flag e inicia o processamento
        model._is_running = True
        model.start([origem], idioma_origem=idioma_pref, idioma_destino="pt", manter_legenda=True)
        
        while model._is_running:
            time.sleep(1)
            
        # Avaliando
        if os.path.exists(destino):
            traduzido_subs = pysubs2.load(destino)
            
            linhas_alteradas = 0
            detalhes = []
            for i, sub in enumerate(traduzido_subs):
                original = textos_originais[i] if i < len(textos_originais) else ""
                traduzido = sub.text
                if original.strip() != traduzido.strip():
                    linhas_alteradas += 1
                
                detalhes.append({
                    "indice": i+1,
                    "original": original,
                    "traduzido": traduzido
                })
                
            porcentagem = (linhas_alteradas / len(traduzido_subs)) * 100 if len(traduzido_subs) > 0 else 0
            
            relatorio_geral[arquivo] = {
                "linhas_processadas": len(traduzido_subs),
                "linhas_alteradas": linhas_alteradas,
                "porcentagem_traducao": f"{porcentagem:.2f}%",
                "status": "SUCESSO",
                "detalhes": detalhes
            }
        else:
            print(f"\n[FALHA] Arquivo {destino} não foi gerado.")
            relatorio_geral[arquivo] = {"status": "FALHA"}

    relatorio_path = os.path.join(diretorio_teste, "output", "relatorio_teste_massivo.json")
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        json.dump(relatorio_geral, f, indent=4, ensure_ascii=False)
        
    print(f"\n[ANALISE PRONTA] Relatório geral salvo em: {relatorio_path}")

if __name__ == "__main__":
    rodar_teste()
