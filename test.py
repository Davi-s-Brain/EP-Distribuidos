import subprocess
import time
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os

def start_peer(port, vizinhos_file, test_dir):
    print(f"Starting peer at port {port}")
    process = subprocess.Popen([
        "python3", "main.py",
        f"127.0.0.1:{port}",
        vizinhos_file,
        test_dir
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)  # Wait for peer to initialize
    return process

def run_single_test(file_name, chunk_size):
    print(f"Running test for {file_name} with chunk size {chunk_size}")
    try:
        # Start peers 2 and 4 first (they will host the files)
        print("Starting peer 2 and 4...")
        peer2 = start_peer(8002, "vizinhos/v2_vizinhos.txt", "./teste")
        peer4 = start_peer(8004, "vizinhos/v4_vizinhos.txt", "./teste")
        time.sleep(2)  # Wait for peers to initialize

        # Start the main peer (peer 1) with test parameters
        print("Starting peer 1 (main peer)...")
        cmd = [
            "python3", "main.py",
            "127.0.0.1:8001",
            "vizinhos/v1_vizinhos.txt",
            "./teste",
            "--test",
            file_name,
            str(chunk_size)
        ]
        
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True,
                              timeout=30)  # Add timeout to prevent hanging
        
        # Cleanup peers
        peer2.terminate()
        peer4.terminate()
        
        # Parse and return results
        for line in result.stdout.split('\n'):
            if line.startswith('TEST_RESULT'):
                _, fname, chunk, duration = line.split(';')
                return float(duration)
                
    except Exception as e:
        print(f"Error during test: {str(e)}")
        return None
    finally:
        # Ensure peers are terminated
        try:
            peer2.terminate()
            peer4.terminate()
        except:
            pass

def run_test_sequence():
    results = []
    # chunk_sizes = [1, 256, 512]
    # file_sizes = [1, 10, 100]
    chunk_sizes = [1, 256]
    file_sizes = [1, 10]
    repeats = 5

    # Ensure test files exist
    for size in file_sizes:
        file_path = f"./teste/{size}KB.txt"
        if not os.path.exists(file_path):
            print(f"Creating test file {file_path}")
            os.system(f"dd if=/dev/urandom of={file_path} bs=1K count={size}")

    for chunk_size in chunk_sizes:
        for file_size in file_sizes:
            file_name = f"{file_size}KB.txt"
            print(f"\nTesting {file_name} with chunk size {chunk_size}")
            
            for i in range(repeats):
                print(f"  Iteration {i+1}/{repeats}")
                duration = run_single_test(file_name, chunk_size)
                
                if duration is not None:
                    results.append({
                        'file_size': file_size,
                        'chunk_size': chunk_size,
                        'duration': duration,
                        'iteration': i
                    })
                time.sleep(1)  # Wait between tests

    return pd.DataFrame(results)

if __name__ == "__main__":
    print("Starting automated tests...")
    
    # Create directories if they don't exist
    os.makedirs("./teste", exist_ok=True)
    os.makedirs("./vizinhos", exist_ok=True)
    
    # Create neighbor files if they don't exist
    if not os.path.exists("vizinhos/v1_vizinhos.txt"):
        with open("vizinhos/v1_vizinhos.txt", "w") as f:
            f.write("127.0.0.1:8002\n127.0.0.1:8004")
    if not os.path.exists("vizinhos/v2_vizinhos.txt"):
        with open("vizinhos/v2_vizinhos.txt", "w") as f:
            f.write("127.0.0.1:8001\n127.0.0.1:8004")
    if not os.path.exists("vizinhos/v4_vizinhos.txt"):
        with open("vizinhos/v4_vizinhos.txt", "w") as f:
            f.write("127.0.0.1:8001\n127.0.0.1:8002")
    
    results_df = run_test_sequence()
    
    if not results_df.empty:
        # Plot results
        plt.figure(figsize=(12, 6))
        sns.boxplot(x='chunk_size', y='duration', hue='file_size', data=results_df)
        plt.title('Download Duration by Chunk Size and File Size')
        plt.xlabel('Chunk Size (bytes)')
        plt.ylabel('Duration (seconds)')
        plt.savefig('test_results.png')
        
        # Save raw data
        results_df.to_csv('test_results.csv', index=False)
        print("Tests completed. Results saved to test_results.csv and test_results.png")
    else:
        print("No results were collected. Please check for errors above.")