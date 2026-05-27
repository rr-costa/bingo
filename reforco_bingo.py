import os
import random
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from PIL import Image
from typing import List, Tuple
from database import BingoDatabase

class ReforcoGenerator:
    """Classe para geração de cartelas de reforço em A6."""
    
    # Constantes de configuração
    IMAGEM_FUNDO = "static/images/fundo_bingo.png"
    IMAGEM_FREE = "static/images/free.png"
    DB_NAME = "output/bingo_cartelas.db"
    
    # Dimensões (A6 = 10.5 x 14.8 cm)
    # Cartela ocupará a maior parte da página
    LARGURA_CARTELA = 9.5 * cm
    ALTURA_CARTELA = 10 * cm  # Reduzida para deixar mais espaço do fundo
    
    # Cor fixa para reforço (você pode mudar se quiser)
    COR_REFORCO = "#FFE4B5"  # Moccasin/Bege claro
    
    # Configurações de fonte
    FONTES = {
        'numeros': ('ComicSans', 'static/fonts/COMIC.TTF'),
        'bingo': ('KGHappy', 'static/fonts/KGHAPPY.ttf')
    }
    
    def __init__(self, nome_evento: str = "Evento Padrão"):
        """Inicializa o gerador de cartela de reforço.
        
        Args:
            nome_evento: Nome do evento de bingo
        """
        self.nome_evento = nome_evento
        self.cartela = None
        self.usar_fundo = False
        self.usar_imagem_free = False
        self.img_fundo = None
        self.img_free = None
        self.db = BingoDatabase(self.DB_NAME)
        
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
    
    def _gerar_id_cartela(self, numero_reforco: int) -> str:
        """Gera o ID único no formato EVENTO_REFORÇO_{numero}."""
        return f"{self.nome_evento}_REFORCO_{numero_reforco}"
    
    def _obter_proximo_numero_reforco(self) -> int:
        """Obtém o número sequencial para a próxima cartela de reforço."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT MAX(CAST(SUBSTR(id, INSTR(id, '_REFORCO_') + 9) AS INTEGER)) as max_num
        FROM cartelas 
        WHERE evento = ? AND tipo_cartela = 'reforco'
        ''', (self.nome_evento,))
        
        resultado = cursor.fetchone()
        max_num = resultado['max_num'] if resultado and resultado['max_num'] else 0
        return max_num + 1
    
    def carregar_imagens(self):
        """Carrega e prepara as imagens necessárias."""
        # Carrega imagem de fundo
        try:
            img = Image.open(self.IMAGEM_FUNDO)
            # Redimensiona para A6
            self.img_fundo = ImageReader(img.resize((int(A6[0]), int(A6[1]))))
            self.usar_fundo = True
        except Exception as e:
            print(f"Imagem de fundo não encontrada. Erro: {e}")
        
        # Carrega imagem FREE
        try:
            img = Image.open(self.IMAGEM_FREE)
            self._img_free_pil = img.convert('RGBA')
            self.img_free = ImageReader(img.resize((int(1.2*cm), int(1.2*cm))))
            self.usar_imagem_free = True
        except Exception as e:
            print(f"Imagem FREE não encontrada. Erro: {e}")
    
    def desenhar_cartela(self, c: canvas.Canvas, cartela: List[Tuple], numero_reforco: int):
        """Desenha a cartela de reforço na página A6."""
        largura, altura = A6
        
        # Centraliza a cartela na página A6, mas alinha embaixo com margem pequena
        x = (largura - self.LARGURA_CARTELA) / 2
        # Deixa mais espaço em cima (fundo) e alinha embaixo com 0.5cm de margem
        y = altura - self.ALTURA_CARTELA - 0.5*cm
        
        # Fundo e borda da cartela
        c.setFillColor(HexColor(self.COR_REFORCO))
        c.rect(x, y, self.LARGURA_CARTELA, self.ALTURA_CARTELA, fill=1, stroke=0)
        c.setStrokeColor(HexColor("#000000"))
        c.setLineWidth(2)
        c.rect(x, y, self.LARGURA_CARTELA, self.ALTURA_CARTELA, fill=0, stroke=1)
        
        # Texto "Cartela {numero}" no canto superior direito (estilo gerador principal)
        c.setFillColor(HexColor("#000000"))
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(x + self.LARGURA_CARTELA - 0.2*cm, y + self.ALTURA_CARTELA - 0.35*cm, f"Cartela {numero_reforco}")
        
        # Cabeçalho BINGO com fonte maior
        c.setFont(self.FONTES['bingo'][0], 22)
        for col, letra in enumerate("BINGO"):
            c.drawCentredString(
                x + col*(self.LARGURA_CARTELA/5) + (self.LARGURA_CARTELA/10),
                y + self.ALTURA_CARTELA - 1.0*cm,
                letra
            )
        
        # Números
        c.setFont(self.FONTES['numeros'][0], 20)
        for linha in range(5):
            for col in range(5):
                self._desenhar_numero(c, cartela[linha][col], x, y, linha, col)
    
    def _desenhar_numero(self, c: canvas.Canvas, conteudo, x: float, y: float, 
                        linha: int, col: int):
        """Desenha um número ou FREE na cartela de reforço."""
        pos_x = x + col*(self.LARGURA_CARTELA/5) + (self.LARGURA_CARTELA/10)
        # Ajustado para nova altura e posicionamento
        pos_y = y + self.ALTURA_CARTELA - 1.9*cm - linha*1.6*cm
        
        # Quadrado arredondado maior para A6
        box_width = 1.5*cm
        box_height = 1.5*cm
        box_x = pos_x - box_width/2
        box_y = pos_y - box_height/2 + 0.2*cm
        
        c.setStrokeColor(HexColor("#000000"))
        c.setLineWidth(1.5)
        c.roundRect(box_x, box_y, box_width, box_height, 8, fill=0, stroke=1)
        
        if conteudo == "FREE":
            if self.usar_imagem_free and hasattr(self, '_img_free_pil'):
                try:
                    size_px = (int(1.2*cm), int(1.2*cm))
                    rgb = tuple(int(self.COR_REFORCO.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                    base = Image.new('RGBA', size_px, rgb + (255,))
                    img_free_resized = self._img_free_pil.resize(size_px)
                    base.paste(img_free_resized, (0, 0), img_free_resized)
                    img_reader = ImageReader(base)
                    c.drawImage(img_reader, pos_x-0.6*cm, pos_y-0.35*cm, width=1.2*cm, height=1.2*cm, mask='auto')
                except Exception:
                    c.drawCentredString(pos_x, pos_y, "FREE")
            else:
                c.drawCentredString(pos_x, pos_y, "FREE")
        else:
            c.drawCentredString(pos_x, pos_y, str(conteudo))
    
    def criar_pdf(self, numero_reforco: int):
        """Cria o PDF com a cartela de reforço."""
        nome_arquivo = f"output/cartela_reforco_{self.nome_evento.replace(' ', '_')}_{numero_reforco}.pdf"
        
        # Cria novo PDF em tamanho A6
        c = canvas.Canvas(nome_arquivo, pagesize=A6)
        largura, altura = A6
        
        # Desenha imagem de fundo
        if self.usar_fundo:
            c.drawImage(self.img_fundo, 0, 0, width=largura, height=altura)
        
        # Desenha a cartela (passando o número)
        self.desenhar_cartela(c, self.cartela, numero_reforco)
        
        c.showPage()
        c.save()
        
        print(f"PDF de reforço gerado com sucesso: {nome_arquivo}")
        return nome_arquivo
    
    def executar(self) -> str:
        """Executa todo o processo de geração da cartela de reforço.
        
        Returns:
            Nome do arquivo PDF gerado
        """
        try:
            # Gera a cartela
            print("Gerando cartela de reforço...")
            self.cartela = self.gerar_cartela_unica()
            
            # Carrega imagens
            self.carregar_imagens()
            
            # Obtém número sequencial
            numero_reforco = self._obter_proximo_numero_reforco()
            
            # Cria o PDF
            nome_arquivo = self.criar_pdf(numero_reforco)
            
            # Salva no banco de dados
            id_cartela = self._gerar_id_cartela(numero_reforco)
            self.db.salvar_cartela(
                evento=self.nome_evento,
                id_cartela=id_cartela,
                folha=0,  # Reforço não usa folha
                posicao=numero_reforco,
                numeros=self.cartela,
                rodada=0,  # Reforço não usa rodada
                premio="",
                tipo_cartela='reforco'
            )
            
            print(f"Cartela de reforço #{numero_reforco} salva no banco de dados")
            
            return nome_arquivo
            
        except Exception as e:
            print(f"Erro durante a execução: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerador de Cartelas de Reforço de Bingo')
    parser.add_argument('nome_evento', type=str, nargs='?', default="Evento Padrão",
                       help='Nome do evento de bingo')
    
    args = parser.parse_args()
    
    gerador = ReforcoGenerator(nome_evento=args.nome_evento)
    gerador.executar()
