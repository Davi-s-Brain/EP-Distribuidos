import sys
import inquirer
import socket
from inquirer.themes import BlueComposure

MAX_CONNECTIONS = 10

def main(args: list):
    params = args
    peer_ip_and_port = params[0]
    neighbor_list = params[1]
    shared_directory = params[2]

    PEER_IP = socket.gethostbyname(peer_ip_and_port.split(":")[0])
    PEER_PORT = int(peer_ip_and_port.split(":")[1])
    ADDR = (PEER_IP, PEER_PORT)

    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    peer_socket.bind(ADDR)
    peer_socket.listen(MAX_CONNECTIONS)

    choices = [inquirer.List("choice", message="Escolha um comando", choices=[
      "[1] Listar peers",
      "[2] Obter peers",
      "[3] Listar arquivos locais",
      "[4] Buscar arquivos",
      "[5] Exibir estatisticas",
      "[6] Alterar tamanho de chunk",
      "[7] Sair"
    ])]
    selected_action = inquirer.prompt(choices, theme=BlueComposure())

    if selected_action["choice"] == "[9] Sair":
        exit(0)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
