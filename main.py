import sys
import socket
import helpers
import os
from peer import Peer
import time
import statistics
import csv
import threading
from concurrent.futures import ThreadPoolExecutor


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


def download_chunk(main_peer, file_name, chunk_size, chunk_index, peer_ip, peer_port):
    """Baixa um chunk específico de um peer."""
    try:
        main_peer.increment_clock()
        message = f"{main_peer.ip}:{main_peer.port} {main_peer.clock} DL {file_name} {chunk_size} {chunk_index}\n"
        return main_peer.send_command(message, peer_ip, peer_port, expect_response=True)
    except Exception as e:
        print(f"Erro ao baixar chunk {chunk_index}: {e}")
        return False


def download_file_parallel(main_peer, file_info, chunk_size):
    """Faz o download paralelo dos chunks de todos os peers disponíveis."""
    file_name = file_info["name"]
    file_size = int(file_info["size"])
    peers = [p.strip() for p in file_info["peer"].split(",") if p.strip()]
    peer_list = [(p.split(":")[0], int(p.split(":")[1])) for p in peers]
    total_chunks = (file_size + chunk_size - 1) // chunk_size

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=len(peer_list)) as executor:
        futures = []
        for chunk_index in range(total_chunks):
            peer_ip, peer_port = peer_list[chunk_index % len(peer_list)]
            futures.append(
                executor.submit(
                    download_chunk, main_peer, file_name, chunk_size, chunk_index, peer_ip, peer_port
                )
            )
        # Aguarda todos os downloads terminarem
        for i, future in enumerate(futures):
            try:
                success = future.result(timeout=10)
                if not success:
                    print(f"Falha ao baixar chunk {i}")
            except Exception as e:
                print(f"Erro no chunk {i}: {e}")

    duration = time.time() - start_time
    return duration


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
                        fieldnames = ["tamanho_arquivo", "tamanho_chunk", "num_peers", "tempo", "desvio_padrao"]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        for file_name, stats in stats_by_file.items():
                            dict_stats = [s for s in stats if isinstance(s, dict)]
                            if not dict_stats:
                                continue
                            durations = [s["duration"][0] if isinstance(s["duration"], list) else s["duration"] for s in dict_stats]
                            avg_duration = statistics.mean(durations)
                            first = dict_stats[0]
                            writer.writerow({
                                "tamanho_arquivo": first["file_size"],
                                "tamanho_chunk": first["chunk_size"],
                                "num_peers": first["num_peers"],
                                "tempo": avg_duration,
                                "desvio_padrao": first["deviation"]
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
                        try:
                            available_peers = []
                            for peer in selected_peers:
                                for p in peer.split(','):
                                    p = p.strip()
                                    if p:
                                        ip, port = p.split(':')
                                        available_peers.append(f"{ip}:{port}")

                            # Monta o dicionário file_info
                            file_info = {
                                "name": selected_file_name,
                                "size": selected_file_size,
                                "peer": ",".join(available_peers)
                            }

                            duration = download_file_parallel(main_peer, file_info, main_peer.chunck_size)

                            # Salva o arquivo
                            file_path = os.path.join(shared_directory, selected_file_name)
                            total_chunks = (int(selected_file_size) + main_peer.chunck_size - 1) // main_peer.chunck_size
                            with open(file_path, "wb") as f:
                                for chunk_index in range(total_chunks):
                                    chunk_data = main_peer.get_chunk_data(selected_file_name, chunk_index)
                                    if chunk_data:
                                        f.write(chunk_data)
                                    else:
                                        print(f"Chunk {chunk_index} ausente!")

                            # Estatísticas
                            main_peer.add_download_stat(
                                selected_file_name,
                                int(selected_file_size),
                                main_peer.chunck_size,
                                len(available_peers),
                                duration
                            )
                            print(f"Download do arquivo {selected_file_name} finalizado em {duration:.2f}s")
                            main_peer.received_chunks = {}
                        
                        except Exception as e:
                            print(f"Erro ao baixar o arquivo: {str(e)}")
                            continue

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
