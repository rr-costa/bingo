import os
import random
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from PIL import Image
from typing import List, Tuple, Optional
from database import BingoDatabase

class BingoGenerator:
    """Classe principal para geração e armazenamento de cartelas de bingo."""
    
    # Constantes de configuração
    IMAGEM_FUNDO = "fundo_bingo.png"
    IMAGEM_FREE = "free.jpg"
    DB_NAME = "bingo_cartelas.db"
    
    # Configurações padrão
    DEFAULT_CARTELAS_POR_FOLHA = 5
    DEFAULT_NUM_FOLHAS = 10
    
    # Dimensões das cartelas
    LARGURA_CARTELA = 6.5 * cm
    ALTURA_CARTELA = 7.5 * cm
    
    # Cores das rodadas
    CORES_RODADAS = [
        "#90EE90",  # Verde claro
        "#FAA500",   # Laranja
        "#ADD8E6",  # Azul claro
        "#FFFF99",  # Amarelo
        "#FFCCCB",  # Vermelho claro
        "#FFFFFF"   # Branco
    ]
    
    # Configurações de fonte
    FONTES = {
        'numeros': ('ComicSans', 'COMIC.TTF'),
        'bingo': ('KGHappy', 'KGHAPPY.ttf')
    }
    
    def __init__(self, nome_evento: str = "Evento Padrão", 
                 cartelas_por_folha: int = DEFAULT_CARTELAS_POR_FOLHA,
                 num_folhas: int = DEFAULT_NUM_FOLHAS,
                 append: bool = False):
        """Inicializa o gerador de cartelas.
        
        Args:
            nome_evento: Nome do evento de bingo
            cartelas_por_folha: Quantidade de cartelas por folha (1-6)
            num_folhas: Número total de folhas a gerar
            append: Se True, adiciona ao evento existente em vez de recriar
        """
        self.cartelas: List[List[Tuple]] = []
        self.usar_fundo = False
        self.usar_imagem_free = False
        self.img_fundo = None
        self.img_free = None
        self.nome_evento = nome_evento
        self.cartelas_por_folha = min(max(1, cartelas_por_folha), 6)  # Limita entre 1 e 6
        self.num_folhas = max(1, num_folhas)  # Pelo menos 1 folha
        self.append_mode = append
        self.db = BingoDatabase(self.DB_NAME)
        
        # Só limpa cartelas existentes se não for modo append
        if not self.append_mode:
            # Verifica se já existem cartelas para o evento
            count = self.db.contar_cartelas_evento(self.nome_evento)
            if count > 0:
                # Solicita confirmação do usuário
                resposta = input(f"Existem {count} cartelas para o evento '{self.nome_evento}'. Deseja excluí-las? (s/n): ").strip().lower()
                if resposta != 's':
                    print("Operação cancelada pelo usuário.")
                    exit(0)
            
            removidas = self.db.limpar_cartelas_evento(self.nome_evento)
            print(f"Removidas {removidas} cartelas existentes do evento '{self.nome_evento}'")
        else:
            print(f"Modo acréscimo: novas cartelas serão adicionadas ao evento '{self.nome_evento}'")
        
        self._carregar_fontes()
        self._calcular_layout()

    def _calcular_layout(self):
        """Calcula o layout das cartelas na folha baseado no número por folha."""
        if self.cartelas_por_folha <= 3:
            # 1 linha com todas as cartelas
            self.colunas_por_linha = self.cartelas_por_folha
            self.linhas_por_folha = 1
        else:
            # 2 linhas (3 cartelas na primeira, o resto na segunda)
            self.colunas_por_linha = 3
            self.linhas_por_folha = 2
        
        # Espaçamento entre cartelas
        self.espacamento_h = 0.3 * cm
        self.espacamento_v = 0.3 * cm
        
        # Margem superior ajustável
        self.margem_superior = 8.5 * cm if self.cartelas_por_folha > 3 else 7.5 * cm

    def _carregar_fontes(self):
        """Registra as fontes personalizadas."""
        for nome, arquivo in self.FONTES.values():
            try:
                pdfmetrics.registerFont(TTFont(nome, arquivo))
            except:
                print(f"Fonte {nome} não encontrada. Usando fonte padrão.")

    def gerar_cartela_unica(self) -> List[Tuple]:
        """Gera uma cartela 5x5 única com FREE no centro da coluna N."""
        cartela = []
        for i in range(5):
            if i == 2:  # Coluna N
                numeros = random.sample(range(31, 46), 4)
                numeros.insert(2, "FREE")
            else:
                numeros = random.sample(range(1 + i*15, 16 + i*15), 5)
            cartela.append(numeros)
        return list(zip(*cartela))

    def _gerar_id_cartela(self, folha: int, posicao: int) -> str:
        """Gera o ID único no formato EVENTO_F{folha}C{posicao}."""
        return f"{self.nome_evento}_F{folha}C{posicao}"

    def _obter_proxima_folha(self) -> int:
        """Obtém o número da próxima folha disponível para o evento."""
        ultima_folha = self.db.obter_ultima_folha_evento(self.nome_evento)
        return ultima_folha + 1 if ultima_folha is not None else 1

    def carregar_imagens(self):
        """Carrega e prepara as imagens necessárias."""
        # Carrega imagem de fundo
        try:
            img = Image.open(self.IMAGEM_FUNDO)
            self.img_fundo = ImageReader(img.resize((int(A4[0]), int(A4[1]))))
            self.usar_fundo = True
        except Exception as e:
            print(f"Imagem de fundo não encontrada. Erro: {e}")

        # Carrega imagem FREE
        try:
            img = Image.open(self.IMAGEM_FREE)
            self.img_free = ImageReader(img.resize((int(0.8*cm), int(0.8*cm))))
            self.usar_imagem_free = True
        except Exception as e:
            print(f"Imagem FREE não encontrada. Erro: {e}")

    def gerar_todas_cartelas(self):
        """Gera todas as cartelas necessárias, garantindo que sejam únicas."""
        print("Gerando cartelas únicas...")
        total_cartelas = self.num_folhas * self.cartelas_por_folha
        self.cartelas = []
        
        # Se for modo append, verifica cartelas existentes para evitar duplicatas
        cartelas_existentes = []
        if self.append_mode:
            cartelas_existentes = self.db.obter_todas_cartelas_evento(self.nome_evento)
            print(f"Encontradas {len(cartelas_existentes)} cartelas existentes no evento")
        
        while len(self.cartelas) < total_cartelas:
            nova_cartela = self.gerar_cartela_unica()
            
            # Verifica se a cartela já existe (tanto nas novas quanto nas existentes)
            if nova_cartela not in self.cartelas and nova_cartela not in cartelas_existentes:
                self.cartelas.append(nova_cartela)
        
        print(f"Total de novas cartelas geradas: {len(self.cartelas)}")

    def desenhar_cartela(self, c: canvas.Canvas, cartela: List[Tuple], 
                        x: float, y: float, indice: int):
        """Desenha uma única cartela na posição especificada."""
        # Fundo e borda
        c.setFillColor(HexColor(self.CORES_RODADAS[indice % len(self.CORES_RODADAS)]))
        c.rect(x, y, self.LARGURA_CARTELA, self.ALTURA_CARTELA, fill=1, stroke=0)
        c.setStrokeColor(HexColor("#000000"))
        c.setLineWidth(1)
        c.rect(x, y, self.LARGURA_CARTELA, self.ALTURA_CARTELA, fill=0, stroke=1)
        
        # Textos informativos
        c.setFillColor(HexColor("#000000"))
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(x + self.LARGURA_CARTELA - 0.2*cm, y + 0.2*cm, f"Rodada {(indice % len(self.CORES_RODADAS)) + 1}")
        #c.drawString(x + 0.2*cm, y + 0.2*cm, f"Prêmio teste {indice % 5 + 1}")
        
        # Cabeçalho BINGO
        c.setFont(self.FONTES['bingo'][0], 17)
        for col, letra in enumerate("BINGO"):
            c.drawCentredString(
                x + col*(self.LARGURA_CARTELA/5) + (self.LARGURA_CARTELA/10),
                y + self.ALTURA_CARTELA - 0.9*cm,
                letra
            )
        
        # Números
        c.setFont(self.FONTES['numeros'][0], 16)
        for linha in range(5):
            for col in range(5):
                self._desenhar_numero(c, cartela[linha][col], x, y, linha, col)

    def _desenhar_numero(self, c: canvas.Canvas, conteudo, x: float, y: float, 
                        linha: int, col: int):
        """Desenha um número ou FREE na posição especificada da cartela."""
        pos_x = x + col*(self.LARGURA_CARTELA/5) + (self.LARGURA_CARTELA/10)
        pos_y = y + self.ALTURA_CARTELA - 2*cm - linha*1.1*cm
        
        # Quadrado arredondado
        box_width = 1*cm
        box_height = 1*cm
        box_x = pos_x - box_width/2
        box_y = pos_y - box_height/2 + 0.2*cm
        
        c.setStrokeColor(HexColor("#000000"))
        c.roundRect(box_x, box_y, box_width, box_height, 5, fill=0, stroke=1)
        
        if conteudo == "FREE":
            if self.usar_imagem_free:
                c.drawImage(self.img_free, pos_x-0.5*cm, pos_y-0.3*cm, 
                          width=1*cm, height=1*cm)
            else:
                c.drawCentredString(pos_x, pos_y, "X")
        else:
            c.drawCentredString(pos_x, pos_y, str(conteudo))

    def _calcular_posicao_cartela(self, posicao: int, largura_pagina: float) -> Tuple[float, float]:
        """Calcula a posição x,y de uma cartela baseado em sua posição na folha."""
        if self.linhas_por_folha == 1:
            # Todas na mesma linha
            x = (largura_pagina - (self.cartelas_por_folha * self.LARGURA_CARTELA) - 
                ((self.cartelas_por_folha - 1) * self.espacamento_h)) / 2
            x += posicao * (self.LARGURA_CARTELA + self.espacamento_h)
            y = self.margem_superior + 1 * cm
        else:
            # Duas linhas (3 na primeira, resto na segunda)
            if posicao < 3:
                x = (largura_pagina - (3 * self.LARGURA_CARTELA) - (2 * self.espacamento_h)) / 2
                x += posicao * (self.LARGURA_CARTELA + self.espacamento_h)
                y = self.margem_superior
            else:
                pos = posicao - 3
                cartelas_linha = self.cartelas_por_folha - 3
                x = (largura_pagina - (cartelas_linha * self.LARGURA_CARTELA) - 
                    ((cartelas_linha - 1) * self.espacamento_h)) / 2
                x += pos * (self.LARGURA_CARTELA + self.espacamento_h)
                y = self.margem_superior - self.ALTURA_CARTELA - self.espacamento_v
        
        return x, y

    def criar_pdf(self):
        """Cria o PDF com todas as cartelas geradas e armazena no banco de dados."""
        nome_arquivo = f"cartelas_{self.nome_evento.replace(' ', '_')}.pdf"
        
        # Modo append: gera novo arquivo com sufixo numérico
        if self.append_mode:
            contador = 1
            while os.path.exists(nome_arquivo):
                base, ext = os.path.splitext(nome_arquivo)
                nome_arquivo = f"{base}_{contador}{ext}"
                contador += 1
        
        c = canvas.Canvas(nome_arquivo, pagesize=A4)
        largura, altura = A4
        
        # Determina o número da primeira folha
        folha_inicial = 1
        if self.append_mode:
            folha_inicial = self._obter_proxima_folha()
        
        for folha in range(self.num_folhas):
            folha_atual = folha_inicial + folha
            
            # Desenha imagem de fundo
            if self.usar_fundo:
                c.drawImage(self.img_fundo, 0, 0, width=largura, height=altura)
            
            # Número da folha
            c.setFillColor(HexColor("#000000"))
            c.setFont("Helvetica-Bold", 14)
            c.drawRightString(largura - 1*cm, altura - 1*cm, f"Cartela {folha_atual}")
            
            # Desenha as cartelas da folha
            for posicao in range(self.cartelas_por_folha):
                idx = folha * self.cartelas_por_folha + posicao
                x, y = self._calcular_posicao_cartela(posicao, largura)
                
                # Gera ID único e salva no banco
                id_cartela = self._gerar_id_cartela(folha_atual, posicao + 1)
                rodada = (posicao % len(self.CORES_RODADAS)) + 1
                premio = ""
                
                self.db.salvar_cartela(
                    evento=self.nome_evento,
                    id_cartela=id_cartela,
                    folha=folha_atual,
                    posicao=posicao + 1,
                    numeros=self.cartelas[idx],
                    rodada=rodada,
                    premio=premio
                )

                self.desenhar_cartela(c, self.cartelas[idx], x, y, posicao)
            
            c.showPage()
        
        c.save()
        print(f"PDF {'gerado' if not self.append_mode else 'adicionado'} com sucesso: {nome_arquivo}")

    def executar(self):
        """Executa todo o processo de geração das cartelas."""
        try:
            self.carregar_imagens()
            self.gerar_todas_cartelas()
            self.criar_pdf()
        except Exception as e:
            print(f"Erro durante a execução: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerador de Cartelas de Bingo')
    parser.add_argument('nome_evento', type=str, nargs='?', default="Evento Padrão",
                       help='Nome do evento de bingo')
    parser.add_argument('-c', '--cartelas_por_folha', type=int, 
                       default=BingoGenerator.DEFAULT_CARTELAS_POR_FOLHA,
                       help='Número de cartelas por folha (1-6)')
    parser.add_argument('-f', '--folhas', type=int, 
                       default=BingoGenerator.DEFAULT_NUM_FOLHAS,
                       help='Número total de folhas a gerar')
    parser.add_argument('-a', '--append', action='store_true',
                       help='Adiciona novas cartelas a um evento existente sem apagar as antigas')
    
    args = parser.parse_args()
    
    gerador = BingoGenerator(
        nome_evento=args.nome_evento,
        cartelas_por_folha=args.cartelas_por_folha,
        num_folhas=args.folhas,
        append=args.append
    )
    gerador.executar()