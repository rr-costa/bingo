# Cartelas de Reforço - Documentação

## Visão Geral

A feature de **Cartelas de Reforço** permite gerar cartelas especiais em formato **A6** para uso como reforço de rodadas em eventos de bingo. Estas cartelas são:

- Salvas em formato PDF com imagem de fundo
- Armazenadas no banco de dados do evento
- Separadas das cartelas normais de rodadas
- Numeradas sequencialmente por evento

## Como Usar

### Gerar uma Cartela de Reforço

Use o comando:

```bash
python gerar_reforco.py "Nome do Evento"
```

**Exemplos:**

```bash
# Para o evento "54 Festa SA"
python gerar_reforco.py "54 Festa SA"

# Para o evento "Bingo Beneficente"
python gerar_reforco.py "Bingo Beneficente"

# Para um novo evento
python gerar_reforco.py "Festa de São João"
```

### Saída Esperada

A cada execução, o sistema:

1. **Gera uma cartela única e aleatória** em formato 5x5 com FREE no centro
2. **Cria um PDF em A6** com:
   - Imagem de fundo (de `static/images/fundo_bingo.png`)
   - Cartela centralizada na página
   - Fundo em cor bege claro (Moccasin)
   - Letras BINGO em destaque
3. **Salva no banco de dados** com:
   - ID: `{evento}_REFORCO_{numero}`
   - Tipo: `reforco`
   - Numeração sequencial (1, 2, 3, ...)
4. **Salva o arquivo PDF** em: `output/cartela_reforco_{evento}_{numero}.pdf`

## Características Técnicas

### Formato da Cartela
- **Tamanho de página:** A6 (10.5 x 14.8 cm)
- **Cartela:** 9.5 x 11 cm (centralizada)
- **Números:** 5x5 com FREE no centro
- **Cor de fundo da cartela:** Bege claro (#FFE4B5)

### Estrutura no Banco de Dados
As cartelas de reforço são armazenadas na tabela `cartelas` com:

```
id           : {evento}_REFORCO_{numero}
evento       : Nome do evento
tipo_cartela : 'reforco'
rodada       : 0 (não utiliza rodadas)
folha        : 0 (não utiliza folhas)
posicao_na_folha: Número sequencial da cartela de reforço
numeros      : Matriz 5x5 com os números da cartela
```

### Diferenças das Cartelas Normais

| Aspecto | Cartela Normal | Cartela de Reforço |
|---------|----------------|--------------------|
| Tamanho | A4 | A6 |
| Tipo | 'normal' | 'reforco' |
| Rodada | 1-6 | 0 (sem rodada) |
| Folha | Numerada | 0 (sem folha) |
| Cor de fundo | Múltiplas cores por rodada | Bege claro |
| ID | `{evento}_F{folha}C{posicao}` | `{evento}_REFORCO_{numero}` |
| Geração | Com `gerador_bingo.py` | Com `gerar_reforco.py` |

## Fluxo de Uso

1. **Gerar cartelas normais** do evento com:
   ```bash
   python gerador_bingo.py "Nome do Evento" -c 5 -f 600
   ```

2. **Gerar cartelas de reforço** conforme necessário:
   ```bash
   python gerar_reforco.py "Nome do Evento"
   ```

3. **Usar as cartelas:** As cartelas de reforço estão em `output/` prontas para imprimir

## Consultar Cartelas de Reforço no Banco

Para ver quais cartelas de reforço foram geradas para um evento:

```python
from database import BingoDatabase

db = BingoDatabase()
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('''
    SELECT id, evento, posicao_na_folha 
    FROM cartelas 
    WHERE evento = ? AND tipo_cartela = 'reforco'
    ORDER BY posicao_na_folha
''', ("Nome do Evento",))

reforcos = cursor.fetchall()
for row in reforcos:
    print(f"Reforço #{row['posicao_na_folha']}: {row['id']}")
```

## Arquivos Modificados e Criados

### Modificados:
- `database.py` - Adicionado campo `tipo_cartela` na tabela
- `gerador_bingo.py` - Atualizado para usar `tipo_cartela='normal'`

### Criados:
- `reforco_bingo.py` - Classe `ReforcoGenerator` para gerar cartelas de reforço
- `gerar_reforco.py` - CLI para usar o gerador de reforço

## Troubleshooting

### Erro: "Imagem de fundo não encontrada"
- Verifique se `static/images/fundo_bingo.png` existe
- O sistema ainda funciona sem a imagem (usando apenas cor de fundo)

### Erro: "Fonte não encontrada"
- Verifique se `static/fonts/COMIC.TTF` e `static/fonts/KGHAPPY.ttf` existem
- O sistema usa fontes padrão se as personalizadas não forem encontradas

### Cartelas não aparecem no banco
- Certifique-se de que `output/bingo_cartelas.db` tem permissão de escrita
- Verifique se o banco foi criado corretamente com `database.py`

## Notas Importantes

1. **Cada execução cria uma nova cartela** - números são gerados aleatoriamente
2. **Numeração é sequencial por evento** - cada evento tem sua própria contagem
3. **Independentes de rodadas** - cartelas de reforço não usam o sistema de rodadas
4. **Podem ser geradas em qualquer momento** - mesmo durante ou após rodadas
5. **Printáveis** - os PDFs em A6 são otimizados para impressão em papel A6
