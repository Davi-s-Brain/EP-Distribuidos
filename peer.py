import socket
import helpers
import threading
import os
import base64

MAX_CONNECTIONS = 10


# Classe que representa um peer
class Peer:
    def __init__(self, ip, port, shared_directory, status, neighbors, chunck_size):
        self.ip = ip
        self.port = port
        self.shared_directory = shared_directory
        self.status = status
        self.clock = 0
        self.neighbors = neighbors
        self.chunck_size = chunck_size
        self.received_files = []
        self.received_chunks = {}
        self.start_server()

    def increment_clock(self):
        self.clock += 1
        print(f" => Atualizando relogio para {self.clock}")

    # Método de classe para criar um peer usando o arquivo de vizinhos fornecido
    @classmethod
    def create_peer(cls, ip, port, shared_directory, status, neighbors_file, chunck_size):
        neighbors = []
        try:
            with open(neighbors_file, "r") as file_vizinhos:
                neighbors_lines = file_vizinhos.readlines()
            for line in neighbors_lines:
                line = line.strip()
                if line:
                    neigh_ip, neigh_port = line.split(":")
                    new_neighbor = {
                        "ip": neigh_ip,
                        "port": neigh_port,
                        "status": "OFFLINE",
                        "clock": 0
                    }
                    neighbors.append(new_neighbor)

        except Exception as e:
            print(f"[Erro] Não foi possível ler o arquivo de vizinhos {neighbors_file}: {e}")
            exit(0)

        for neighbor in neighbors:
            print(f"Adicionando novo peer {neighbor['ip']}:{neighbor['port']} status OFFLINE")
        return cls(ip, port, shared_directory, status, neighbors, chunck_size)

    # Método para iniciar o servidor que escuta por conexões de outros peers
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

    def lamport_verify(self ,sender_clock):
        if sender_clock > self.clock:
            self.clock = sender_clock
            print(f"=> Atualizando relogio para {self.clock} #Atualização de clock")    

    # Método para lidar com os comandos recebidos
    def handle_command(self, command, conn):
        splitted_command = command.split()

        sender_clock = int(splitted_command[1])
        sender_ip = splitted_command[0].split(":")[0]
        sender_port = splitted_command[0].split(":")[1]

        #Atualizando clock segundo modelo de Lamport
        

        for neighbor in self.neighbors:
            if(neighbor['ip'] == sender_ip and neighbor['port'] == sender_port):
                neighbor['clock'] = int(neighbor['clock'])
                if neighbor['clock'] < sender_clock:
                    neighbor['clock'] = sender_clock

        # Verifica se o comando recebido é do tipo HELLO
        if (splitted_command[2] == "HELLO"):
            formated_command = helpers.format_string(command)
            print(f"Mensagem recebida: '{formated_command}'")
            if sender_clock > self.clock:
                self.clock = sender_clock
                print(f"=> Atualizando relogio para {self.clock}")    
                self.increment_clock()
            else:
                self.increment_clock()
            self.change_neighbor_status(sender_ip, sender_port, "ONLINE", sender_clock)

        # Verifica se o comando recebido é do tipo GET_PEERS
        elif (splitted_command[2] == "GET_PEERS"):
            formated_command = helpers.format_string(command)
            print(f"Resposta recebida: '{formated_command}'")
            if sender_clock > self.clock:
                self.clock = sender_clock
                print(f"=> Atualizando relogio para {self.clock}")  
                self.increment_clock()  
            else:
                self.increment_clock()
            vizinhos = []
            for neighbor in self.neighbors:
                if (neighbor['port'] != sender_port):
                    vizinhos.append(
                        f"{neighbor['ip']}:{neighbor['port']}:{neighbor['status']}:{neighbor['clock']}")
            peers_str = " ".join(vizinhos)

            self.increment_clock()
            response = f"{self.ip}:{self.port} {self.clock} PEER_LIST {len(self.neighbors)} {peers_str}\n"
            formated_response = helpers.format_string(response)
            print(
                f"Encaminhando mensagem '{formated_response}' para {sender_ip}:{sender_port}")
            conn.sendall(response.encode())

        # Verifica se o comando recebido é do tipo PEER_LIST
        elif (splitted_command[2] == "PEER_LIST"):
            formated_command = helpers.format_string(command)
            print(f"Resposta recebida: '{formated_command}'")
            if sender_clock > self.clock:
                self.clock = sender_clock
                print(f"=> Atualizando relogio para {self.clock}")  
                self.increment_clock()  
            else:
                self.increment_clock()
            recieved_neighbors = command.split()[4:]
            for neighbor in recieved_neighbors:
                neighbor_info = neighbor.split(":")
                for self_neigh in self.neighbors:
                    if(neighbor_info[0] == self_neigh['ip'] and neighbor_info[1] == self_neigh['port'] and neighbor_info[3] < self_neigh['clock']):
                        pass
                    else:    
                        self.change_neighbor_status(
                            neighbor_info[0], neighbor_info[1], neighbor_info[2], neighbor_info[3])
                

        # Verifica se o comando recebido é do tipo BYE
        elif (splitted_command[2] == "BYE"):
            formated_command = helpers.format_string(command)
            print(f"Mensagem recebida '{formated_command}'")
            if sender_clock > self.clock:
                self.clock = sender_clock
                print(f"=> Atualizando relogio para {self.clock}") 
                self.increment_clock()   
            else:
                self.increment_clock()
            self.change_neighbor_status(sender_ip, sender_port, "OFFLINE", sender_clock)

        # Verifica se o comando recebido é do tipo LS
        elif (splitted_command[2] == "LS"):
            formated_command = helpers.format_string(command)
            print(f"Mensagem recebida '{formated_command}'")
            if sender_clock > self.clock:
                self.clock = sender_clock
                print(f"=> Atualizando relogio para {self.clock}")    
                self.increment_clock()
            else:
                self.increment_clock()
            files = helpers.list_local_files(self.shared_directory)
            files_str = []
            files_without_ip = []

            for file in files:
                file_size = os.path.getsize(
                    os.path.join(self.shared_directory, file))
                files_str.append(f"{file}:{file_size}:{self.ip}:{self.port}")
                files_without_ip.append(f"{file}:{file_size}")

            formated_files = " ".join(files_str)
            response = f"{self.ip}:{self.port} {self.clock} LS_LIST {len(files)} {formated_files}\n"
            formated_response = helpers.format_string(response)
            print(
                f"Encaminhando mensagem {self.ip}:{self.port} {self.clock} LS_LIST {len(files)} { ' '.join(files_without_ip) } para {sender_ip}:{sender_port}")
            conn.sendall(response.encode())

        # Verifica se o comando recebido é do tipo LS_LIST
        elif (splitted_command[2] == "LS_LIST"):
            formated_command = helpers.format_string(command)
            print(f"Resposta recebida: '{formated_command}'")
            if sender_clock > self.clock:
                self.clock = sender_clock
                print(f"=> Atualizando relogio para {self.clock}")    
                self.increment_clock()
            else:
                self.increment_clock()
            files_entries = command.split()[4:]
            for entry in files_entries:
                parts = entry.split(":")
                if len(parts) == 4:
                    file_dict = {
                        "name": parts[0],
                        "size": parts[1],
                        "peer": f"{parts[2]}:{parts[3]}"
                    }

                    grouped = False
                    for existing_file in self.received_files:
                        if existing_file["name"] == file_dict["name"] and existing_file["size"] == file_dict["size"]:
                            existing_file["peer"] += f", {file_dict['peer']}"
                            grouped = True
                            break
                    if not grouped:
                        self.received_files.append({
                            "name": file_dict["name"],
                            "size": file_dict["size"],
                            "peer": file_dict["peer"]
                        })

        # Verifica se o comando recebido é do tipo DL
        elif (splitted_command[2] == "DL"):
            formated_command = helpers.format_string(command)
            print(f"Mensagem recebida '{formated_command}'")
            if sender_clock > self.clock:
                self.clock = sender_clock
                print(f"=> Atualizando relogio para {self.clock}")  
                self.increment_clock()  
            else:
                self.increment_clock()
            file_name = splitted_command[3]
            chunk_size = int(splitted_command[4])
            chunk_index = int(splitted_command[5])
            file_path = os.path.join(self.shared_directory, file_name)
            if os.path.exists(file_path):
                with open(file_path, "rb") as file:
                    file.seek(chunk_index * chunk_size)
                    data = file.read(chunk_size)
                    b64_data = base64.b64encode(data).decode()
                response = f"{self.ip}:{self.port} {self.clock} FILE {file_name} {chunk_size} {chunk_index} {b64_data}\n"
                conn.sendall(response.encode())
                print(
                    f"Enviando chunk {chunk_index} do arquivo {file_name} para {sender_ip}:{sender_port}")
            else:
                print(f"Arquivo {file_name} não encontrado.")

        # Verifica se o comando recebido é do tipo FILE
        elif (splitted_command[2] == "FILE"):
            formated_command = helpers.format_string(command)
            print(f"Mensagem recebida: '{formated_command}'")
            if sender_clock > self.clock:
                self.clock = sender_clock
                print(f"=> Atualizando relogio para {self.clock}")   
                self.increment_clock() 
            else:
                self.increment_clock()
            file_name = splitted_command[3]
            chunk_size = int(splitted_command[4])
            chunk_index = int(splitted_command[5])

            try:
                b64_data = command.split(" ", 6)[-1].strip()
                file_data = base64.b64decode(b64_data)
                self.store_chunk_data(file_name, chunk_index, file_data)
            except Exception as e:
                print(f"Erro ao decodificar chunk: {e}")

    # Método que envia comandos para outros peers
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
                        response = ""
                        while True:
                            part = s.recv(4096).decode()
                            response += part
                            if "\n" in part:
                                break
                        self.handle_command(response, s)
                return True
            except Exception as e:
                print(
                    f"[Erro] Não foi possível conectar com {ip}:{port} - {e}")
                return False

    # Método que altera o status de um vizinho e o adiciona se não existir
    def change_neighbor_status(self, ip, port, status, clock):
        for neighbor in self.neighbors:
            if (neighbor["ip"] == ip and neighbor["port"] == port):
                neighbor["status"] = status
                neighbor["clock"] = clock
                print(f"Atualizando peer {ip}:{port} status {status}")
                return

        neighbor_obj = {
            "ip": ip,
            "port": port,
            "status": status,
            "clock": clock
        }
        self.neighbors.append(neighbor_obj)
        print(f"Adicionando novo peer {ip}:{port} status {status}")

    def get_chunk_data(self, filename, chunk_index):
        key = f"{filename}_{chunk_index}"
        return self.received_chunks.get(key)

    def store_chunk_data(self, filename, chunk_index, data):
        key = f"{filename}_{chunk_index}"
        self.received_chunks[key] = data
