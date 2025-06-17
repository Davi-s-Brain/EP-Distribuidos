import sys
import socket
import helpers
import os
from peer import Peer
import time
import statistics
import csv


# Mostra o menu no terminal
def print_menu():
    print("\t\nEscolha um comando:")
    print("\t[1] Listar peers")
    print("\t[2] Obter peers")
    print("\t[3] Listar arquivos locais")
    print("\t[4] Buscar arquivos")
    print("\t[5] Exibir estatísticas")
    print("\t[6] Alterar tamanho de chunk")
    print("\t[7] Salvar estatísicas em arquivo")
    print("\t[9] Sair")


def run_automated_test(main_peer, file_name, chunk_size):
    """Executa teste automatizado para um arquivo específico"""
    print("Iniciando teste automatizado...")
    
    # Initialize peers with retry mechanism
    max_retries = 3
    connected_peers = 0
    
    for attempt in range(max_retries):
        print(f"\nTentativa {attempt + 1} de conectar aos peers...")
        
        # Try to connect to all peers
        for neighbor in main_peer.neighbors:
            main_peer.increment_clock()
            message = f"{main_peer.ip}:{main_peer.port} {main_peer.clock} HELLO\n"
            if main_peer.send_command(message, neighbor["ip"], int(neighbor["port"])):
                print(f"Conectado com sucesso ao peer {neighbor['ip']}:{neighbor['port']}")
                connected_peers += 1
        
        time.sleep(1)  # Wait before retry

        print(f"Status dos peers após HELLO: {main_peer.neighbors}")
    
    if connected_peers == 0:
        print("Falha ao conectar com qualquer peer")
        return False
    
    print("\nIniciando listagem de arquivos...")
    # Lista os arquivos apenas dos peers online
    for neighbor in main_peer.neighbors:
        if neighbor["status"] == "ONLINE":
            main_peer.increment_clock()
            message = f"{main_peer.ip}:{main_peer.port} {main_peer.clock} LS\n"
            print(f"Solicitando arquivos de {neighbor['ip']}:{neighbor['port']}")
            main_peer.send_command(message, neighbor["ip"], int(neighbor["port"]), expect_response=True)
    
    time.sleep(1)  # Wait for responses
    
    # Encontra o arquivo alvo
    target_file = None
    for file in main_peer.received_files:
        if file["name"] == file_name:
            target_file = file
            break
    
    if target_file:
        try:
            # Criar arquivo vazio
            file_path = os.path.join(main_peer.shared_directory, file_name)
            with open(file_path, "wb") as f:
                pass
            
            # Conta peers únicos
            unique_peers = set(p.strip() for p in target_file["peer"].split(","))
            num_peers = len(unique_peers)
            
            # Calcula chunks
            total_chunks = (int(target_file["size"]) + chunk_size - 1) // chunk_size
            chunks_received = 0
            
            download_start = time.time()
            max_retries = 3
            
            # Faz download distribuindo chunks entre peers
            peers_list = list(unique_peers)
            while chunks_received < total_chunks:
                chunk_index = chunks_received
                peer = peers_list[chunk_index % len(peers_list)]
                ip, port = peer.split(":")
                
                retries = 0
                while retries < max_retries:
                    main_peer.increment_clock()
                    dl_message = f"{main_peer.ip}:{main_peer.port} {main_peer.clock} DL {file_name} {chunk_size} {chunk_index}\n"
                    if main_peer.send_command(dl_message, ip, int(port), expect_response=True):
                        # Verifica se o chunk foi realmente recebido
                        if main_peer.get_chunk_data(file_name, chunk_index):
                            chunks_received += 1
                            break
                    retries += 1
                    time.sleep(0.1)  # Pequeno delay entre tentativas
                
                if retries >= max_retries:
                    print(f"Erro: Não foi possível baixar o chunk {chunk_index}")
                    return False

            # Escreve arquivo final
            with open(file_path, "wb") as f:
                for i in range(total_chunks):
                    chunk_data = main_peer.get_chunk_data(file_name, i)
                    if chunk_data:
                        f.write(chunk_data)
            
            duration = time.time() - download_start
            
            # Adiciona estatísticas
            main_peer.add_download_stat(
                file_name,
                chunk_size, 
                num_peers,
                int(target_file["size"]),
                duration
            )
            
            print(f"TEST_RESULT;{file_name};{chunk_size};{num_peers};{target_file['size']};{duration:.6f}")
            main_peer.print_statistics()
            return True
            
        except Exception as e:
            print(f"Erro durante download: {e}")
            return False
    
    return False

def main(args: list):
    # Realiza a leitura dos parâmetros passados na linha de comando
    params = args
    peer_ip_and_port = params[0]
    shared_directory = params[2]
    chunck_size = 256

    # Verifica se o diretório é válido
    if not helpers.verify_files_path(shared_directory):
        exit(0)

    PEER_IP = socket.gethostbyname(peer_ip_and_port.split(":")[0])
    PEER_PORT = peer_ip_and_port.split(":")[1]

    # Cria o peer principal
    main_peer = Peer.create_peer(
        ip=PEER_IP, port=PEER_PORT, shared_directory=shared_directory, status="ONLINE", neighbors_file=params[1], chunck_size=256)

    # Adiciona modo de teste
    if len(args) > 3 and args[3] == "--test":
        print("MODO DE TESTE ATIVADO.")
        file_name = args[4]
        chunk_size = int(args[5])
        if run_automated_test(main_peer, file_name, chunk_size):
            sys.exit(0)
        sys.exit(1)

    while True:
        send_message = False
        print_menu()
        choice = input(">").strip()
        chunck_size = chunck_size

        # Verifica se o usuário escolheu a opção de listar peers
        if choice == "1":
            if not main_peer.neighbors:
                print("Nenhum peer disponível.")
                continue
            print("\nLista de peers:")
            print("[0] Voltar para o menu anterior")
            for index, neighbor in enumerate(main_peer.neighbors, start=1):
                print(
                    f"[{index}] {neighbor['ip']}:{neighbor['port']} {neighbor['status']} (clock: {neighbor['clock']})")
            sub_choice = input(">").strip()
            if sub_choice == "0":
                continue
            try:
                sub_choice_int = int(sub_choice)
                if 1 <= sub_choice_int <= len(main_peer.neighbors):
                    peer = main_peer.neighbors[sub_choice_int - 1]
                    main_peer.increment_clock()
                    message = f"{main_peer.ip}:{main_peer.port} {main_peer.clock} HELLO\n"
                    print(
                        f"Encaminhando mensagem '{message.strip()}' para {peer['ip']}:{peer['port']}")
                    send_message = main_peer.send_command(
                        message, peer["ip"], int(peer["port"]))
                    if send_message:
                        main_peer.change_neighbor_status(
                            peer["ip"], peer["port"], "ONLINE", peer['clock'])
                else:
                    print("Opção inválida.")
            except ValueError:
                print("Entrada inválida. Por favor, digite um número.")

        # Verifica se o usuário escolheu a opção de obter peers

        # Salva estatísticas num arquivo
        elif choice == "7":
            try: # TEM QUE ARRUMAR AQUI
                print("Digite o nome do arquivo para salvar as estatísticas (com extensão .csv):")
                file_name_input = input("> ").strip()
                if not file_name_input:
                    print("Nome do arquivo não pode ser vazio.")
                    continue

                # Agrupa as estatísticas pelo nome do arquivo
                stats_by_file = {}
                print(main_peer.download_stats.keys())
                for stat in main_peer.download_stats.values():
                    print(stat)
                    if stat["file_size"] not in stats_by_file:
                        stats_by_file[stat["file_size"]] = []
                    stats_by_file[stat["file_size"]].append(stat)

                try:
                    with open(file_name_input, "w", newline="") as csvfile:
                        fieldnames = ["TamanhoArquivo", "TamanhoChunk", "NumPeers", "Tempo", "DesvioPadrao"]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        for file_name, stats in stats_by_file.items():
                            # Process only statistics that are dicts
                            dict_stats = [s for s in stats if isinstance(s, dict)]
                            if not dict_stats:
                                continue
                            durations = [s["duration"] for s in dict_stats]
                            std_dev = statistics.stdev(durations) if len(durations) > 1 else 0.0
                            first = dict_stats[0]
                            writer.writerow({
                                "TamanhoArquivo": first["file_size"],
                                "TamanhoChunk": first["chunk_size"],
                                "NumPeers": first["num_peers"],
                                "Tempo": first["duration"],
                                "DesvioPadrao": std_dev
                            })
                    print(f"Estatísticas salvas em {file_name_input}")

                except IOError as e:
                    print(f"Erro ao salvar estatísticas: {str(e)}")
                    continue

            except Exception as e:
                print(f"Erro ao salvar estatísticas: {str(e)}")
                continue

        elif choice == "2":
            original_neighbors = main_peer.neighbors.copy()
            for neighbor in original_neighbors:
                main_peer.increment_clock()
                message = f"{main_peer.ip}:{main_peer.port} {main_peer.clock} GET_PEERS\n"
                print(
                    f"Encaminhando mensagem '{message.strip()}' para {neighbor['ip']}:{neighbor['port']}")
                main_peer.send_command(message, neighbor["ip"], int(
                    neighbor["port"]), expect_response=True)

        # Verifica se o usuário escolheu a opção de listar os arquivos locais
        elif choice == "3":
            arquivos = helpers.list_local_files(shared_directory)
            for arquivo in arquivos:
                print(arquivo)

        # Verifica se o usuário escolheu a opção de buscar arquivos
        elif choice == "4":
            # Envia a solicitação para todos os pares online
            for neighbor in main_peer.neighbors:
                if neighbor["status"] == "ONLINE":
                    main_peer.increment_clock()
                    message = f"{main_peer.ip}:{main_peer.port} {main_peer.clock} LS\n"
                    print(
                        f"Encaminhando mensagem '{message.strip()}' para {neighbor['ip']}:{neighbor['port']}")
                    main_peer.send_command(message, neighbor["ip"], int(
                        neighbor["port"]), expect_response=True)

            # Agrupa arquivos iguais (mesmo nome e tamanho)
            grouped_files = {}
            for file in main_peer.received_files:
                key = (file["name"], file["size"])
                if key not in grouped_files:
                    grouped_files[key] = {"peers": set()}
                # Adiciona acada peer ao conjunto de peers
                for peer in file["peer"].split(','):
                    peer = peer.strip()
                    if peer:  # Only add non-empty peers
                        grouped_files[key]["peers"].add(peer)

            if not grouped_files:
                print("Nenhum arquivo encontrado.")
            else:
                print("\nArquivos encontrados na rede:")
                print(f"{'Index':<8}{'Nome':<26} | {'Tamanho':<10} | {'Peers':<20}")
                print(f"[0] {'<Cancelar>':<30}")
                for index, (key, value) in enumerate(grouped_files.items(), start=1):
                    name, size = key

                    peers = ", ".join(sorted(value["peers"]))
                    print(f"[{index}] {name:<30} | {size:<10} | {peers:<25}")

                print("\nDigite o número do arquivo para fazer o download:")
                file_choice = input("> ").strip()

                if file_choice == "0":
                    continue
                try:
                    file_choice_int = int(file_choice)
                    
                    # Move a validação do índice para antes de qualquer processamento
                    if not (1 <= file_choice_int <= len(grouped_files)):
                        print("Opção inválida.")
                        continue

                    # Se chegou aqui, o índice é válido
                    selected_key = list(grouped_files.keys())[file_choice_int - 1]
                    selected_file_name, selected_file_size = selected_key
                    selected_peers = grouped_files[selected_key]["peers"]

                    print(f"Arquivo selecionado: {selected_file_name}")
                    
                    # Calcula o número total de chunks
                    total_chunks = (int(selected_file_size) + main_peer.chunck_size - 1) // main_peer.chunck_size
                    
                    try:
                        # Primeiro cria um arquivo vazio no diretório compartilhado
                        file_path = os.path.join(shared_directory, selected_file_name)
                        with open(file_path, "wb") as f:
                            pass
                            
                        # Prepara a lista de peers disponíveis
                        available_peers = []
                        for peer in selected_peers:
                            for p in peer.split(','):
                                p = p.strip()
                                if p:
                                    ip, port = p.split(':')
                                    available_peers.append((ip, int(port)))
                        
                        # Calcula o número total de chunks e distribui entre os peers
                        total_chunks = (int(selected_file_size) + main_peer.chunck_size - 1) // main_peer.chunck_size
                        chunks_per_peer = total_chunks // len(available_peers)
                        remaining_chunks = total_chunks % len(available_peers)
                        
                        # Faz o download dos chunks
                        download_start = time.time()
                        chunks_downloaded = 0
                        current_chunk = 0
                        
                        while chunks_downloaded < total_chunks:
                            for peer_index, (peer_ip, peer_port) in enumerate(available_peers):
                                # Calcula o intervalo de chunks para este peer
                                start_chunk = current_chunk
                                end_chunk = min(current_chunk + chunks_per_peer + (1 if peer_index < remaining_chunks else 0), total_chunks)
                                
                                # Faz o download dos chunks deste peer
                                for chunk_index in range(start_chunk, end_chunk):
                                    if not main_peer.get_chunk_data(selected_file_name, chunk_index):
                                        main_peer.increment_clock()
                                        dl_message = f"{main_peer.ip}:{main_peer.port} {main_peer.clock} DL {selected_file_name} {main_peer.chunck_size} {chunk_index}\n"
                                        print(f"Encaminhando mensagem: '{dl_message.strip()}' para {peer_ip}:{peer_port}")
                                        main_peer.send_command(dl_message, peer_ip, peer_port, expect_response=True)
                                        chunks_downloaded += 1
                                
                                current_chunk = end_chunk
                                if current_chunk >= total_chunks:
                                    break
                            
                            if current_chunk < total_chunks:
                                current_chunk = 0  # Começa novamente do primeiro chunk se não tiver mais chunks para baixar
                        
                        download_end = time.time()
                        # Escreve os chunks baixados no arquivo em ordem
                        with open(file_path, "wb") as f:
                            for chunk_index in range(total_chunks):
                                chunk_data = main_peer.get_chunk_data(selected_file_name, chunk_index)
                                if chunk_data:
                                    f.write(chunk_data)

                        duration = download_end - download_start
                        main_peer.add_download_stat(
                            selected_file_name,
                            int(selected_file_size),
                            main_peer.chunck_size,
                            len(available_peers),
                            duration
                        )

                        print(f"Download do arquivo {selected_file_name} finalizado.")
                        # Limpa a lista de arquivos recebidos e chunks recebidos
                        main_peer.received_chunks = {}
                        
                    except Exception as e:
                        print(f"Erro durante o download: {str(e)}")
                        continue

                except ValueError:
                    print("Entrada inválida. Por favor, digite um número.")

        elif choice == "5":
            main_peer.print_statistics()

        # Verifica se o usuário escolheu a opção de alterar o tamanho do chunk
        elif choice == "6":
            try:
                print("Digite novo tamanho de chunk:")
                new_chunk_size = int(input("> ").strip())
                if new_chunk_size <= 0:
                    print("Tamanho do chunk deve ser um número positivo.")
                else:
                    main_peer.chunck_size = new_chunk_size
                    print(f"Tamanho de chunk alterado: {new_chunk_size}")
            except ValueError:
                print("Entrada inválida. Por favor, digite um número válido.")


        # Verifica se o usuário escolheu a opção de sair. Em seguida, encaminha a mensagem BYE para todos os vizinhos
        elif choice == "9":
            print("Saindo...")
            for neighbor in main_peer.neighbors:
                main_peer.increment_clock()
                message = f"{main_peer.ip}:{main_peer.port} {main_peer.clock} BYE\n"
                print(
                    f"Encaminhando mensagem '{message.strip()}' para {neighbor['ip']}:{neighbor['port']}")
                main_peer.send_command(
                    message, neighbor["ip"], int(neighbor["port"]))
            exit(0)
        else:
            print("Opção inválida. Tente novamente.")
        # Se uma mensagem foi enviada, espera um pouco para evitar flood
        
        

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
