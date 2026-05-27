#!/usr/bin/env python3
"""
Script para consultar cartelas de reforço no banco de dados.

Uso:
    python listar_reforcos.py "Nome do Evento"
    python listar_reforcos.py "54 Festa SA"
"""

from database import BingoDatabase
import argparse

def main():
    parser = argparse.ArgumentParser(
        description='Listar Cartelas de Reforço de um Evento'
    )
    
    parser.add_argument('nome_evento', type=str,
                       help='Nome do evento de bingo')
    
    args = parser.parse_args()
    
    db = BingoDatabase()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("=" * 70)
    print(f"CARTELAS DE REFORÇO - {args.nome_evento}")
    print("=" * 70)
    
    cursor.execute('''
        SELECT id, posicao_na_folha, numeros
        FROM cartelas 
        WHERE evento = ? AND tipo_cartela = 'reforco'
        ORDER BY posicao_na_folha
    ''', (args.nome_evento,))
    
    reforcos = cursor.fetchall()
    
    if not reforcos:
        print(f"Nenhuma cartela de reforço encontrada para '{args.nome_evento}'")
        print("=" * 70)
        return
    
    for i, row in enumerate(reforcos, 1):
        print(f"\n#{row['posicao_na_folha']}")
        print(f"  ID: {row['id']}")
        print(f"  PDF: output/cartela_reforco_{args.nome_evento.replace(' ', '_')}_{row['posicao_na_folha']}.pdf")
        
    print()
    print("=" * 70)
    print(f"Total: {len(reforcos)} cartela(s) de reforço")
    print("=" * 70)

if __name__ == "__main__":
    main()
