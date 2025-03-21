import sys
import inquirer
from inquirer.themes import BlueComposure


def main(args: list):
    parametros = args
    endereco_peer = parametros[0]
    vizinhos = parametros[1]
    diretorio_compartilhado = parametros[2]

    escolhas = [inquirer.List("escolha", message="Escolha um comando", choices=[
      "[1] Listar peers",
      "[2] Obter peers",
      "[3] Listar arquivos locais",
      "[4] Buscar arquivos",
      "[5] Exibir estatisticas",
      "[6] Alterar tamanho de chunk",
      "[9] Sair"
    ])]
    acao_escolhida = inquirer.prompt(escolhas, theme=BlueComposure())

    if acao_escolhida["escolha"] == "[9] Sair":
        exit(0)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
