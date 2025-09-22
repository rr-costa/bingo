import sqlite3
from typing import List, Tuple, Optional, Dict, Any
import threading

class BingoDatabase:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_name: str = "bingo_cartelas.db"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.initialized = False
        return cls._instance
    
    def __init__(self, db_name: str = "bingo_cartelas.db"):
        if not self.initialized:
            self.db_name = db_name
            self.thread_local = threading.local()
            self._criar_tabela()
            self.initialized = True
    
    def get_connection(self):
        """Obtém uma conexão de banco de dados thread-safe"""
        if not hasattr(self.thread_local, "conn"):
            self.thread_local.conn = sqlite3.connect(self.db_name)
            self.thread_local.conn.row_factory = sqlite3.Row
        return self.thread_local.conn
    
    def _criar_tabela(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cartelas (
            id TEXT PRIMARY KEY,
            evento TEXT,
            folha INTEGER,
            posicao_na_folha INTEGER,
            numeros TEXT,
            rodada INTEGER,
            premio TEXT,
            utilizada INTEGER DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_evento ON cartelas (evento)
        ''')
        
        conn.commit()

    def limpar_cartelas_evento(self, evento: str) -> int:
        """Remove todas as cartelas de um evento específico"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        DELETE FROM cartelas WHERE evento = ?
        ''', (evento,))
        conn.commit()
        return cursor.rowcount

    def contar_cartelas_evento(self, evento: str) -> int:
        """Conta quantas cartelas existem para um evento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM cartelas WHERE evento = ?', (evento,))
        return cursor.fetchone()[0]

    def salvar_cartela(self, evento: str, id_cartela: str, folha: int, 
                      posicao: int, numeros: List[Tuple], rodada: int, premio: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        numeros_str = str(numeros)
        
        cursor.execute('''
        INSERT OR REPLACE INTO cartelas 
        (id, evento, folha, posicao_na_folha, numeros, rodada, premio)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (id_cartela, evento, folha, posicao, numeros_str, rodada, premio))
        
        conn.commit()

    def marcar_como_utilizada(self, id_cartela: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE cartelas SET utilizada = 1 WHERE id = ?
        ''', (id_cartela,))
        conn.commit()

    def obter_cartela(self, id_cartela: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM cartelas WHERE id = ?
        ''', (id_cartela,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def obter_todas_cartelas_evento(self, evento: str) -> List[List[Tuple]]:
        """Obtém todas as cartelas de um evento específico"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        SELECT numeros FROM cartelas WHERE evento = ?
        ''', (evento,))
        rows = cursor.fetchall()
        return [eval(row['numeros']) for row in rows] if rows else []

    def obter_cartelas_nao_utilizadas(self, rodada: int = None) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if rodada is not None:
            cursor.execute('''
            SELECT * FROM cartelas 
            WHERE utilizada = 0 AND rodada = ?
            ORDER BY folha, posicao_na_folha
            ''', (rodada,))
        else:
            cursor.execute('''
            SELECT * FROM cartelas 
            WHERE utilizada = 0
            ORDER BY folha, posicao_na_folha
            ''')
            
        return [dict(row) for row in cursor.fetchall()]

    def obter_eventos(self) -> List[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT evento FROM cartelas')
        return [row['evento'] for row in cursor.fetchall()]

    def obter_ultima_folha_evento(self, evento: str) -> Optional[int]:
        """Obtém o número da última folha usada no evento."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        SELECT MAX(folha) as ultima_folha FROM cartelas WHERE evento = ?
        ''', (evento,))
        row = cursor.fetchone()
        return row['ultima_folha'] if row and row['ultima_folha'] is not None else None

    def fechar_conexoes(self):
        """Fecha todas as conexões abertas"""
        if hasattr(self.thread_local, "conn"):
            self.thread_local.conn.close()
            del self.thread_local.conn