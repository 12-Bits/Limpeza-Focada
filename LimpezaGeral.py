import os
import glob
import json
import winreg
import datetime
from datetime import timezone

# Arquivo de configuração (será usado para carregar o destino de lixo, se necessário)
CONFIG_FILE = "config.json"

# Pastas comuns de lixo do sistema
# Usa os.path.expandvars para expandir variáveis de ambiente como %TEMP%
PASTAS_DE_LIXO = [
    # Temporários do Sistema e Usuário
    os.path.expandvars(r"%TEMP%"),
    os.path.expandvars(r"%SystemRoot%\Temp"),
    # Pastas de cache de aplicativos comuns
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\INetCache"), # Cache de internet
    os.path.expandvars(r"%LOCALAPPDATA%\Temp\Downloaded Installations"), # Instaladores temporários
]

# Extensões ou nomes de lixo específicos
NOMES_E_EXTENSOES_DE_LIXO = [
    ("~$", "*"),
    ("*.tmp", "*"),
    ("*.log", "*"),
    ("*.bak", "*"),
    ("*.old", "*"),
    ("*.dmp", "*"),
]

# Pastas de cache de navegadores (Exemplo: Google Chrome)
# Adicionar mais navegadores ou apps aqui
PASTAS_CACHE_NAVEGADORES = [
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache"),
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache"),
]

def escanear_arquivos_temporarios():
    """Escaneia pastas de lixo conhecidas e retorna uma lista de arquivos para limpeza."""
    arquivos_encontrados = []

    # 1. Escaneamento de Pastas Fixas de Lixo
    for pasta in PASTAS_DE_LIXO:
        if os.path.isdir(pasta):
            try:
                # Usa os.walk para pegar subpastas e glob para encontrar padrões
                for raiz, _, files in os.walk(pasta):
                    for nome_arquivo in files:
                        caminho_completo = os.path.join(raiz, nome_arquivo)

                        # Verifica se corresponde a uma extensão ou nome de lixo conhecido
                        for padrao, _ in NOMES_E_EXTENSOES_DE_LIXO:
                            if nome_arquivo.lower().endswith(padrao.lstrip('*').lower()) or padrao == "*":
                                arquivos_encontrados.append(caminho_completo)
                                break # Passa para o próximo arquivo
            except Exception as e:
                # Permite que a limpeza continue mesmo se uma pasta for inacessível
                print(f"⚠️ Aviso: Não foi possível escanear {pasta} ({e})")

    # 2. Escaneamento de Cache de Navegadores (Pastas completas)
    for pasta_cache in PASTAS_CACHE_NAVEGADORES:
        if os.path.isdir(pasta_cache):
            for raiz, _, files in os.walk(pasta_cache):
                for nome_arquivo in files:
                    caminho_completo = os.path.join(raiz, nome_arquivo)
                    arquivos_encontrados.append(caminho_completo)

    # Remove duplicatas
    return list(set(arquivos_encontrados))

def executar_limpeza(arquivos_para_deletar):
    """Tenta deletar os arquivos um por um e retorna o total de bytes liberados."""
    total_bytes_liberados = 0
    arquivos_removidos_com_sucesso = 0

    for arquivo in arquivos_para_deletar:
        try:
            # Obtém o tamanho antes de remover
            tamanho = os.path.getsize(arquivo)
            os.remove(arquivo)
            total_bytes_liberados += tamanho
            arquivos_removidos_com_sucesso += 1
        except Exception as e:
            # Arquivos em uso, permissão negada, etc.
            print(f"❌ Erro ao deletar lixo: {arquivo} ({e})")

    return total_bytes_liberados, arquivos_removidos_com_sucesso

def obter_pastas_programas_instalados():
    """
    Consulta o Registro do Windows para encontrar pastas de instalação de programas.
    Retorna um dicionário {nome_do_programa: caminho_da_pasta}
    """
    programas = {}

    # Define as chaves do registro a serem verificadas
    # (Programas de 64 bits, 32 bits em sistema 64 bits, e programas do usuário)
    chaves_reg = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]

    for hive, subkey_path in chaves_reg:
        try:
            with winreg.OpenKey(hive, subkey_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:

                            # Tenta ler o nome de exibição e o local de instalação
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]

                            # Adiciona à lista se ambos existirem e o local for válido
                            if display_name and install_location and os.path.isdir(install_location):
                                # Evita entradas duplicadas
                                if install_location not in programas.values():
                                    programas[display_name] = os.path.normpath(install_location)

                    except FileNotFoundError:
                        # Chave não possui 'DisplayName' ou 'InstallLocation', ignora
                        continue
                    except Exception as e:
                        # Outros erros (ex: permissão)
                        # print(f"Erro ao ler subchave: {e}") # Debug
                        continue
        except FileNotFoundError:
            # Chave principal não encontrada (ex: HKEY_CURRENT_USER pode não ter)
            # print(f"Chave não encontrada: {subkey_path}") # Debug
            continue
        except Exception as e:
            # print(f"Erro ao abrir chave principal: {e}") # Debug
            continue

    # Retorna o dicionário de programas
    return programas

def encontrar_arquivos_nao_acessados(pasta_raiz, data_limite_dt, cancel_flag=None):
    """
    Escaneia uma pasta e subpastas em busca de arquivos NÃO ACESSADOS
    desde a data_limite_dt.

    Usa 'os.path.getatime()' (Data de Acesso).
    """
    arquivos_encontrados = []
    total_arquivos_escaneados = 0

    try:
        for raiz, dirs, files in os.walk(pasta_raiz, topdown=True):

            # PONTO DE VERIFICAÇÃO DE CANCELAMENTO
            if cancel_flag and cancel_flag.is_set():
                print("Escaneamento de programa cancelado.")
                return arquivos_encontrados

            for arquivo in files:
                total_arquivos_escaneados += 1
                try:
                    caminho = os.path.join(raiz, arquivo)

                    stats = os.stat(caminho)
                    access_time_stamp = stats.st_atime

                    # Converte o timestamp para um objeto datetime ciente do fuso horário
                    access_time_dt = datetime.datetime.fromtimestamp(access_time_stamp, tz=timezone.utc)

                    # Converte a data_limite (que é 'naive') para UTC para comparação
                    data_limite_utc = data_limite_dt.astimezone(timezone.utc)

                    if access_time_dt < data_limite_utc:
                        arquivos_encontrados.append(caminho)

                except Exception as e:
                    # Ignora arquivos que não podem ser acessados (ex: permissão)
                    # print(f"Erro ao verificar atime de {caminho}: {e}") # Debug
                    continue

    except Exception as e:
        # print(f"Erro ao andar pela pasta {pasta_raiz}: {e}") # Debug
        pass

    return arquivos_encontrados, total_arquivos_escaneados

def encontrar_pastas_vazias(pasta_raiz):
    """
    Percorre a pasta raiz (de baixo para cima) e lista diretórios vazios.
    """
    pastas_vazias = []

    if not os.path.isdir(pasta_raiz):
        return pastas_vazias

    try:
        # topdown=False é CRUCIAL aqui.
        # Ele olha primeiro as subpastas mais profundas.
        # Se 'A/B' estiver vazia, ele lista 'B'. Se depois de remover 'B', 'A' ficar vazia,
        # essa lógica permite identificar cadeias de pastas vazias.
        for raiz, dirs, files in os.walk(pasta_raiz, topdown=False):
            for nome_dir in dirs:
                caminho_completo = os.path.join(raiz, nome_dir)
                try:
                    # Verifica se a pasta está realmente vazia (sem arquivos ou subpastas)
                    if not os.listdir(caminho_completo):
                        pastas_vazias.append(caminho_completo)
                except Exception:
                    # Ignora pastas sem permissão de leitura
                    continue
    except Exception as e:
        print(f"Erro ao caminhar pela pasta {pasta_raiz}: {e}")

    return pastas_vazias

def remover_pastas_vazias(lista_pastas):
    """Remove as pastas listadas usando os.rmdir (só funciona se estiverem vazias)."""
    removidas = 0
    erros = 0

    for pasta in lista_pastas:
        try:
            # os.rmdir só deleta se a pasta estiver VAZIA. É uma trava de segurança nativa.
            os.rmdir(pasta)
            removidas += 1
        except OSError:
            # Se a pasta não estiver vazia (ex: arquivo oculto ou criado recentemente), falha silenciosamente
            erros += 1

    return removidas