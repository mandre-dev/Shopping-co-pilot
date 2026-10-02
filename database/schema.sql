-- Modelo de dados simplificado de uma área de Compras/Estoque
-- Focado nas entidades que realmente importam para reposição e análise de fornecedor

CREATE TABLE fornecedores (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    prazo_medio_entrega_dias INTEGER NOT NULL,
    avaliacao REAL  -- 0 a 5, baseada em atraso histórico
);

CREATE TABLE produtos (
    id INTEGER PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    categoria TEXT NOT NULL,
    fornecedor_id INTEGER REFERENCES fornecedores(id),
    preco_unitario REAL NOT NULL,
    estoque_minimo INTEGER NOT NULL,
    estoque_atual INTEGER NOT NULL
);

CREATE TABLE vendas (
    id INTEGER PRIMARY KEY,
    produto_id INTEGER REFERENCES produtos(id),
    data DATE NOT NULL,
    quantidade INTEGER NOT NULL
);

CREATE TABLE pedidos_compra (
    id INTEGER PRIMARY KEY,
    produto_id INTEGER REFERENCES produtos(id),
    fornecedor_id INTEGER REFERENCES fornecedores(id),
    data_pedido DATE NOT NULL,
    data_entrega_prevista DATE NOT NULL,
    data_entrega_real DATE,  -- NULL enquanto não chega
    quantidade INTEGER NOT NULL,
    custo_total REAL NOT NULL
);
