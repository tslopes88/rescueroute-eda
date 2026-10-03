"""
Módulo de persistência relacional com SQLite para o sistema de estoque.

Garante acididade (Atomicidade, Consistência, Isolamento e Durabilidade) nas operações
através de transações SQL gerenciadas via context managers com fechamento automático.
"""

from contextlib import contextmanager
import sqlite3
from typing import Generator

from modelos import ItemPedido, ItemVenda, Movimentacao, Peca, Pedido, Venda


class BancoDados:
    """
    Gerenciador da camada de persistência em SQLite.
    """

    def __init__(self, db_path: str = "estoque.db"):
        self.db_path = db_path
        self._inicializar_banco()

    @contextmanager
    def get_conexao(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager que abre, gerencia transação e fecha a conexão SQLite."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _inicializar_banco(self) -> None:
        """Cria a estrutura de tabelas caso não existam."""
        with self.get_conexao() as conn:
            cursor = conn.cursor()

            # Tabela de Peças (Catálogo de Estoque)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pecas (
                    sku TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    fabricante TEXT NOT NULL,
                    preco_centavos INTEGER NOT NULL CHECK (preco_centavos >= 0),
                    estoque_atual INTEGER NOT NULL CHECK (estoque_atual >= 0),
                    estoque_reservado INTEGER NOT NULL CHECK (
                        estoque_reservado >= 0 AND estoque_reservado <= estoque_atual
                    ),
                    estoque_minimo INTEGER NOT NULL CHECK (estoque_minimo >= 0),
                    localizacao TEXT NOT NULL
                );
            """)

            # Tabela de Movimentações (Histórico Rastreável)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                    tipo TEXT NOT NULL,
                    observacao TEXT,
                    FOREIGN KEY (sku) REFERENCES pecas (sku) ON DELETE CASCADE
                );
            """)

            # Tabela de Pedidos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id TEXT PRIMARY KEY,
                    cliente TEXT NOT NULL,
                    status TEXT NOT NULL,
                    urgencia INTEGER NOT NULL CHECK (urgencia IN (1, 2, 3)),
                    ordem_chegada INTEGER NOT NULL,
                    data_criacao TEXT NOT NULL
                );
            """)

            # Tabela de Itens de Pedido
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS itens_pedido (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pedido_id TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                    FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE,
                    FOREIGN KEY (sku) REFERENCES pecas (sku)
                );
            """)

            # Tabela de Layout do Depósito (Grafos)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vias_deposito (
                    ponto_a TEXT NOT NULL,
                    ponto_b TEXT NOT NULL,
                    PRIMARY KEY (ponto_a, ponto_b)
                );
            """)

            # Tabela de Vendas Faturadas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vendas (
                    id_venda TEXT PRIMARY KEY,
                    id_pedido_origem TEXT,
                    cliente TEXT NOT NULL,
                    valor_total_centavos INTEGER NOT NULL CHECK (valor_total_centavos >= 0),
                    data_venda TEXT NOT NULL
                );
            """)

            # Tabela de Itens de Venda
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS itens_venda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venda_id TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                    preco_unitario_centavos INTEGER NOT NULL CHECK (preco_unitario_centavos >= 0),
                    subtotal_centavos INTEGER NOT NULL CHECK (subtotal_centavos >= 0),
                    FOREIGN KEY (venda_id) REFERENCES vendas (id_venda) ON DELETE CASCADE,
                    FOREIGN KEY (sku) REFERENCES pecas (sku)
                );
            """)

            conn.commit()

    # --- OPERAÇÕES DE PEÇAS ---

    @staticmethod
    def _salvar_peca_na_conexao(conn: sqlite3.Connection, peca: Peca) -> None:
        conn.execute(
            """
                INSERT INTO pecas (
                    sku, nome, categoria, fabricante, preco_centavos,
                    estoque_atual, estoque_reservado, estoque_minimo, localizacao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sku) DO UPDATE SET
                    nome=excluded.nome,
                    categoria=excluded.categoria,
                    fabricante=excluded.fabricante,
                    preco_centavos=excluded.preco_centavos,
                    estoque_atual=excluded.estoque_atual,
                    estoque_reservado=excluded.estoque_reservado,
                    estoque_minimo=excluded.estoque_minimo,
                    localizacao=excluded.localizacao;
            """,
            (
                peca.sku,
                peca.nome,
                peca.categoria,
                peca.fabricante,
                peca.preco_centavos,
                peca.estoque_atual,
                peca.estoque_reservado,
                peca.estoque_minimo,
                peca.localizacao,
            ),
        )

    def salvar_peca(self, peca: Peca) -> None:
        """Insere ou atualiza uma peça no banco de dados SQLite."""
        with self.get_conexao() as conn:
            self._salvar_peca_na_conexao(conn, peca)

    def atualizar_peca(self, peca: Peca) -> None:
        """Atualiza os dados descritivos de uma peça sem alterar seus saldos de estoque."""
        with self.get_conexao() as conn:
            cursor = conn.execute(
                """
                UPDATE pecas
                SET nome = ?, categoria = ?, fabricante = ?, preco_centavos = ?, localizacao = ?
                WHERE sku = ?;
                """,
                (peca.nome, peca.categoria, peca.fabricante, peca.preco_centavos, peca.localizacao, peca.sku),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"Peça com SKU '{peca.sku}' não encontrada.")

    @staticmethod
    def _registrar_movimentacao_na_conexao(
        conn: sqlite3.Connection, movimentacao: Movimentacao
    ) -> None:
        cursor = conn.execute(
            """
            INSERT INTO movimentacoes (timestamp, sku, quantidade, tipo, observacao)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                movimentacao.timestamp,
                movimentacao.sku,
                movimentacao.quantidade,
                movimentacao.tipo,
                movimentacao.observacao,
            ),
        )
        movimentacao.id_movimentacao = cursor.lastrowid

    @staticmethod
    def _salvar_pedido_na_conexao(conn: sqlite3.Connection, pedido: Pedido) -> None:
        conn.execute(
            """
            INSERT INTO pedidos (id, cliente, status, urgencia, ordem_chegada, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET status=excluded.status;
            """,
            (
                pedido.id_pedido,
                pedido.cliente,
                pedido.status,
                pedido.urgencia,
                pedido.ordem_chegada,
                pedido.data_criacao,
            ),
        )

    def salvar_operacao_estoque(
        self,
        pecas: list[Peca],
        movimentacoes: list[Movimentacao],
        pedido: Pedido | None = None,
        venda: Venda | None = None,
    ) -> None:
        """Grava estoque, histórico, pedido e venda na mesma transação SQLite."""
        with self.get_conexao() as conn:
            for peca in pecas:
                self._salvar_peca_na_conexao(conn, peca)
            for movimentacao in movimentacoes:
                self._registrar_movimentacao_na_conexao(conn, movimentacao)
            if pedido is not None:
                self._salvar_pedido_na_conexao(conn, pedido)
            if venda is not None:
                self._salvar_venda_na_conexao(conn, venda)

    def carregar_todas_pecas(self) -> list[Peca]:
        """Carrega todas as peças do banco para reconstruir a Tabela Hash em memória."""
        with self.get_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT sku, nome, categoria, fabricante, preco_centavos,
                       estoque_atual, estoque_reservado, estoque_minimo, localizacao
                FROM pecas;
            """
            )
            linhas = cursor.fetchall()
            return [
                Peca(
                    sku=sku,
                    nome=nome,
                    categoria=categoria,
                    fabricante=fabricante,
                    preco_centavos=preco_centavos,
                    estoque_atual=estoque_atual,
                    estoque_reservado=estoque_reservado,
                    estoque_minimo=estoque_minimo,
                    localizacao=localizacao,
                )
                for sku, nome, categoria, fabricante, preco_centavos, estoque_atual, estoque_reservado, estoque_minimo, localizacao in linhas
            ]

    # --- OPERAÇÕES DE MOVIMENTAÇÃO ---

    def registrar_movimentacao(self, mov: Movimentacao) -> Movimentacao:
        """Grava o registro de movimentação de estoque."""
        with self.get_conexao() as conn:
            self._registrar_movimentacao_na_conexao(conn, mov)
        return mov

    def carregar_movimentacoes(self, sku: str | None = None) -> list[Movimentacao]:
        """Carrega o histórico de movimentações, opcionalmente filtrado por SKU."""
        with self.get_conexao() as conn:
            cursor = conn.cursor()
            if sku:
                cursor.execute(
                    """
                    SELECT id, sku, quantidade, tipo, observacao, timestamp
                    FROM movimentacoes
                    WHERE UPPER(sku) = ?
                    ORDER BY id ASC;
                """,
                    (sku.strip().upper(),),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, sku, quantidade, tipo, observacao, timestamp
                    FROM movimentacoes
                    ORDER BY id ASC;
                """
                )

            linhas = cursor.fetchall()
            return [
                Movimentacao(
                    id_movimentacao=id_mov,
                    sku=sku_val,
                    quantidade=qtd,
                    tipo=tipo_val,
                    observacao=obs,
                    timestamp=dt_val,
                )
                for id_mov, sku_val, qtd, tipo_val, obs, dt_val in linhas
            ]

    # --- OPERAÇÕES DE PEDIDOS ---

    def salvar_pedido(self, pedido: Pedido) -> None:
        """Salva um pedido e seus itens em uma transação atômica."""
        with self.get_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO pedidos (id, cliente, status, urgencia, ordem_chegada, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status;
            """,
                (
                    pedido.id_pedido,
                    pedido.cliente,
                    pedido.status,
                    pedido.urgencia,
                    pedido.ordem_chegada,
                    pedido.data_criacao,
                ),
            )

            # Insere os itens apenas se for novo pedido
            cursor.execute("SELECT COUNT(*) FROM itens_pedido WHERE pedido_id = ?;", (pedido.id_pedido,))
            if cursor.fetchone()[0] == 0:
                for item in pedido.itens:
                    cursor.execute(
                        "INSERT INTO itens_pedido (pedido_id, sku, quantidade) VALUES (?, ?, ?);",
                        (pedido.id_pedido, item.sku, item.quantidade),
                    )
            conn.commit()

    def carregar_pedidos(self) -> list[Pedido]:
        """Carrega todos os pedidos do banco de dados com seus respectivos itens."""
        with self.get_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, cliente, status, urgencia, ordem_chegada, data_criacao FROM pedidos ORDER BY ordem_chegada ASC;")
            linhas_pedidos = cursor.fetchall()

            pedidos = []
            for p in linhas_pedidos:
                pid, cliente, status, urgencia, ordem_chegada, data_criacao = p
                cursor.execute("SELECT sku, quantidade FROM itens_pedido WHERE pedido_id = ?;", (pid,))
                itens = [
                    ItemPedido(sku=sku_item, quantidade=qtd_item)
                    for sku_item, qtd_item in cursor.fetchall()
                ]
                pedidos.append(
                    Pedido(
                        id_pedido=pid,
                        cliente=cliente,
                        itens=itens,
                        urgencia=urgencia,
                        ordem_chegada=ordem_chegada,
                        status=status,
                        data_criacao=data_criacao,
                    )
                )
            return pedidos

    # --- OPERAÇÕES DO GRAFO DO DEPÓSITO ---

    def salvar_via_deposito(self, ponto_a: str, ponto_b: str) -> None:
        """Salva uma conexão de corredor no depósito."""
        self.salvar_vias_deposito([(ponto_a, ponto_b)])

    def salvar_vias_deposito(self, vias: list[tuple[str, str]]) -> None:
        """Salva várias conexões do depósito na mesma transação."""
        normalizadas = []
        for ponto_a, ponto_b in vias:
            if not isinstance(ponto_a, str) or not ponto_a.strip():
                raise ValueError("O primeiro setor não pode ficar vazio.")
            if not isinstance(ponto_b, str) or not ponto_b.strip():
                raise ValueError("O segundo setor não pode ficar vazio.")
            ponto_a, ponto_b = ponto_a.strip().upper(), ponto_b.strip().upper()
            if ponto_a == ponto_b:
                raise ValueError("Uma via deve conectar dois setores diferentes.")
            normalizadas.append(tuple(sorted((ponto_a, ponto_b))))
        with self.get_conexao() as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO vias_deposito (ponto_a, ponto_b) VALUES (?, ?);",
                normalizadas,
            )

    def carregar_vias_deposito(self) -> list[tuple[str, str]]:
        """Carrega todas as vias cadastradas no depósito."""
        with self.get_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ponto_a, ponto_b FROM vias_deposito;")
            return cursor.fetchall()

    # --- OPERAÇÕES DE VENDAS ---

    @staticmethod
    def _salvar_venda_na_conexao(conn: sqlite3.Connection, venda: Venda) -> None:
        """Insere uma venda e seus itens; IDs repetidos são rejeitados."""
        conn.execute(
            """
            INSERT INTO vendas (id_venda, id_pedido_origem, cliente, valor_total_centavos, data_venda)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                venda.id_venda,
                venda.id_pedido_origem,
                venda.cliente,
                venda.valor_total_centavos,
                venda.data_venda,
            ),
        )
        conn.executemany(
            """
            INSERT INTO itens_venda (
                venda_id, sku, quantidade, preco_unitario_centavos, subtotal_centavos
            ) VALUES (?, ?, ?, ?, ?);
            """,
            [
                (
                    venda.id_venda,
                    item.sku,
                    item.quantidade,
                    item.preco_unitario_centavos,
                    item.subtotal_centavos,
                )
                for item in venda.itens
            ],
        )

    def salvar_venda(self, venda: Venda) -> None:
        """Salva uma venda e seus itens em uma transação atômica."""
        with self.get_conexao() as conn:
            self._salvar_venda_na_conexao(conn, venda)

    def carregar_vendas(self) -> list[Venda]:
        """Carrega todas as vendas registradas com seus respectivos itens."""
        with self.get_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_venda, id_pedido_origem, cliente, valor_total_centavos, data_venda FROM vendas ORDER BY data_venda DESC;"
            )
            linhas_vendas = cursor.fetchall()

            vendas = []
            for v in linhas_vendas:
                vid, id_ped_origem, cliente, valor_total, data_venda = v
                cursor.execute(
                    "SELECT sku, quantidade, preco_unitario_centavos FROM itens_venda WHERE venda_id = ?;",
                    (vid,),
                )
                itens = [
                    ItemVenda(sku=sku_item, quantidade=qtd_item, preco_unitario_centavos=preco_item)
                    for sku_item, qtd_item, preco_item in cursor.fetchall()
                ]
                vendas.append(
                    Venda(
                        id_venda=vid,
                        cliente=cliente,
                        itens=itens,
                        id_pedido_origem=id_ped_origem,
                        data_venda=data_venda,
                    )
                )
            return vendas
