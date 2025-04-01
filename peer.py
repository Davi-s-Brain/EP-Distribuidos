import socket
import helpers
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
        print(f" => Atualizando relogio para {self.clock}")

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
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.bind((self.ip, int(self.port)))
                server.listen(MAX_CONNECTIONS)

                while True:
                    conn, addr = server.accept()
                    data = conn.recv(1024).decode()
                    if data:
                        self.handle_command(data, conn)
                    conn.close()

            except Exception as e:
                print(f"[Erro] {self.ip}:{self.port} não está disponível: {e}")
                exit(0)

        threading.Thread(target=server_thread, daemon=True).start()

    def handle_command(self, command, conn):
        splitted_command = command.split()

        sender_ip = splitted_command[0].split(":")[0]
        sender_port = splitted_command[0].split(":")[1]

        if (splitted_command[2] == "HELLO"):
            formated_command = helpers.format_string(command)
            print(f"Mensagem recebida: '{formated_command}'")
            self.increment_clock()
            self.change_neighbor_status(sender_ip, sender_port, "ONLINE")

        elif (splitted_command[2] == "GET_PEERS"):
            formated_command = helpers.format_string(command)
            print(f"Resposta recebida: '{formated_command}'")
            self.increment_clock()
            vizinhos = []
            for neighbor in self.neighbors:
                if (neighbor['port'] != sender_port):
                    vizinhos.append(
                        f"{neighbor['ip']}:{neighbor['port']}:{neighbor['status']}:0")
            peers_str = " ".join(vizinhos)

            self.increment_clock()
            response = f"{self.ip}:{self.port} {self.clock} PEER_LIST {len(self.neighbors)} {peers_str}\n"
            formated_response = helpers.format_string(response)
            print(
                f"Encaminhando mensagem '{formated_response}' para {sender_ip}:{sender_port}")
            conn.sendall(response.encode())

        elif (splitted_command[2] == "PEER_LIST"):
            formated_command = helpers.format_string(command)
            print(f"Resposta recebida: '{formated_command}'")
            self.increment_clock()
            recieved_neighbors = command.split()[4:]
            for neighbor in recieved_neighbors:
                neighbor_info = neighbor.split(":")
                self.change_neighbor_status(
                    neighbor_info[0], neighbor_info[1], neighbor_info[2])

        elif (splitted_command[2] == "BYE"):
            formated_command = helpers.format_string(command)
            print(f"Mensagem recebida '{formated_command}'")
            self.increment_clock()
            self.change_neighbor_status(sender_ip, sender_port, "OFFLINE")

    def send_command(self, command, ip, port, expect_response=False) -> bool:
        splitted_command = command.split()
        if len(splitted_command) < 3:
            print("Incorrect message format")
            return False
        else:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, port))
                    s.sendall(command.encode())

                    if expect_response:
                        response = s.recv(4096).decode()
                        self.handle_command(response, s)
                return True
            except Exception as e:
                print(
                    f"[Erro] Não foi possível conectar com {ip}:{port} - {e}")
                return False

    def format_message(self, command, destiny_ip, destiny_port):
        return f"Encaminhando mensagem '{command}' para {destiny_ip}:{destiny_port}"

    def change_neighbor_status(self, ip, port, status):
        for neighbor in self.neighbors:
            if (neighbor["ip"] == ip and neighbor["port"] == port):
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
