import sys
import socket
import helpers
import inquirer
from peer import Peer
from inquirer.themes import BlueComposure


def main(args: list):
    # Realiza a leitura dos parâmetros passados na linha de comando
    params = args
    peer_ip_and_port = params[0]
    shared_directory = params[2]
    selected_action = {"choice": ""}

    # Verifica se o diretório é válido
    isPathValid = helpers.verify_files_path(shared_directory)

    # Caso o diretório não seja válido o programa é finalizado
    if not isPathValid:
        exit(0)

    PEER_IP = socket.gethostbyname(peer_ip_and_port.split(":")[0])
    PEER_PORT = peer_ip_and_port.split(":")[1]

    # Cria o peer principal
    main_peer = Peer.create_peer(
        ip=PEER_IP, port=PEER_PORT, shared_directory=shared_directory, status="ONLINE")

    # Mostra o menu no terminal
    while selected_action["choice"] != "[7] Sair":
        send_message = False
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

        # Verifica se o usuário escolheu a opção de listar peers
        if selected_action["choice"] == "[1] Listar peers":
            choices = ["[0] voltar para o menu anterior"]
            for index, neighbor in enumerate(main_peer.neighbors, start=1):
                choice_str = f"[{index}] {neighbor['ip']}:{neighbor['port']} {neighbor['status']}"
                choices.append(choice_str)

            choice_peer = [inquirer.List(
                "choice_peers", message="Lista de peers", choices=choices)]
            selected_peer = inquirer.prompt(choice_peer, theme=BlueComposure())

            for choice in choices:
                if selected_peer["choice_peers"] == "[0] voltar para o menu anterior":
                    break
                if selected_peer["choice_peers"] == choice:
                    peer = main_peer.neighbors[choices.index(choice) - 1]
                    main_peer.increment_clock()
                    print(f"Encaminhando mensagem '{main_peer.ip}:{main_peer.port} {main_peer.clock} HELLO' para {peer['ip']}:{peer['port']}")
                    send_message = main_peer.send_command(
                        f"{main_peer.ip}:{main_peer.port} {main_peer.clock} HELLO\n", peer["ip"], int(peer["port"]))

            if send_message:
                main_peer.change_neighbor_status(peer["ip"], peer["port"], "ONLINE")

        # Verifica se o usuário escolheu a opção de obter peers
        elif selected_action["choice"] == "[2] Obter peers":
            main_peer.increment_clock()
            original_neighbors = main_peer.neighbors.copy()
            for neighbor in original_neighbors:
                main_peer.send_command(
                    f"{main_peer.ip}:{main_peer.port} {main_peer.clock} GET_PEERS\n", neighbor["ip"], int(neighbor["port"]),expect_response=True)

        # Verifica se o usuário escolheu a opção de listar os arquivos locais
        elif selected_action["choice"] == "[3] Listar arquivos locais":
            helpers.list_local_files(shared_directory)

        # Verifica se o usuário escolheu a opção de sair. Em seguida, encaminha a mensagem BYE para todos os vizinhos
        elif selected_action["choice"] == "[7] Sair":
            print("Saindo...")
            for neighbor in main_peer.neighbors:
                main_peer.increment_clock()
                print(f"Encaminhando Mensagem '{main_peer.ip}:{main_peer.port} {main_peer.clock} BYE' para {neighbor['ip']}:{neighbor['port']}")
                main_peer.send_command(
                    f"{main_peer.ip}:{main_peer.port} {main_peer.clock} BYE\n", neighbor["ip"], int(neighbor["port"]))
            exit(0)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
