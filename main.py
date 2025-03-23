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
        print(f"Atualizando relogio para {self.clock}")

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

            while True:
                conn, addr = server.accept()
                data = conn.recv(1024).decode()
                if data:
                    self.handle_command(data, conn)
                conn.close()

        threading.Thread(target=server_thread, daemon=True).start()


    def handle_command(self, command, conn): ##TODO: terminar
        
        
        splitted_command = command.split()

        sender_ip = splitted_command[0].split(":")[0]
        sender_port = splitted_command[0].split(":")[1]

        if (splitted_command[2] == "HELLO"):
            print(f"Mensagem recebida: '{command}'")
            self.change_neighbor_status(sender_ip, sender_port, "ONLINE")

        elif (splitted_command[2] == "GET_PEERS"):
            vizinhos = []
            for neighbor in self.neighbors:
                if(neighbor["ip"] != self.ip and neighbor["port"] != self.port):
                    vizinhos.append(f"{neighbor['ip']}:{neighbor['port']}:{neighbor['status']}")
            response = f"{self.ip}:{self.port} {self.clock} PEER_LIST {len(self.neighbors)} {vizinhos}"  
            conn.sendall(response.encode())  

        elif(splitted_command[2] == "PEER_LIST"):
            print(f"Resposta recebida: '{command}'")
            recieved_neighbors = command.split()[:4]
            for neighbor in recieved_neighbors:
                neighbor_info = neighbor.split(":")
                self.change_neighbor_status(neighbor_info[0], neighbor_info[1], "ONLINE")

        elif(splitted_command[2] == "BYE"):
            self.change_neighbor_status(sender_ip, sender_ip, "OFFLINE")

        
        self.increment_clock()

    def send_command(self, command, ip, port): ##TODO: terminar de mandar as mensagens
        #self.increment_clock()
        splitted_command = command.split()
        if(len(splitted_command) < 3):
            print("Incorret message format")
        else:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, port))
                    s.sendall(command.encode())
                    #response = s.recv(1024).decode()
                    print(self.format_message(command, ip, port))
            except Exception as e:
                print(f"[Erro] Não foi possível conectar com {ip}:{port} - {e}")

    def format_message(self, command, destiny_ip, destiny_port):
        return f"Encaminhando mensagem '{command}' para {destiny_ip}:{destiny_port}"

    def change_neighbor_status(self, ip, port, status):

        for neighbor in self.neighbors:
            if(neighbor["ip"] == ip and neighbor["port"] == port):
                neighbor["status"] = status
                print(f"Atualizando peer {ip}:{port} status {status}")
                return

        neighbor_obj = {
            "ip": ip,
            "port": port,
            "status": status
        }
        self.neighbors.append(neighbor_obj)
        print(f"Adicionando novo peer {ip}:{port} status {status}")

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

    main_peer = Peer.create_peer(
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

        if selected_action["choice"] == "[1] Listar peers":
            main_peer.increment_clock()
            choices = ["[0] voltar para o menu anterior"]
            for index, neighbor in enumerate(main_peer.neighbors, start=1):
                choice_str = f"[{index}] {neighbor['ip']}:{neighbor['port']} {neighbor['status']}"
                choices.append(choice_str)

            choice_peer = [inquirer.List(
                "choice_peers", message="Lista de peers", choices=choices)]
            selected_peer = inquirer.prompt(choice_peer, theme=BlueComposure())

            for choice in choices:
                if selected_peer["choice_peers"] == choice:
                    peer = main_peer.neighbors[choices.index(choice) - 1]
            
            main_peer.send_command(
                f"{main_peer.ip}:{main_peer.port} {main_peer.clock} HELLO\n", peer["ip"], int(peer["port"]))
            

        elif selected_action["choice"] == "[3] Listar arquivos locais":
            main_peer.increment_clock()
            list_local_files(shared_directory)

        elif selected_action["choice"] == "[9] Sair":
            main_peer.increment_clock()
            for neighbor in main_peer.neighbors:
                main_peer.send_command(f"{main_peer.ip}:{main_peer.port} {main_peer.clock} BYE", neighbor["ip"], neighbor["port"])
            exit(0)

        elif selected_action["choice"] == "[2] Obter peers":
            main_peer.increment_clock()
            for neighbor in main_peer.neighbors:
                main_peer.send_command(f"{main_peer.ip}:{main_peer.port} {main_peer.clock} GET_PEERS", neighbor["ip"], int(neighbor["port"]))



if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
