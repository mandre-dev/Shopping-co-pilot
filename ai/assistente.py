"""
Duas funcionalidades de IA sobre o banco de compras:

1. resumo_executivo() - lê a tabela reposicao_sugerida e escreve um parágrafo
   pra quem não vai abrir o Power BI.
2. perguntar(pergunta) - recebe uma pergunta em português, converte pra SQL
   e devolve a resposta. Ex: "quais fornecedores atrasam mais?"

Usa a API gratuita do Google Gemini (chave em GEMINI_API_KEY). Sem a chave,
cai num modo local que cobre as perguntas mais comuns sem depender de API.
"""

import os
import sqlite3
import pandas as pd

DB_PATH = "../database/copiloto_compras.db"


def _tem_chave_gemini():
    return bool(os.environ.get("GEMINI_API_KEY"))


def _chamar_gemini(prompt):
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    modelo = genai.GenerativeModel("gemini-2.0-flash-lite")
    resposta = modelo.generate_content(prompt)
    return resposta.text.strip()


def resumo_executivo():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM reposicao_sugerida", conn)
    conn.close()

    criticos = df[df["abaixo_do_minimo"] == 1]
    custo_total = criticos["custo_reposicao"].sum()
    fornecedor_critico = (
        criticos.groupby("fornecedor")["custo_reposicao"].sum().idxmax()
        if not criticos.empty else "nenhum"
    )
    categoria_critica = (
        criticos.groupby("categoria")["custo_reposicao"].sum().idxmax()
        if not criticos.empty else "nenhuma"
    )

    dados = (
        f"{len(criticos)} produtos abaixo do estoque mínimo\n"
        f"Custo total de reposição estimado: R$ {custo_total:,.2f}\n"
        f"Fornecedor com maior valor pendente de reposição: {fornecedor_critico}\n"
        f"Categoria mais afetada: {categoria_critica}"
    )

    if _tem_chave_gemini():
        try:
            prompt = (
                "Escreva um resumo executivo de 4 frases para o gestor de Compras, "
                "em português, direto ao ponto, com base nestes dados:\n\n" + dados
            )
            return _chamar_gemini(prompt)
        except Exception as e:
            print(f"[aviso] IA indisponível, usando resumo local ({e})")

    return (
        f"{len(criticos)} produtos estão abaixo do estoque mínimo, com custo de "
        f"reposição estimado em R$ {custo_total:,.2f}. A categoria mais crítica é "
        f"{categoria_critica}, e o fornecedor {fornecedor_critico} concentra o maior "
        f"valor pendente. Recomenda-se priorizar os pedidos dessa categoria antes que "
        f"o estoque zere."
    )


# perguntas fixas cobertas sem precisar de IA - cobre os casos mais comuns
_PERGUNTAS_LOCAIS = {
    "fornecedores atrasam": """
        SELECT f.nome, ROUND(AVG(julianday(p.data_entrega_real) - julianday(p.data_entrega_prevista)), 1) AS atraso_medio
        FROM pedidos_compra p JOIN fornecedores f ON f.id = p.fornecedor_id
        WHERE p.data_entrega_real IS NOT NULL
        GROUP BY f.nome ORDER BY atraso_medio DESC LIMIT 5
    """,
    "produtos criticos": """
        SELECT sku, produto, estoque_atual, estoque_minimo, custo_reposicao
        FROM reposicao_sugerida WHERE abaixo_do_minimo = 1
        ORDER BY custo_reposicao DESC LIMIT 10
    """,
    "categoria mais cara": """
        SELECT categoria, SUM(custo_reposicao) AS total
        FROM reposicao_sugerida GROUP BY categoria ORDER BY total DESC LIMIT 5
    """,
}


def perguntar(pergunta):
    conn = sqlite3.connect(DB_PATH)

    if _tem_chave_gemini():
        schema = """
        Tabelas disponíveis:
        reposicao_sugerida(sku, produto, categoria, fornecedor, prazo_entrega_dias,
            avaliacao_fornecedor, estoque_atual, estoque_minimo, demanda_prevista_dia,
            abaixo_do_minimo, qtd_sugerida_compra, custo_reposicao)
        pedidos_compra(id, produto_id, fornecedor_id, data_pedido,
            data_entrega_prevista, data_entrega_real, quantidade, custo_total)
        fornecedores(id, nome, prazo_medio_entrega_dias, avaliacao)
        """
        try:
            prompt = (
                f"{schema}\n\nEscreva apenas uma query SQLite (sem explicação, sem markdown) "
                f"que responda: {pergunta}"
            )
            sql = _chamar_gemini(prompt).replace("```sql", "").replace("```", "").strip()
            resultado = pd.read_sql(sql, conn)
            conn.close()
            return resultado
        except Exception as e:
            print(f"[aviso] Falha ao gerar SQL via IA, tentando resposta local ({e})")

    # fallback: casamento simples por palavra-chave
    for chave, sql in _PERGUNTAS_LOCAIS.items():
        if any(palavra in pergunta.lower() for palavra in chave.split()):
            resultado = pd.read_sql(sql, conn)
            conn.close()
            return resultado

    conn.close()
    return "Não consegui interpretar essa pergunta sem a chave de IA configurada."


if __name__ == "__main__":
    print("--- Resumo Executivo ---")
    print(resumo_executivo())

    print("\n--- Pergunta: quais fornecedores atrasam mais? ---")
    print(perguntar("quais fornecedores atrasam mais?"))
