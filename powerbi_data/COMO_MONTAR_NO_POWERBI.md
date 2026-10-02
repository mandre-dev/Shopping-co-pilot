# Montando o dashboard no Power BI

Os CSVs desta pasta já saem prontos do pipeline Python. Não precisa tratar
nada no Power Query além do básico de tipo de coluna.

## 1. Importar os dados

Power BI Desktop → Obter Dados → Texto/CSV → selecione os 4 arquivos:
- `reposicao_sugerida.csv` (tabela principal)
- `performance_fornecedores.csv`
- `produtos.csv`
- `vendas.csv`

## 2. Relacionamentos

No Model View, crie:
- `produtos[fornecedor_id]` → `performance_fornecedores` não tem chave direta,
  então relacione por nome do fornecedor se quiser cruzar, ou deixe as duas
  tabelas independentes (ambas já vêm agregadas o suficiente pra maioria dos
  visuais).
- `vendas[produto_id]` → `produtos[id]`

## 3. Visuais sugeridos (uma página só, sem exagero)

**Cartões no topo:**
- Total de produtos abaixo do mínimo (`COUNTROWS` filtrado por `abaixo_do_minimo`)
- Custo total de reposição (`SUM(custo_reposicao)`)
- Prazo médio de entrega dos fornecedores críticos

**Gráfico de barras:** custo de reposição por categoria (`reposicao_sugerida`)

**Gráfico de barras horizontal:** atraso médio por fornecedor
(`performance_fornecedores`, ordenado decrescente)

**Tabela:** os 10 produtos mais críticos (sku, produto, estoque atual,
estoque mínimo, qtd sugerida), ordenada por custo de reposição

**Gráfico de linha (opcional, mais avançado):** evolução de vendas dos
últimos 90 dias por categoria, usando `vendas.csv` + `produtos.csv`

## 4. Deixando dinâmico de verdade

Se quiser ir além de "print estático pro README": configure um Gateway de
Dados Local apontando pro `copiloto_compras.db` (via ODBC do SQLite) e agende
a atualização automática. Isso fecha o ciclo: pipeline Python atualiza o
banco → Power BI atualiza sozinho.

Pra fins de portfólio, também é perfeitamente válido só reexportar os CSVs
e clicar em "Atualizar" manualmente antes de printar o resultado.
