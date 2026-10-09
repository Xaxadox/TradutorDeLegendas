import os
import sys
import re

try:
    import requests
except ImportError:
    requests = None

ANILIST_URL = "https://graphql.anilist.co"

def buscar_anime(nome):
    query = '''
    query ($search: String) {
      Page(page: 1, perPage: 10) {
        media(search: $search, type: ANIME) {
          id
          title {
            romaji
            english
          }
        }
      }
    }
    '''
    variables = {'search': nome}
    
    if requests is None:
        print("[AVISO] Módulo 'requests' indisponível para busca.")
        return []

    try:
        response = requests.post(ANILIST_URL, json={'query': query, 'variables': variables}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['data']['Page']['media']
    except Exception as e:
        print(f"Erro ao buscar o anime: {e}")
        return []

def buscar_personagens(anime_id):
    query = '''
    query ($id: Int) {
      Media(id: $id) {
        characters(page: 1, perPage: 50, sort: [ROLE, RELEVANCE, ID]) {
          nodes {
            name {
              first
              last
              full
            }
          }
        }
      }
    }
    '''
    variables = {'id': anime_id}
    
    if requests is None:
        print("[AVISO] Módulo 'requests' indisponível para busca.")
        return []

    try:
        response = requests.post(ANILIST_URL, json={'query': query, 'variables': variables}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['data']['Media']['characters']['nodes']
    except Exception as e:
        print(f"Erro ao buscar os personagens: {e}")
        return []

def main():
    print("=" * 50)
    print("EXTRATOR AUTOMÁTICO DE PERSONAGENS (AniList)")
    print("=" * 50)
    
    nome_busca = input("Digite o nome do anime que deseja buscar: ").strip()
    if not nome_busca:
        return
        
    print("\nBuscando...")
    animes = buscar_anime(nome_busca)
    
    if not animes:
        print("Nenhum anime encontrado.")
        return
        
    print("\nResultados encontrados:")
    for i, anime in enumerate(animes):
        titulo_romaji = anime['title'].get('romaji') or ""
        titulo_eng = anime['title'].get('english') or ""
        print(f"[{i+1}] {titulo_romaji} / {titulo_eng}")
        
    escolha = input("\nEscolha o número do anime (ou pressione Enter para cancelar): ").strip()
    if not escolha.isdigit() or int(escolha) < 1 or int(escolha) > len(animes):
        print("Operação cancelada.")
        return
        
    anime_escolhido = animes[int(escolha) - 1]
    anime_id = anime_escolhido['id']
    titulo_principal = anime_escolhido['title'].get('romaji') or anime_escolhido['title'].get('english')
    
    print(f"\nO anime selecionado foi: {titulo_principal}")
    nome_arquivo = input("Qual deve ser o nome do arquivo? (Deixe em branco para usar o título original): ").strip()
    if not nome_arquivo:
        nome_arquivo = titulo_principal
        
    # Remove caracteres inválidos para Windows no nome do arquivo
    nome_arquivo = "".join([c for c in nome_arquivo if c.isalpha() or c.isdigit() or c in ' -_()']).strip()
    
    print("\nBuscando os nomes dos personagens mais relevantes...")
    personagens = buscar_personagens(anime_id)
    
    if not personagens:
        print("Nenhum personagem encontrado.")
        return
        
    lista_nomes = set()
    for char in personagens:
        nome_completo = char['name'].get('full')
        primeiro_nome = char['name'].get('first')
        ultimo_nome = char['name'].get('last')
        
        # Pega o nome completo
        if nome_completo:
            lista_nomes.add(nome_completo.strip())
        # E também garante que o Google não estrague apenas o primeiro nome
        if primeiro_nome:
            lista_nomes.add(primeiro_nome.strip())
        if ultimo_nome:
            lista_nomes.add(ultimo_nome.strip())
            
    # Ordena do nome mais longo para o mais curto (necessário para o replace não sobrepor nomes menores)
    lista_ordenada = sorted(list(lista_nomes), key=len, reverse=True)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pasta_glossarios = os.path.join(base_dir, "glossarios")
    os.makedirs(pasta_glossarios, exist_ok=True)
    
    caminho_arquivo = os.path.join(pasta_glossarios, f"{nome_arquivo}.txt")
    
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(f"# --- {titulo_principal} ---\n")
        f.write("# Personagens extraídos automaticamente via AniList API\n")
        f.write("# Adicione ou modifique abaixo conforme necessário:\n\n")
        for nome in lista_ordenada:
            if nome: # Evita linhas vazias
                f.write(f"{nome}\n")
            
    print(f"\n[SUCESSO] {len(lista_ordenada)} termos salvos em: {caminho_arquivo}")


def limpar_nome_anime(nome_arquivo):
    """Limpa o nome do arquivo para encontrar o nome do anime real."""
    nome = nome_arquivo.rsplit('.', 1)[0]
    # Remove tags em colchetes ou parênteses [SubsPlease], (1080p)
    nome = re.sub(r'\[.*?\]|\(.*?\)', '', nome)
    # Remove números de episódio finais (ex: - 12, - 01v2, _15)
    nome = re.sub(r'[-_]\s*\d+.*$', '', nome)
    # Limpa espaços e hifens
    nome = nome.replace('_', ' ').replace('-', ' ').strip()
    nome = re.sub(r'\s+', ' ', nome)
    return nome

def auto_alimentar(nome_video):
    """Busca silenciosa do anime e cria arquivo. Retorna o caminho do arquivo gerado."""
    nome_limpo = limpar_nome_anime(nome_video)
    if not nome_limpo:
        return None
        
    animes = buscar_anime(nome_limpo)
    if not animes:
        return None
        
    # Pega o primeiro (melhor match)
    anime = animes[0]
    anime_id = anime['id']
    titulo = anime['title'].get('romaji') or anime['title'].get('english') or nome_limpo
    
    # Remove caracteres inválidos para Windows
    nome_arquivo = "".join([c for c in titulo if c.isalpha() or c.isdigit() or c in ' -_()']).strip()
    
    personagens = buscar_personagens(anime_id)
    if not personagens:
        return None
        
    lista_nomes = set()
    for char in personagens:
        nome_completo = char['name'].get('full')
        primeiro_nome = char['name'].get('first')
        ultimo_nome = char['name'].get('last')
        
        if nome_completo:
            lista_nomes.add(nome_completo.strip())
        if primeiro_nome:
            lista_nomes.add(primeiro_nome.strip())
        if ultimo_nome:
            lista_nomes.add(ultimo_nome.strip())
            
    lista_ordenada = sorted(list(lista_nomes), key=len, reverse=True)
    
    # Salva
    pasta_glossarios = "glossarios"
    # Resolve path to be absolute relative to this file's dir
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pasta_glossarios_abs = os.path.join(base_dir, pasta_glossarios)
    os.makedirs(pasta_glossarios_abs, exist_ok=True)
    
    caminho_arquivo = os.path.join(pasta_glossarios_abs, f"{nome_arquivo}.txt")
    
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(f"# --- {titulo} ---\n")
        f.write("# Personagens extraídos via auto_alimentar\n\n")
        for nome in lista_ordenada:
            if nome:
                f.write(f"{nome}\n")
                
    return caminho_arquivo

if __name__ == "__main__":
    main()
