#!/usr/bin/env python3
"""
Script CLI para gerar cartelas de reforço de um evento de bingo.

Uso:
    python gerar_reforco.py "Nome do Evento"
    python gerar_reforco.py "54 Festa SA"
"""

from reforco_bingo import ReforcoGenerator
import argparse

def main():
    parser = argparse.ArgumentParser(
        description='Gerador de Cartelas de Reforço de Bingo',
        epilog='Exemplos:\n'
               '  python gerar_reforco.py "54 Festa SA"\n'
               '  python gerar_reforco.py "Bingo Beneficente"',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('nome_evento', type=str,
                       help='Nome do evento de bingo')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("GERADOR DE CARTELAS DE REFORÇO DE BINGO")
    print("=" * 60)
    print(f"Evento: {args.nome_evento}")
    print()
    
    gerador = ReforcoGenerator(nome_evento=args.nome_evento)
    resultado = gerador.executar()
    
    if resultado:
        print()
        print("=" * 60)
        print("Cartela de reforço gerada com sucesso!")
        print(f"Arquivo: {resultado}")
        print("=" * 60)
    else:
        print("\nErro ao gerar cartela de reforço!")
        exit(1)

if __name__ == "__main__":
    main()
