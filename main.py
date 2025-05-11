import sys
import socket
import helpers
from peer import Peer


# Mostra o menu no terminal
def print_menu():
    print("\t\nEscolha um comando:")
    print("\t[1] Listar peers")
    print("\t[2] Obter peers")
    print("\t[3] Listar arquivos locais")
    print("\t[4] Buscar arquivos")
    print("\t[5] Exibir estatísticas")
    print("\t[6] Alterar tamanho de chunk")
    print("\t[9] Sair")


def main(args: list):
    # Realiza a leitura dos parâmetros passados na linha de comando
    params = args
    peer_ip_and_port = params[0]
    shared_directory = params[2]

    # Verifica se o diretório é válido
    if not helpers.verify_files_path(shared_directory):
        exit(0)

    PEER_IP = socket.gethostbyname(peer_ip_and_port.split(":")[0])
    PEER_PORT = peer_ip_and_port.split(":")[1]

    # Cria o peer principal
    main_peer = Peer.create_peer(
        ip=PEER_IP, port=PEER_PORT, shared_directory=shared_directory, status="ONLINE")

    while True:
        send_message = False
        print_menu()
        choice = input(">").strip()

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
        elif choice == "2":
            ##--main_peer.increment_clock()
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
            ##--main_peer.increment_clock()
            # Envia a solicitação para todos os pares online
            for neighbor in main_peer.neighbors:
                if neighbor["status"] == "ONLINE":
                    main_peer.increment_clock()
                    message = f"{main_peer.ip}:{main_peer.port} {main_peer.clock} LS\n"
                    print(
                        f"Encaminhando mensagem '{message.strip()}' para {neighbor['ip']}:{neighbor['port']}")
                    main_peer.send_command(message, neighbor["ip"], int(
                        neighbor["port"]), expect_response=True)

            # Espera que os arquivos sejam recebidos em main_peer.received_files,
            if len(main_peer.received_files) == 0:
                print("Nenhum arquivo encontrado")
            else:
                print("\nArquivos encontrados na rede:")
                print(f"{'Index':<8}{'Nome':<26} | {'Tamanho':<10} | {'Peer':<20}")
                print(f"[0] {'<Cancelar>':<30}")
                for index, file in enumerate(main_peer.received_files, start=1):
                    print(
                        f"[{index}] {file['name']:<30} | {file['size']:<10} | {file['peer']:<25}")

                print("\nDigite o número do arquivo para fazer o download:")
                file_choice = input("> ").strip()

                if file_choice == "0":
                    continue
                try:
                    file_choice_int = int(file_choice)
                    if 1 <= file_choice_int <= len(main_peer.received_files):
                        selected_file = main_peer.received_files[file_choice_int - 1]
                        print(f"Arquivo selecionado: {selected_file['name']}")
                        target_peer = selected_file['peer']
                        ip_port = target_peer.split(":")
                        target_ip = ip_port[0]
                        target_port = int(ip_port[1])
                        main_peer.increment_clock()
                        dl_message = f"{main_peer.ip}:{main_peer.port} {main_peer.clock} DL {selected_file['name']} 0 0\n"
                        print(
                            f"Enviando mensagem: '{dl_message.strip()}' para {target_ip}:{target_port}")
                        main_peer.send_command(
                            dl_message, target_ip, target_port, expect_response=True)
                    else:
                        print("Opção inválida.")
                except ValueError:
                    print("Entrada inválida. Por favor, digite um número.")

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


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
