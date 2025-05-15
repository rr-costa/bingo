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

class BingoGenerator:
    """Classe principal para geração e armazenamento de cartelas de bingo."""
    
    # Constantes de configuração
    NUM_FOLHAS = 10
    IMAGEM_FUNDO = "fundo_bingo.png"
    IMAGEM_FREE = "free.jpg"
    SAIDA_PDF = "cartelasBingo.pdf"
    DB_NAME = "bingo_cartelas.db"
    
    # Dimensões das cartelas
    LARGURA_CARTELA = 6.5 * cm
    ALTURA_CARTELA = 7.5 * cm
    
    # Cores das rodadas
    CORES_RODADAS = [
        "#FFFFFF",  # Branco
        "#ADD8E6",  # Azul claro
        "#FFFF99",  # Amarelo
        "#90EE90",  # Verde claro
        "#FFCCCB"   # Vermelho claro
    ]
    
    # Configurações de fonte
    FONTES = {
        'numeros': ('ComicSans', 'COMIC.TTF'),
        'bingo': ('KGHappy', 'KGHAPPY.ttf')
    }
    
    def __init__(self):
        """Inicializa o gerador de cartelas."""
        self.cartelas: List[List[Tuple]] = []
        self.usar_fundo = False
        self.usar_imagem_free = False
        self.img_fundo = None
        self.img_free = None
        self.conn = None
        self._carregar_fontes()


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
        """Gera o ID único no formato F{folha}C{posicao}."""
        return f"F{folha}C{posicao}"

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
        total_cartelas = self.NUM_FOLHAS * 5
        self.cartelas = []
        
        while len(self.cartelas) < total_cartelas:
            nova_cartela = self.gerar_cartela_unica()
            if nova_cartela not in self.cartelas:
                self.cartelas.append(nova_cartela)
        
        print(f"Total de cartelas geradas: {len(self.cartelas)}")

    def desenhar_cartela(self, c: canvas.Canvas, cartela: List[Tuple], 
                        x: float, y: float, indice: int):
        """Desenha uma única cartela na posição especificada."""
        # Fundo e borda
        c.setFillColor(HexColor(self.CORES_RODADAS[indice % 5]))
        c.rect(x, y, self.LARGURA_CARTELA, self.ALTURA_CARTELA, fill=1, stroke=0)
        c.setStrokeColor(HexColor("#000000"))
        c.setLineWidth(1)
        c.rect(x, y, self.LARGURA_CARTELA, self.ALTURA_CARTELA, fill=0, stroke=1)
        
        # Textos informativos
        c.setFillColor(HexColor("#000000"))
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(x + self.LARGURA_CARTELA - 0.2*cm, y + 0.2*cm, f"Rodada {indice % 5 + 1}")
        c.drawString(x + 0.2*cm, y + 0.2*cm, f"Prêmio a definir {indice % 5 + 1}")
        
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
        box_y = pos_y - box_height/2 + 0.1*cm
        
        c.setStrokeColor(HexColor("#000000"))
        c.roundRect(box_x, box_y, box_width, box_height, 5, fill=0, stroke=1)
        
        if conteudo == "FREE":
            if self.usar_imagem_free:
                c.drawImage(self.img_free, pos_x-0.5*cm, pos_y-0.4*cm, 
                          width=1*cm, height=1*cm)
            else:
                c.drawCentredString(pos_x, pos_y, "FREE")
        else:
            c.drawCentredString(pos_x, pos_y, str(conteudo))

    def criar_pdf(self):
        """Cria o PDF com todas as cartelas geradas e armazena no banco de dados."""
        c = canvas.Canvas(self.SAIDA_PDF, pagesize=A4)
        largura, altura = A4
        
        # Configurações de layout
        margem_superior = 13.5 * cm
        espacamento_h = 0.3 * cm
        espacamento_v = 0.3 * cm
        y1 = altura - margem_superior - self.ALTURA_CARTELA
        y2 = y1 - self.ALTURA_CARTELA - espacamento_v
        x_trio = (largura - 3*self.LARGURA_CARTELA - 2*espacamento_h) / 2
        x_dupla = (largura - 2*self.LARGURA_CARTELA - espacamento_h) / 2
        
        for folha in range(self.NUM_FOLHAS):
            # Desenha imagem de fundo
            if self.usar_fundo:
                c.drawImage(self.img_fundo, 0, 0, width=largura, height=altura)
            
            # Número da folha
            c.setFillColor(HexColor("#000000"))
            c.setFont("Helvetica-Bold", 14)
            c.drawRightString(largura - 1*cm, altura - 1*cm, f"Cartela {folha + 1}")
            
            # Desenha as 5 cartelas da folha
            for posicao in range(5):
                idx = folha * 5 + posicao
                if posicao < 3:  # Primeiras 3 cartelas (linha superior)
                    x = x_trio + posicao*(self.LARGURA_CARTELA + espacamento_h)
                    y = y1
                else:  # Últimas 2 cartelas (linha inferior)
                    x = x_dupla + (posicao-3)*(self.LARGURA_CARTELA + espacamento_h)
                    y = y2
                
                # Gera ID único e salva no banco
                id_cartela = self._gerar_id_cartela(folha + 1, posicao + 1)
                rodada = (posicao % 5) + 1
                premio = f"Prêmio teste {rodada}"
                
                self.desenhar_cartela(c, self.cartelas[idx], x, y, posicao)
            
            c.showPage()
        
        c.save()
        print(f"PDF gerado com sucesso: {self.SAIDA_PDF}")


    def executar(self):
        """Executa todo o processo de geração das cartelas."""
        try:
            self.carregar_imagens()
            self.gerar_todas_cartelas()
            self.criar_pdf()
        except Exception as e:
            print(f"Erro durante a execução: {str(e)}")
            import traceback
            traceback.print_exc()  # Isso mostrará o stack trace completo     

if __name__ == "__main__":
    gerador = BingoGenerator()
    gerador.executar()