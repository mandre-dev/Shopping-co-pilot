"""
Calcula, para cada produto:
  - demanda média diária nos últimos 30 e 90 dias
  - previsão de demanda pros próximos 30 dias (média móvel ponderada,
    dando mais peso ao período recente)
  - se está abaixo do estoque mínimo
  - quantidade sugerida de compra, considerando o prazo de entrega do fornecedor
    (não adianta sugerir comprar só o que falta hoje se o fornecedor demora 15 dias)

Roda direto sobre o banco e grava o resultado numa tabela nova, além de
exportar CSVs prontos para o Power BI.
"""

import sqlite3
import pandas as pd
from datetime import date, timedelta

DB_PATH = "../database/copiloto_compras.db"


def carregar_dados(conn):
    produtos = pd.read_sql("SELECT * FROM produtos", conn)
    vendas = pd.read_sql("SELECT * FROM vendas", conn, parse_dates=["data"])
    fornecedores = pd.read_sql("SELECT * FROM fornecedores", conn)
    return produtos, vendas, fornecedores


def calcular_demanda(vendas, produto_id, dias):
    limite = pd.Timestamp(date.today() - timedelta(days=dias))
    vendas_periodo = vendas[(vendas["produto_id"] == produto_id) & (vendas["data"] >= limite)]
    if vendas_periodo.empty:
        return 0.0
    return vendas_periodo["quantidade"].sum() / dias


def previsao_demanda(vendas, produto_id):
    media_30 = calcular_demanda(vendas, produto_id, 30)
    media_90 = calcular_demanda(vendas, produto_id, 90)
    # peso maior pro período recente, mas sem ignorar a tendência de 3 meses
    return round(media_30 * 0.7 + media_90 * 0.3, 2)


def montar_relatorio(produtos, vendas, fornecedores):
    fornecedores_idx = fornecedores.set_index("id")
    linhas = []

    for _, produto in produtos.iterrows():
        demanda_dia = previsao_demanda(vendas, produto["id"])
        fornecedor = fornecedores_idx.loc[produto["fornecedor_id"]]
        prazo = fornecedor["prazo_medio_entrega_dias"]

        # cobertura de segurança: estoque mínimo + demanda esperada durante o prazo de entrega
        cobertura_necessaria = produto["estoque_minimo"] + (demanda_dia * prazo)
        abaixo_do_minimo = produto["estoque_atual"] < produto["estoque_minimo"]
        qtd_sugerida = max(0, round(cobertura_necessaria - produto["estoque_atual"]))

        linhas.append({
            "sku": produto["sku"],
            "produto": produto["nome"],
            "categoria": produto["categoria"],
            "fornecedor": fornecedor["nome"],
            "prazo_entrega_dias": prazo,
            "avaliacao_fornecedor": fornecedor["avaliacao"],
            "estoque_atual": produto["estoque_atual"],
            "estoque_minimo": produto["estoque_minimo"],
            "demanda_prevista_dia": demanda_dia,
            "abaixo_do_minimo": abaixo_do_minimo,
            "qtd_sugerida_compra": qtd_sugerida,
            "custo_reposicao": round(qtd_sugerida * produto["preco_unitario"], 2),
        })

    return pd.DataFrame(linhas)


def analise_fornecedores(conn):
    pedidos = pd.read_sql(
        """
        SELECT p.id, p.fornecedor_id, f.nome AS fornecedor,
               p.data_entrega_prevista, p.data_entrega_real, p.custo_total
        FROM pedidos_compra p
        JOIN fornecedores f ON f.id = p.fornecedor_id
        WHERE p.data_entrega_real IS NOT NULL
        """,
        conn, parse_dates=["data_entrega_prevista", "data_entrega_real"]
    )
    pedidos["atraso_dias"] = (pedidos["data_entrega_real"] - pedidos["data_entrega_prevista"]).dt.days
    pedidos["atraso_dias"] = pedidos["atraso_dias"].clip(lower=0)

    resumo = pedidos.groupby("fornecedor").agg(
        pedidos_entregues=("id", "count"),
        atraso_medio_dias=("atraso_dias", "mean"),
        pct_pedidos_atrasados=("atraso_dias", lambda x: round((x > 0).mean() * 100, 1)),
        valor_total_comprado=("custo_total", "sum"),
    ).reset_index()
    resumo["atraso_medio_dias"] = resumo["atraso_medio_dias"].round(1)
    return resumo.sort_values("atraso_medio_dias", ascending=False)


def main():
    conn = sqlite3.connect(DB_PATH)
    produtos, vendas, fornecedores = carregar_dados(conn)

    relatorio = montar_relatorio(produtos, vendas, fornecedores)
    performance_fornecedores = analise_fornecedores(conn)

    relatorio.to_sql("reposicao_sugerida", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    relatorio.to_csv("../powerbi_data/reposicao_sugerida.csv", index=False, encoding="utf-8-sig")
    performance_fornecedores.to_csv("../powerbi_data/performance_fornecedores.csv", index=False, encoding="utf-8-sig")
    produtos.to_csv("../powerbi_data/produtos.csv", index=False, encoding="utf-8-sig")
    vendas.to_csv("../powerbi_data/vendas.csv", index=False, encoding="utf-8-sig")

    criticos = relatorio[relatorio["abaixo_do_minimo"]]
    print(f"{len(criticos)} produtos abaixo do mínimo")
    print(f"Custo total estimado de reposição: R$ {criticos['custo_reposicao'].sum():,.2f}")
    print("CSVs exportados em powerbi_data/")


if __name__ == "__main__":
    main()
