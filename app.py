from flask import Flask, render_template, request, jsonify
from database import BingoDatabase
import ast
import atexit

app = Flask(__name__)
db = BingoDatabase()

@atexit.register
def shutdown():
    db.fechar_conexoes()

@app.route('/')
def index():
    eventos = db.obter_eventos()
    return render_template('index.html', eventos=eventos)

@app.route('/get_eventos', methods=['GET'])
def get_eventos():
    eventos = db.obter_eventos()
    return jsonify(eventos)

@app.route('/iniciar_rodada', methods=['POST'])
def iniciar_rodada():
    try:
        evento = request.form['evento']
        rodada = int(request.form['rodada'])
        
        cartelas = db.obter_cartelas_nao_utilizadas(rodada)
        
        cartelas_formatadas = []
        for cartela in cartelas:
            try:
                numeros = ast.literal_eval(cartela['numeros'])
                cartelas_formatadas.append({
                    'id': cartela['id'],
                    'folha': cartela['folha'],
                    'posicao': cartela['posicao_na_folha'],
                    'numeros': numeros
                })
            except Exception as e:
                print(f"Erro na cartela {cartela['id']}: {str(e)}")
                continue

        return jsonify({'status': 'success', 'cartelas': cartelas_formatadas})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/verificar_vencedor', methods=['POST'])
def verificar_vencedor():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request deve ser JSON'}), 415
            
        dados = request.get_json()
        numeros_sorteados = dados['numeros_sorteados']
        cartelas = dados['cartelas']
        
        resultados = {
            'quatro_cantos': [],
            'linhas': [],
            'colunas': [],
            'diagonais': [],
            'cartela_cheia': [],
            'status': {'quentes': 0, 'mornas': 0}
        }

        for cartela in cartelas:
            numeros = cartela['numeros']
            folha = cartela['folha']
            
            # Verificar 4 cantos
            cantos = [
                numeros[0][0], numeros[0][4],  # B1, B5
                numeros[4][0], numeros[4][4]    # O1, O5
            ]
            if all(str(c) in map(str, numeros_sorteados) or c == "FREE" for c in cantos):
                resultados['quatro_cantos'].append(folha)
            
            # Verificar linhas, colunas e diagonais
            for i in range(5):
                linha = numeros[i]
                if all(str(n) in map(str, numeros_sorteados) or n == "FREE" for n in linha):
                    resultados['linhas'].append({'folha': folha, 'posicao': f'Linha {i+1}'})
                
                coluna = [numeros[j][i] for j in range(5)]
                if all(str(n) in map(str, numeros_sorteados) or n == "FREE" for n in coluna):
                    resultados['colunas'].append({'folha': folha, 'posicao': f'Coluna {chr(65+i)}'})
            
            diagonal1 = [numeros[i][i] for i in range(5)]
            diagonal2 = [numeros[i][4-i] for i in range(5)]
            if all(str(n) in map(str, numeros_sorteados) or n == "FREE" for n in diagonal1):
                resultados['diagonais'].append({'folha': folha, 'posicao': 'Diagonal Principal'})
            if all(str(n) in map(str, numeros_sorteados) or n == "FREE" for n in diagonal2):
                resultados['diagonais'].append({'folha': folha, 'posicao': 'Diagonal Secundária'})

            # Verificar cartela cheia e contagem quente/morna - CORREÇÃO AQUI
            numeros_validos = [num for linha in numeros for num in linha if num != "FREE"]
            numeros_faltando = sum(1 for num in numeros_validos if str(num) not in map(str, numeros_sorteados))
            
            if numeros_faltando == 0:
                resultados['cartela_cheia'].append(folha)
            elif numeros_faltando == 1:
                resultados['status']['quentes'] += 1
            elif numeros_faltando == 2:
                resultados['status']['mornas'] += 1

        return jsonify(resultados)
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)