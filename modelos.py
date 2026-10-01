"""
Modelos de domínio para o sistema de logística e controle de estoque de peças de computador.
"""

from datetime import datetime


class Peca:
    """
    Representa uma peça de computador no catálogo do estoque.

    Valores monetários são armazenados em centavos (int) para evitar erros de ponto flutuante:
    Exemplo: R$ 199,90 = 19990 centavos.
    """

    def __init__(
        self,
        sku: str,
        nome: str,
        categoria: str,
        fabricante: str,
        preco_centavos: int,
        estoque_atual: int = 0,
        estoque_reservado: int = 0,
        estoque_minimo: int = 0,
        localizacao: str = "EXPEDICAO",
    ):
        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("O SKU deve ser um texto não vazio.")
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("O nome da peça não pode ser vazio.")
        if not isinstance(preco_centavos, int) or isinstance(preco_centavos, bool) or preco_centavos < 0:
            raise ValueError("O preço em centavos deve ser um número inteiro não negativo.")
        if not isinstance(estoque_atual, int) or isinstance(estoque_atual, bool) or estoque_atual < 0:
            raise ValueError("O estoque atual não pode ser negativo.")
        if not isinstance(estoque_reservado, int) or isinstance(estoque_reservado, bool) or estoque_reservado < 0:
            raise ValueError("O estoque reservado não pode ser negativo.")
        if not isinstance(estoque_minimo, int) or isinstance(estoque_minimo, bool) or estoque_minimo < 0:
            raise ValueError("O estoque mínimo não pode ser negativo.")
        if estoque_reservado > estoque_atual:
            raise ValueError("O estoque reservado não pode superar o estoque físico.")
        if not isinstance(localizacao, str) or not localizacao.strip():
            raise ValueError("A localização no depósito não pode ser vazia.")
        if categoria is not None and not isinstance(categoria, str):
            raise ValueError("A categoria deve ser texto.")
        if fabricante is not None and not isinstance(fabricante, str):
            raise ValueError("O fabricante deve ser texto.")

        self.sku = sku.strip().upper()
        self.nome = nome.strip()
        self.categoria = categoria.strip() if categoria else "Geral"
        self.fabricante = fabricante.strip() if fabricante else "Genérico"
        self.preco_centavos = preco_centavos
        self.estoque_atual = estoque_atual
        self.estoque_reservado = estoque_reservado
        self.estoque_minimo = estoque_minimo
        self.localizacao = localizacao.strip().upper()

    @property
    def estoque_disponivel(self) -> int:
        """Estoque livre para novas reservas (atual - reservado)."""
        return max(0, self.estoque_atual - self.estoque_reservado)

    @property
    def abaixo_do_minimo(self) -> bool:
        """Indica se a disponibilidade total está abaixo da margem mínima."""
        return self.estoque_atual < self.estoque_minimo

    @property
    def preco_formatado(self) -> str:
        """Formata o preço em centavos para a representação em Real (R$)."""
        reais, centavos = divmod(self.preco_centavos, 100)
        reais_formatados = f"{reais:,}".replace(",", ".")
        return f"R$ {reais_formatados},{centavos:02d}"

    def __repr__(self) -> str:
        return (
            f"<Peca SKU={self.sku} Nome='{self.nome}' "
            f"Estoque={self.estoque_atual} (Reservado={self.estoque_reservado}) "
            f"Preço={self.preco_formatado} Local={self.localizacao}>"
        )


class Movimentacao:
    """
    Registro imutável de alteração no estoque para fins de rastreabilidade e auditoria.
    """

    def __init__(
        self,
        id_movimentacao: int | None,
        sku: str,
        quantidade: int,
        tipo: str,
        observacao: str = "",
        timestamp: str | None = None,
    ):
        tipos_validos = ("ENTRADA", "SAIDA", "RESERVA", "LIBERACAO", "AJUSTE")
        if tipo not in tipos_validos:
            raise ValueError(f"Tipo de movimentação inválido. Tipos aceitos: {tipos_validos}")
        if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade <= 0:
            raise ValueError("A quantidade movimentada deve ser um inteiro positivo.")

        self.id_movimentacao = id_movimentacao
        self.sku = sku.strip().upper()
        self.quantidade = quantidade
        self.tipo = tipo
        self.observacao = observacao.strip()
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __repr__(self) -> str:
        return f"<Movimentacao #{self.id_movimentacao} {self.tipo} SKU={self.sku} Qtd={self.quantidade} Data={self.timestamp}>"


class ItemPedido:
    """
    Representa uma peça e quantidade associada a um pedido de expedição.
    """

    def __init__(self, sku: str, quantidade: int):
        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("SKU do item inválido.")
        if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade <= 0:
            raise ValueError("Quantidade do item deve ser um número positivo.")
        self.sku = sku.strip().upper()
        self.quantidade = quantidade


class Pedido:
    """
    Representa um pedido de separação/expedição de peças.

    Estados possíveis:
      - ABERTO: Pedido criado, aguardando separação.
      - SEPARADO: Estoque reservado, rota calculada via BFS.
      - EXPEDIDO: Peças baixadas do estoque e entregues.
      - CANCELADO: Pedido cancelado, reservas liberadas.
    """

    STATUS_VALIDOS = ("ABERTO", "SEPARADO", "EXPEDIDO", "CANCELADO")

    def __init__(
        self,
        id_pedido: str,
        cliente: str,
        itens: list[ItemPedido],
        urgencia: int = 2,
        ordem_chegada: int = 0,
        status: str = "ABERTO",
        data_criacao: str | None = None,
    ):
        if not isinstance(id_pedido, str) or not id_pedido.strip():
            raise ValueError("O ID do pedido não pode ser vazio.")
        if not isinstance(cliente, str) or not cliente.strip():
            raise ValueError("O cliente do pedido não pode ser vazio.")
        if not itens or len(itens) == 0:
            raise ValueError("O pedido deve conter pelo menos um item.")
        if status not in self.STATUS_VALIDOS:
            raise ValueError(f"Status inválido. Estados permitidos: {self.STATUS_VALIDOS}")
        if not isinstance(urgencia, int) or isinstance(urgencia, bool) or urgencia not in (1, 2, 3):
            raise ValueError("A urgência deve ser 1 (Urgente), 2 (Normal) ou 3 (Baixa).")
        if not isinstance(ordem_chegada, int) or isinstance(ordem_chegada, bool) or ordem_chegada < 0:
            raise ValueError("A ordem de chegada deve ser um inteiro não negativo.")

        self.id_pedido = id_pedido.strip().upper()
        self.cliente = cliente.strip()
        self.itens = itens
        self.urgencia = urgencia  # 1 = Alta (Urgente), 2 = Média, 3 = Baixa
        self.ordem_chegada = ordem_chegada
        self.status = status
        self.data_criacao = data_criacao or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __repr__(self) -> str:
        return f"<Pedido {self.id_pedido} Cliente='{self.cliente}' Status={self.status} Urgência={self.urgencia}>"
