"""
Cria o banco copiloto_compras.db e popula com dados fictícios de um cenário
de loja de acabamentos: fornecedores, produtos, histórico de vendas de 6 meses
e pedidos de compra (alguns já entregues, outros ainda em aberto).
"""

import sqlite3
import random
from datetime import date, timedelta
from faker import Faker

fake = Faker("pt_BR")
random.seed(7)

DB_PATH = "copiloto_compras.db"
CATEGORIAS = ["Pisos", "Revestimentos", "Tintas", "Argamassas", "Louças", "Metais", "Iluminação"]


def criar_schema(conn):
    with open("schema.sql") as f:
        conn.executescript(f.read())


def gerar_fornecedores(conn, n=8):
    fornecedores = []
    for i in range(n):
        prazo = random.randint(3, 15)
        avaliacao = round(random.uniform(2.5, 5.0), 1)
        fornecedores.append((i + 1, fake.company(), prazo, avaliacao))
    conn.executemany(
        "INSERT INTO fornecedores VALUES (?, ?, ?, ?)", fornecedores
    )
    return [f[0] for f in fornecedores]


def gerar_produtos(conn, fornecedor_ids, n=150):
    produtos = []
    for i in range(n):
        estoque_minimo = random.randint(10, 50)
        # parte dos produtos já nasce abaixo do mínimo, pra simular o problema real
        estoque_atual = random.randint(0, 80) if random.random() > 0.3 else random.randint(0, estoque_minimo)
        produtos.append((
            i + 1,
            f"SKU-{1000 + i}",
            f"{random.choice(CATEGORIAS)} {fake.word().capitalize()}",
            random.choice(CATEGORIAS),
            random.choice(fornecedor_ids),
            round(random.uniform(15, 450), 2),
            estoque_minimo,
            estoque_atual,
        ))
    conn.executemany(
        "INSERT INTO produtos VALUES (?, ?, ?, ?, ?, ?, ?, ?)", produtos
    )
    return [p[0] for p in produtos]


def gerar_vendas(conn, produto_ids, dias=180):
    hoje = date.today()
    vendas = []
    venda_id = 1
    for produto_id in produto_ids:
        # cada produto tem uma "popularidade" diferente, o que gera sazonalidade real nos dados
        popularidade = random.choice([0, 0, 1, 1, 1, 2, 2, 3])
        for d in range(dias):
            if popularidade == 0 or random.random() > 0.4:
                continue
            dia = hoje - timedelta(days=d)
            qtd = random.randint(1, 3 + popularidade * 2)
            vendas.append((venda_id, produto_id, dia.isoformat(), qtd))
            venda_id += 1
    conn.executemany("INSERT INTO vendas VALUES (?, ?, ?, ?)", vendas)


def gerar_pedidos_compra(conn, produto_ids, fornecedor_map, n=200):
    hoje = date.today()
    pedidos = []
    for i in range(n):
        produto_id = random.choice(produto_ids)
        fornecedor_id = fornecedor_map[produto_id]
        prazo = random.randint(3, 15)
        data_pedido = hoje - timedelta(days=random.randint(1, 150))
        data_prevista = data_pedido + timedelta(days=prazo)

        # ~20% dos pedidos atrasam de verdade, isso alimenta a análise de performance de fornecedor
        atraso = random.randint(1, 8) if random.random() < 0.2 else 0
        data_real = data_prevista + timedelta(days=atraso) if data_prevista <= hoje else None

        quantidade = random.randint(20, 200)
        preco = round(random.uniform(15, 450), 2)
        pedidos.append((
            i + 1, produto_id, fornecedor_id,
            data_pedido.isoformat(), data_prevista.isoformat(),
            data_real.isoformat() if data_real else None,
            quantidade, round(quantidade * preco, 2),
        ))
    conn.executemany(
        "INSERT INTO pedidos_compra VALUES (?, ?, ?, ?, ?, ?, ?, ?)", pedidos
    )


def main():
    conn = sqlite3.connect(DB_PATH)
    criar_schema(conn)

    fornecedor_ids = gerar_fornecedores(conn)
    produto_ids = gerar_produtos(conn, fornecedor_ids)
    gerar_vendas(conn, produto_ids)

    fornecedor_map = {
        row[0]: row[1]
        for row in conn.execute("SELECT id, fornecedor_id FROM produtos")
    }
    gerar_pedidos_compra(conn, produto_ids, fornecedor_map)

    conn.commit()
    conn.close()
    print(f"Banco criado em {DB_PATH}")


if __name__ == "__main__":
    main()
