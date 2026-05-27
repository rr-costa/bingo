# 🎲 Feature: Cartelas de Reforço de Bingo

## 📋 Resumo da Implementação

Nova feature implementada com sucesso! Você agora pode criar cartelas de reforço em formato **A6** para seus eventos de bingo, salvas no banco de dados de forma separada e numeradas sequencialmente.

## 🚀 Quick Start

### Gerar uma Cartela de Reforço

```bash
python gerar_reforco.py "Nome do Evento"
```

**Exemplo:**
```bash
python gerar_reforco.py "54 Festa SA"
```

Isso vai gerar um PDF em A6 e salvar a cartela no banco com numeração automática.

### Listar Cartelas de Reforço de um Evento

```bash
python listar_reforcos.py "Nome do Evento"
```

## 📝 Características

✅ **Formato A6** - Otimizado para impressão em papel pequeno  
✅ **Imagem de Fundo** - Usa a mesma imagem do gerador principal  
✅ **Numeração Automática** - Cada cartela é numerada sequencialmente  
✅ **Armazenamento Separado** - Salvas com `tipo_cartela='reforco'`  
✅ **Fora das Rodadas** - Não interferem com o sistema de rodadas  
✅ **Fonte Personalizada** - Mesmas fontes do sistema principal  

## 🗂️ Arquivos Criados/Modificados

### Novos Arquivos
- `reforco_bingo.py` - Classe geradora de cartelas de reforço
- `gerar_reforco.py` - CLI para gerar cartelas de reforço
- `listar_reforcos.py` - CLI para listar cartelas de reforço geradas
- `REFORCO_DOCUMENTATION.md` - Documentação completa da feature

### Modificados
- `database.py` - Adicionado campo `tipo_cartela` na tabela
- `gerador_bingo.py` - Atualizado para usar `tipo_cartela='normal'`

## 💾 Estrutura no Banco de Dados

As cartelas de reforço são armazenadas com:

```
Tabela: cartelas
├── id          : "{evento}_REFORCO_{numero}"
├── evento      : Nome do evento
├── tipo_cartela: "reforco"
├── rodada      : 0 (sem rodada)
├── folha       : 0 (sem folha)
├── posicao_na_folha: Número sequencial (1, 2, 3, ...)
└── numeros     : Array 5x5 com os números da cartela
```

## 📊 Comparação: Cartelas Normais vs Reforço

| Aspecto | Normal | Reforço |
|---------|--------|---------|
| Tamanho | A4 | A6 |
| Tipo | 'normal' | 'reforco' |
| Rodada | 1-6 | 0 |
| Folha | Numerada | 0 |
| Gerador | `gerador_bingo.py` | `gerar_reforco.py` |
| Cores | 6 cores por rodada | Bege claro |

## 📦 Saída de Arquivos

Os PDFs são salvos em: `output/cartela_reforco_{evento}_{numero}.pdf`

**Exemplo para "54 Festa SA":**
```
output/cartela_reforco_54_Festa_SA_1.pdf
output/cartela_reforco_54_Festa_SA_2.pdf
output/cartela_reforco_54_Festa_SA_3.pdf
...
```

## 🔄 Fluxo de Uso Completo

```bash
# 1. Gerar cartelas normais do evento
python gerador_bingo.py "54 Festa SA" -c 5 -f 600

# 2. Gerar cartelas de reforço conforme necessário
python gerar_reforco.py "54 Festa SA"      # Reforço #1
python gerar_reforco.py "54 Festa SA"      # Reforço #2
python gerar_reforco.py "54 Festa SA"      # Reforço #3

# 3. Listar cartelas de reforço geradas
python listar_reforcos.py "54 Festa SA"

# 4. Imprimir os PDFs em formato A6
# Arquivos prontos em output/cartela_reforco_54_Festa_SA_*.pdf
```

## 🛠️ Requisitos Atendidos

- ✅ Criar uma única cartela dentro de evento
- ✅ Cartela de reforço da rodada
- ✅ Folha A6 com imagem de fundo
- ✅ Mesma qualidade do gerador principal
- ✅ Salvas no banco do evento fora das rodadas
- ✅ Marcadas como "Reforço"
- ✅ Numeradas sequencialmente

## 🧪 Testes Realizados

✅ Geração de múltiplas cartelas de reforço para um mesmo evento  
✅ Numeração sequencial correta  
✅ Armazenamento correto no banco de dados  
✅ Compatibilidade com cartelas normais  
✅ Funcionamento com múltiplos eventos  
✅ Geração de PDFs em A6 com fundo  

## 📞 Suporte

Para mais detalhes técnicos, consulte `REFORCO_DOCUMENTATION.md`
