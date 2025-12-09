import os
import shutil
import datetime
import json
import tkinter
from tkinter import messagebox

# Arquivo de configuração
CONFIG_FILE = "config.json"

# Pastas críticas fixas do sistema (NÃO podem ser removidas)
PASTAS_FIXAS_BLOQUEADAS = [
    r"C:\Windows\System32",
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    ".git",
    "$RECYCLE.BIN",
    "System Volume Information"
]

EXTENSOES_FIXAS_IGNORADAS = {
    '.dll','.exe','.sys', '.lnk', '.tmp', '.log', '.ini', '.dat', '.cab',
    '.msi', '.chm', '.pbd', '.pyc', '.git', '.svn', '.bak'
}

# --- LÓGICA DE CONFIGURAÇÃO  ---

def get_default_config():
    """Retorna um dicionário com a configuração padrão."""
    return {
        "pastas_bloqueadas": [],
        "pasta_destino_padrao": "",
        "pasta_padrao_rapido": os.path.join(os.path.expanduser("~"), "Downloads"),
        "extensoes_ignoradas": [],
        "mostrar_aviso_inicial": True
    }

def carregar_config():
    """
    Carrega a configuração do JSON.
    É à prova de falhas: se o arquivo não existir ou estiver corrompido,
    retorna a configuração padrão.
    """
    default_config = get_default_config()

    if os.path.exists(CONFIG_FILE):
        try:
            # Garante que o arquivo não está vazio
            if os.path.getsize(CONFIG_FILE) > 0:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    # Tenta ler o arquivo
                    config = json.load(f)

                    # Garante que todas as chaves padrão existem no arquivo lido
                    for key, value in default_config.items():
                        config.setdefault(key, value)
                    return config
            else:
                print(f"AVISO: {CONFIG_FILE} está vazio. Carregando padrões.")
                return default_config

        except json.JSONDecodeError:
            print(f"AVISO: {CONFIG_FILE} está corrompido. Carregando padrões.")
            return default_config
        except Exception as e:
            #Erro Generico
            print(f"Erro ao carregar {CONFIG_FILE}: {e}. Carregando padrões.")
            return default_config
    else:
        # O arquivo não existe
        return default_config

# Salvar configuração
def salvar_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# Config inicial (Carrega a configuração UMA VEZ na inicialização)
config = carregar_config()

# --- RESTO DAS FUNÇÕES DO PROGRAMA ---

def pasta_bloqueada(caminho):
    caminho = os.path.abspath(caminho).lower()

    # Usa a config carregada globalmente
    pastas_usuario = config.get("pastas_bloqueadas", [])
    todas_bloqueadas = [*PASTAS_FIXAS_BLOQUEADAS, *pastas_usuario]

    for bloqueada in todas_bloqueadas:
        try:
            caminho_bloqueado = os.path.abspath(bloqueada).lower()
            if caminho.startswith(caminho_bloqueado):
                return True
        except Exception:
            continue # Ignora caminhos inválidos na lista de bloqueio
    return False

def listar_arquivos(pastas, data_limite, cancel_flag=None, pastas_ignorar=None):
    """Retorna lista de arquivos mais antigos que a data limite (com subpastas)"""
    arquivos = []

    # Usa a config global
    pastas_usuario = set(os.path.normpath(p) for p in config.get("pastas_bloqueadas", []))
    pastas_fixas = {os.path.normpath(p) for p in PASTAS_FIXAS_BLOQUEADAS}

    # Se 'pastas_ignorar' (da GUI Avançada) foi passado, use-o
    if pastas_ignorar:
        pastas_usuario.update(set(os.path.normpath(p) for p in pastas_ignorar))

    nomes_subpastas_ignorar = set(os.path.basename(p) for p in pastas_fixas.union(pastas_usuario))
    caminhos_absolutos_ignorar = pastas_fixas.union(pastas_usuario)

    #Extensões
    extensoes_usuario = set(config.get("extensoes_ignoradas", []))
    extensoes_bloqueadas = extensoes_usuario.union(EXTENSOES_FIXAS_IGNORADAS)

    for pasta in pastas:
        pasta_inicial = os.path.normpath(pasta)
        if os.path.isdir(pasta_inicial):
            # Lógica de checagem de data
            for raiz, dirs, files in os.walk(pasta_inicial, topdown=True):

                # Filtragem de diretórios
                dirs[:] = [d for d in dirs if d not in nomes_subpastas_ignorar and
                           os.path.normpath(os.path.join(raiz, d)) not in caminhos_absolutos_ignorar]

                # ⭐️ PONTO DE VERIFICAÇÃO 1: Antes de processar os arquivos de uma nova pasta
                if cancel_flag and cancel_flag.is_set():
                    print("Escaneamento cancelado pelo usuário.") #Remover
                    return arquivos # Retorna o que foi encontrado até agora

                for arquivo in files:
                    try:
                        nome, extensao = os.path.splitext(arquivo)
                        if extensao.lower() in extensoes_bloqueadas:
                            continue
                    except Exception:
                        continue

                    caminho = os.path.join(raiz, arquivo)

                    try:
                        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(caminho))
                        if mod_time < data_limite:
                            arquivos.append(caminho)
                    except Exception as e:
                        print(f"⚠️ Erro ao acessar {caminho}: {e}")
        else:
            print(f"⚠️ Pasta inválida: {pasta}")
    return arquivos

def deletar_arquivos(arquivos, numeros):
    for num in numeros:
        if 1 <= num <= len(arquivos):
            try:
                os.remove(arquivos[num - 1])
                print(f"✅ {os.path.basename(arquivos[num - 1])} deletado.")
            except Exception as e:
                print(f"⚠️ Erro ao deletar {arquivos[num - 1]}: {e}")
        else:
            print(f"⚠️ Número {num} inválido.")

def mover_arquivos(arquivos, numeros, destino):
    if not os.path.exists(destino):
        os.makedirs(destino)
        print(f"📂 Pasta de destino criada: {destino}")
    for num in numeros:
        if 1 <= num <= len(arquivos):
            try:
                destino_final = os.path.join(destino, os.path.basename(arquivos[num - 1]))
                shutil.move(arquivos[num - 1], destino_final)
                print(f"✅ {os.path.basename(arquivos[num - 1])} movido para {destino}")
            except Exception as e:
                print(f"⚠️ Erro ao mover {arquivos[num - 1]}: {e}")
        else:
            print(f"⚠️ Número {num} inválido.")