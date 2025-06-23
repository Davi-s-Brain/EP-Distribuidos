import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import os
import warnings
import glob
from collections import defaultdict

def load_data():
    """Load and process statistics data"""
    stats = []
    for file in glob.glob("csv/estatistica*.csv"):
        df = pd.read_csv(file)
        stats.append(df)
    
    if not stats:
        raise ValueError("No statistics files found")
    
    df = pd.concat(stats, ignore_index=True)
    df['throughput'] = df['tamanho_arquivo'] / (df['tempo'] * 1024)  # KB/s
    return df

def calculate_statistics(data):
    """Calculate statistics for each configuration"""
    stats_dict = defaultdict(dict)
    
    for file_size in sorted(data['tamanho_arquivo'].unique()):
        file_data = data[data['tamanho_arquivo'] == file_size]
        
        for chunk_size in sorted(file_data['tamanho_chunk'].unique()):
            chunk_data = file_data[file_data['tamanho_chunk'] == chunk_size]
            
            if len(chunk_data) > 0:
                stats_dict[file_size][chunk_size] = {
                    'mean_time': chunk_data['tempo'].mean(),
                    'std_time': chunk_data['tempo'].std() if len(chunk_data) > 1 else 0,
                    'mean_throughput': chunk_data['throughput'].mean(),
                    'std_throughput': chunk_data['throughput'].std() if len(chunk_data) > 1 else 0,
                    'samples': 12
                }
    
    return stats_dict

def analyze_chunk_performance():
    """Analyze impact of chunk size on performance"""
    df = load_data()
    stats_dict = calculate_statistics(df)
    
    # Create plots directory
    os.makedirs("plots", exist_ok=True)
    
    # Set style
    sns.set_theme(style="whitegrid", font_scale=1.2)
    
    # 1. Throughput Analysis with Error Bars
    plt.figure(figsize=(12, 8))
    for file_size in sorted(stats_dict.keys()):
        chunk_sizes = []
        throughputs = []
        errors = []
        
        for chunk_size, stats in stats_dict[file_size].items():
            chunk_sizes.append(chunk_size)
            throughputs.append(stats['mean_throughput'])
            errors.append(stats['std_throughput'])
        
        plt.errorbar(chunk_sizes, throughputs, yerr=errors, 
                    label=f'{file_size/1024:.0f}KB', 
                    marker='o', capsize=5)
    
    plt.title('Throughput vs Tamanho do Chunk')
    plt.xlabel('Tamanho do Chunk (bytes)')
    plt.ylabel('Throughput (KB/s)')
    plt.legend(title='Tamanho do Arquivo')
    plt.savefig('plots/throughput_analysis.png')
    plt.close()
    
    # Print statistical analysis
    print("\nAnálise Estatística do Impacto do Tamanho do Chunk:")
    for file_size, chunks in stats_dict.items():
        print(f"\nTamanho do Arquivo: {file_size/1024:.0f}KB")
        print("\nMétricas por tamanho de chunk:")
        print(f"{'Chunk Size':<10} | {'Throughput (KB/s)':<20} | {'Tempo (s)':<15} | {'Amostras':<8}")
        print("-" * 60)
        
        for chunk_size, stats in chunks.items():
            print(f"{chunk_size:<10} | {stats['mean_throughput']:>8.2f} ± {stats['std_throughput']:>6.2f} | "
                  f"{stats['mean_time']:>6.3f} ± {stats['std_time']:>5.3f} | {stats['samples']:>8}")
    
    # 2. Efficiency Analysis
    plt.figure(figsize=(10, 6))
    for file_size in sorted(stats_dict.keys()):
        chunks = stats_dict[file_size]
        chunk_sizes = list(chunks.keys())
        times = [chunks[c]['mean_time'] for c in chunk_sizes]
        plt.plot(chunk_sizes, times, marker='o', label=f'{file_size/1024:.0f}KB')
    
    plt.title('Tempo de Download vs Tamanho do Chunk')
    plt.xlabel('Tamanho do Chunk (bytes)')
    plt.ylabel('Tempo médio (s)')
    plt.legend(title='Tamanho do Arquivo')
    plt.savefig('plots/download_time_analysis.png')
    plt.close()

if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        analyze_chunk_performance()