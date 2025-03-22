import os
import sys
import socket
import inquirer
from inquirer.themes import BlueComposure

MAX_CONNECTIONS = 10


class Peer:
    def __init__(self, ip, port, shared_directory, status):
        self.ip = ip
        self.port = port
        self.shared_directory = shared_directory
        self.status = status
        self.clock = 0

    def __str__(self):
        return f"Peer {self.ip}:{self.port} - {self.shared_directory}"

    def __repr__(self):
        return f"Peer {self.ip}:{self.port} - {self.shared_directory}"

    @classmethod
    def create_peer(cls, ip, port, shared_directory, status):
        address = (ip, int(port))
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        peer_socket.bind(address)
        peer_socket.listen(MAX_CONNECTIONS)

        return cls(ip, port, shared_directory, status)


def handle_file(path: str) -> list[str]:
    neighbor = []
    try:
        with open(path, 'r') as file:
            for file_neighbor in file.readlines():
                formated_neighbor = file_neighbor.strip()
                neighbor.append(formated_neighbor)
    except IOError as error:
        print(f"Error reading file {path}: {error}")
        return []
    return neighbor


def list_local_files(directory: str) -> None:
    try:
        files = os.listdir(directory)
    except Exception as error:
        print(f"Error reading directory {directory}: {error}")
 
    for file in files:
        print(f"{file}")


def main(args: list):
    params = args
    peer_ip_and_port = params[0]
    neighbor_list = params[1]
    shared_directory = params[2]

    PEER_IP = socket.gethostbyname(peer_ip_and_port.split(":")[0])
    PEER_PORT = int(peer_ip_and_port.split(":")[1])

    initial_peer = Peer.create_peer(
        ip=PEER_IP, port=PEER_PORT, shared_directory=shared_directory, status="ONLINE")

    for neighbor in handle_file(neighbor_list):
        split_neighbor = neighbor.split(":")
        neighbor_ip = split_neighbor[0]
        neighbor_port = split_neighbor[1]

        neighbor_peer = Peer.create_peer(
            ip=neighbor_ip, port=neighbor_port, shared_directory=shared_directory, status="OFFLINE")

        if neighbor_peer:
            print(
                f"Adicionando novo peer {neighbor_ip}:{neighbor_port} status OFFLINE")
        else:
            print(f"Erro na criação do peer")

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

    if selected_action["choice"] == "[3] Listar arquivos locais":
        list_local_files(shared_directory)

    elif selected_action["choice"] == "[9] Sair":
        exit(0)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
