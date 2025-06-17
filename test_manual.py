import pexpect
import time

def run_automated_test():
    """Executa testes automatizados simulando inputs do usuário"""
    
    # Inicia os peers em processos separados
    peer1 = pexpect.spawn('python3 main.py 127.0.0.1:8001 vizinhos/v1_vizinhos.txt ./')
    time.sleep(1)
    peer2 = pexpect.spawn('python3 main.py 127.0.0.1:8002 vizinhos/v2_vizinhos.txt ./teste')
    time.sleep(1) 
    peer4 = pexpect.spawn('python3 main.py 127.0.0.1:8004 vizinhos/v4_vizinhos.txt ./teste')
    time.sleep(1)

    # Lista de comandos para testar no peer1
    test_sequence = [
        # Conectar peers
        "1",  # Listar peers
        "1",  # Seleciona primeiro peer
        "1",  # Listar peers
        "2",  # Seleciona segundo peer
        
        # Buscar arquivos
        "4",  # Buscar arquivos BOTAR MAIS COISA AQUI
        "2",  # Seleciona primeiro arquivo para download
        
        # Ver estatísticas
        "7",  # Exibir estatísticas

        "estatisticas.csv",  # Salvar estatisticas em arquivo
        
        # Sair
        "9"
    ]

    # Executa a sequência de comandos
    for cmd in test_sequence:
        peer1.expect(">")  # Espera pelo prompt
        print(f"\nEnviando comando: {cmd}")
        peer1.sendline(cmd)
        time.sleep(1)  # Espera processamento
        print(peer1.before.decode())  # Mostra output

    # Encerra os peers
    # peer1.close()
    peer2.close()
    peer4.close()

if __name__ == "__main__":
    run_automated_test()