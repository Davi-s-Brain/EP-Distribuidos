import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

def setup_plot_style():
    """Configure plot styling"""
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'figure.dpi': 300
    })

def load_and_process_data():
    """Load and process statistics data"""
    stats = []
    for file in glob.glob("csv_peers/estatistica*.csv"):
        try:
            df = pd.read_csv(file)
            stats.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
            continue
    
    if not stats:
        raise ValueError("No statistics files found")
    
    df = pd.concat(stats, ignore_index=True)
    
    # Convert sizes to KB for better readability
    df['tamanho_arquivo_kb'] = df['tamanho_arquivo'] / 1024
    return df

def create_plots():
    """Generate all comparison plots"""
    try:
        df = load_and_process_data()
        setup_plot_style()
        
        # Create figure with 2x2 subplots
        fig = plt.figure(figsize=(15, 15))
        
        # Plot 1: Download Time vs Chunk Size
        ax1 = plt.subplot(221)
        sns.lineplot(data=df, x='tamanho_chunk', y='tempo',
                    hue='tamanho_arquivo_kb', marker='o',
                    linewidth=2.5, markersize=8)
        ax1.set_title('Tempo de Download vs Tamanho do Chunk')
        ax1.set_xlabel('Tamanho do Chunk (bytes)')
        ax1.set_ylabel('Tempo (segundos)')
        ax1.legend(title='Tamanho Arquivo (KB)')
        
        # Plot 2: Download Time vs Number of Peers
        ax2 = plt.subplot(222)
        sns.lineplot(data=df, x='num_peers', y='tempo',
                    hue='tamanho_arquivo_kb', marker='o',
                    linewidth=2.5, markersize=8)
        ax2.set_title('Tempo de Download vs Número de Peers')
        ax2.set_xlabel('Número de Peers')
        ax2.set_ylabel('Tempo (segundos)')
        ax2.legend(title='Tamanho Arquivo (KB)')
        
        # Plot 3: Standard Deviation vs Chunk Size
        ax3 = plt.subplot(223)
        sns.lineplot(data=df, x='tamanho_chunk', y='desvio_padrao',
                    hue='tamanho_arquivo_kb', marker='o',
                    linewidth=2.5, markersize=8)
        ax3.set_title('Desvio Padrão vs Tamanho do Chunk')
        ax3.set_xlabel('Tamanho do Chunk (bytes)')
        ax3.set_ylabel('Desvio Padrão')
        ax3.legend(title='Tamanho Arquivo (KB)')
        
        # Plot 4: Standard Deviation vs Number of Peers
        ax4 = plt.subplot(224)
        sns.lineplot(data=df, x='num_peers', y='desvio_padrao',
                    hue='tamanho_arquivo_kb', marker='o',
                    linewidth=2.5, markersize=8)
        ax4.set_title('Desvio Padrão vs Número de Peers')
        ax4.set_xlabel('Número de Peers')
        ax4.set_ylabel('Desvio Padrão')
        ax4.legend(title='Tamanho Arquivo (KB)')
        
        # Adjust layout and save
        plt.tight_layout()
        os.makedirs("plots", exist_ok=True)
        plt.savefig('plots/performance_comparison.png', bbox_inches='tight')
        plt.close()
        
        print("Plots generated successfully in plots/performance_comparison.png")
        
    except Exception as e:
        print(f"Error generating plots: {e}")

if __name__ == "__main__":
    create_plots()