import os
import sys
import socket
import inquirer
from inquirer.themes import BlueComposure
import threading

MAX_CONNECTIONS = 10


class Peer:
    def __init__(self, ip, port, shared_directory, status, neighbors):
        self.ip = ip
        self.port = port
        self.shared_directory = shared_directory
        self.status = status
        self.clock = 0
        self.neighbors = neighbors
        self.start_server()

    def increment_clock(self):
        self.clock += 1

    @classmethod
    def create_peer(cls, ip, port, shared_directory, status):
        neighbors = []
        last_port_digit = port[-1]

        with open(f"./vizinhos/v{last_port_digit}_vizinhos.txt") as file_vizinhos:
            neighbors_file = file_vizinhos.readlines()

        for neighbor in neighbors_file:
            formated_neighbor = neighbor.replace("\n", "")
            formated_ip, formated_port = formated_neighbor.split(":")

            new_neighbor = {"ip": formated_ip,
                            "port": formated_port, "status": "OFFLINE"}

            neighbors.append(new_neighbor)

        for neighbor in neighbors:
            print(
                f"Adicionando novo peer {neighbor['ip']}:{neighbor['port']} status OFFLINE")

        return cls(ip, port, shared_directory, status, neighbors)

    def start_server(self):
        def server_thread():
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind((self.ip, int(self.port)))
            server.listen(MAX_CONNECTIONS)

            ip = socket.gethostbyname(self.ip)
            print(f"[Servidor] Escutando em {ip}:{self.port}")

            while True:
                conn, addr = server.accept()
                data = conn.recv(1024).decode()
                self.handle_command(data, conn)
                conn.close()

        threading.Thread(target=server_thread, daemon=True).start()


    def handle_command(self, command, conn):
        if command == "TIME":
            print("Recebi um Time")
        elif command.startswith("ECHO "):
            print("Recebi um echo")
        else:
            response = "Comando desconhecido"
        ##conn.sendall(response.encode())

    def send_command(self, command, ip, port):
        splitted_command = command.split(" ")
        if(len(splitted_command) < 3):
            print("Incorret message format")
        else:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, port))
                    s.sendall(command.encode())
                    #response = s.recv(1024).decode()
                    print(f"Encaminhando mensagem {command} para {ip}{port}")
            except Exception as e:
                print(f"[Erro] Não foi possível conectar com {ip}:{port} - {e}")

def handle_file(path: str) -> list[str]:
    neighbor = []
    try:
        with open(path, 'r') as file:
            for file_neighbor in file.readlines():
                formated_neighbor = file_neighbor.strip()
                neighbor.append(formated_neighbor)
    except IOError as error:
        print(f"Erro ao ler o arquivo {path}: {error}")
        return []
    return neighbor


def list_local_files(directory: str) -> None:
    try:
        files = os.listdir(directory)
    except Exception as error:
        print(f"Erro ao ler o diretório {directory}: {error}")

    for file in files:
        print(f"{file}")


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


def main(args: list):
    params = args
    peer_ip_and_port = params[0]
    shared_directory = params[2]
    selected_action = {"choice": ""}

    isPathValid = verify_files_path(shared_directory)

    if not isPathValid:
        exit(0)

    PEER_IP = socket.gethostbyname(peer_ip_and_port.split(":")[0])
    PEER_PORT = peer_ip_and_port.split(":")[1]

    Peer.create_peer(
        ip=PEER_IP, port=PEER_PORT, shared_directory=shared_directory, status="ONLINE")

    while selected_action["choice"] != "[7] Sair":
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
