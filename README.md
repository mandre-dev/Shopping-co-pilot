# Copiloto de Compras

Projeto de análise de dados aplicado a um problema real de uma área de
Compras: falta de visibilidade sobre quando repor estoque, quais
fornecedores atrasam mais e onde o dinheiro de reposição está concentrado.

## O problema

Numa loja (ou rede de lojas) de material de acabamento, o comprador
geralmente decide o que repor olhando planilha por planilha, sem
previsão de demanda e sem histórico consolidado de performance de
fornecedor. Isso gera duas falhas comuns:

- Comprar reativo: só percebe a ruptura quando o produto já zerou.
- Ignorar o prazo de entrega do fornecedor na hora de decidir quanto pedir.

Este projeto ataca as duas coisas com dados reais de vendas, estoque e
histórico de pedidos.

## A solução

1. **Banco de dados** (`database/`) — modelo relacional simples de
   produtos, fornecedores, vendas e pedidos de compra, com dados
   fictícios gerados de forma realista (sazonalidade por produto,
   atrasos de fornecedor variáveis).

2. **Análise e previsão** (`analytics/reposicao.py`) — calcula a demanda
   prevista de cada produto (média móvel ponderada entre 30 e 90 dias) e
   cruza com o prazo de entrega do fornecedor pra sugerir a quantidade
   de compra, não só "abaixo do mínimo, comprar o que falta".

3. **Dashboard** (Power BI, ver `powerbi_data/COMO_MONTAR_NO_POWERBI.md`) —
   visão executiva de estoque crítico, custo de reposição e performance
   de fornecedores.

4. **IA aplicada** (`ai/assistente.py`) — duas funções:
   - Resumo executivo em linguagem natural a partir dos dados calculados.
   - "Pergunte aos dados": traduz uma pergunta em português pra SQL e
     devolve a resposta, sem precisar abrir o dashboard pra tudo.

   Usa a API gratuita do Google Gemini. Sem chave configurada, cai num
   modo local que já cobre as perguntas mais comuns — o projeto funciona
   de ponta a ponta mesmo sem custo nenhum.

5. **Automação** (`automation/rodar_pipeline.py`) — roda o pipeline
   inteiro (recalcular + exportar + resumir) em um comando, pronto pra
   ser agendado (cron / Agendador de Tarefas) e rodar sozinho todo dia.

## Como rodar

```bash
pip install pandas openpyxl faker google-generativeai
cd database && python gerar_dados.py
cd ../automation && python rodar_pipeline.py
```

Os CSVs prontos pro Power BI ficam em `powerbi_data/`.

## Stack

Python (pandas, sqlite3), SQL, Power BI, API do Google Gemini (opcional).
# Shopping-co-pilot
