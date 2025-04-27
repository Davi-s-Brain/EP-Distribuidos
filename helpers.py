import os

# Função que lista os arquivos locais dado um certo diretório
def list_local_files(directory: str) -> None:
    try:
        files = os.listdir(directory)
    except Exception as error:
        print(f"Erro ao ler o diretório {directory}: {error}")
    
    return files

# Função que verifica se o diretório existe, se é um diretório e se é acessível
def verify_files_path(directory: str) -> bool:
    if not os.path.exists(directory):
        print(f"O diretório {directory} não existe")
        return False
    elif not os.path.isdir(directory):
        print(f"{directory} não é um diretório")
        return False
    elif not os.access(directory, os.R_OK):
        print(f"O diretório {directory} não é acessível")
        return False

    return True

# Função que formata uma string removendo quebras de linha
def format_string(string: str) -> str:
    return string.replace("\n", "")
