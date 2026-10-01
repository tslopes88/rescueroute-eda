"""
Camada de serviços e regras de negócio do sistema de logística e controle de estoque de peças.

Integra o banco de dados SQLite com as estruturas de dados customizadas em memória:
  - TabelaHash: Índice de consulta O(1) por SKU reconstruído a partir do SQLite.
  - MinHeap: Fila de prioridade com desempate FIFO para pedidos e reposição.
  - Grafo: Grafo de setores do depósito para cálculo de rotas de coleta via BFS.
  - PilhaOperacoes: Pilha LIFO encadeada para desfazer operações de estoque com segurança.
"""

from banco import BancoDados
from estruturas import AcaoReversivel, Grafo, MinHeap, PilhaOperacoes, TabelaHash
from modelos import ItemPedido, Movimentacao, Peca, Pedido


class GerenciadorEstoque:
    """
    Orquestrador central do sistema de estoque e logística.
    """

    def __init__(self, db_path: str = "estoque.db"):
        self.banco = BancoDados(db_path)
        self.tabela_hash = TabelaHash()
        self.heap_pedidos = MinHeap()
        self.grafo_deposito = Grafo()
        self.pilha_undo = PilhaOperacoes()
        self.contador_ordem_pedidos = 0

        self.carregar_dados()

    @staticmethod
    def _copiar_peca(peca: Peca, **alteracoes: int | str) -> Peca:
        dados = {
            "sku": peca.sku,
            "nome": peca.nome,
            "categoria": peca.categoria,
            "fabricante": peca.fabricante,
            "preco_centavos": peca.preco_centavos,
            "estoque_atual": peca.estoque_atual,
            "estoque_reservado": peca.estoque_reservado,
            "estoque_minimo": peca.estoque_minimo,
            "localizacao": peca.localizacao,
        }
        dados.update(alteracoes)
        return Peca(**dados)

    def carregar_dados(self) -> None:
        """
        Reconstrói o estado em memória a partir da fonte de verdade (SQLite).
        """
        self.tabela_hash.limpar()
        self.grafo_deposito = Grafo()

        # 1. Carrega catálogo de peças para a Tabela Hash O(1)
        pecas = self.banco.carregar_todas_pecas()
        for peca in pecas:
            self.tabela_hash.inserir(peca.sku, peca)

        # 2. Carrega layout do depósito no Grafo
        vias = self.banco.carregar_vias_deposito()
        if not vias:
            # Layout padrão inicial do depósito caso esteja vazio
            vias_padrao = [
                ("EXPEDICAO", "RECEBIMENTO"),
                ("RECEBIMENTO", "CORREDOR-A"),
                ("CORREDOR-A", "CORREDOR-B"),
                ("CORREDOR-B", "CORREDOR-C"),
                ("CORREDOR-C", "SETOR-NO-BREAKS"),
                ("CORREDOR-A", "SETOR-PLACAS"),
            ]
            self.banco.salvar_vias_deposito(vias_padrao)
            for a, b in vias_padrao:
                self.grafo_deposito.adicionar_via(a, b)
        else:
            for a, b in vias:
                self.grafo_deposito.adicionar_via(a, b)

        # 3. Carrega pedidos abertos na Min-Heap de prioridades
        self.heap_pedidos = MinHeap()
        pedidos = self.banco.carregar_pedidos()
        for p in pedidos:
            if p.ordem_chegada > self.contador_ordem_pedidos:
                self.contador_ordem_pedidos = p.ordem_chegada

            # Insere no Heap apenas se estiver aguardando separação
            if p.status == "ABERTO":
                self.heap_pedidos.inserir((p.urgencia, p.ordem_chegada, p.id_pedido))

    # --- CATÁLOGO DE PEÇAS ---

    def cadastrar_peca(
        self,
        sku: str,
        nome: str,
        categoria: str,
        fabricante: str,
        preco_centavos: int,
        estoque_atual: int = 0,
        estoque_minimo: int = 0,
        localizacao: str = "EXPEDICAO",
    ) -> Peca:
        """Cadastra uma nova peça garantindo SKU único."""
        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("O SKU não pode ficar vazio.")
        sku_clean = sku.strip().upper()
        if self.tabela_hash.buscar(sku_clean) is not None:
            raise ValueError(f"Já existe uma peça cadastrada com o SKU '{sku_clean}'.")

        peca = Peca(
            sku=sku_clean,
            nome=nome,
            categoria=categoria,
            fabricante=fabricante,
            preco_centavos=preco_centavos,
            estoque_atual=estoque_atual,
            estoque_reservado=0,
            estoque_minimo=estoque_minimo,
            localizacao=localizacao,
        )
        if peca.localizacao not in self.grafo_deposito.conexoes:
            raise ValueError(
                f"A localização '{peca.localizacao}' não existe no mapa. "
                "Cadastre primeiro uma conexão para esse setor no menu do depósito."
            )

        self.banco.salvar_peca(peca)
        self.tabela_hash.inserir(peca.sku, peca)

        return peca

    def atualizar_peca(
        self,
        sku: str,
        nome: str,
        categoria: str,
        fabricante: str,
        preco_centavos: int,
        localizacao: str,
    ) -> Peca:
        """Atualiza os dados descritivos sem alterar saldos nem movimentos de estoque."""
        peca = self.buscar_peca_sku(sku)
        if peca is None:
            raise ValueError(f"Peça com SKU '{sku}' não encontrada.")
        atualizada = self._copiar_peca(
            peca,
            nome=nome.strip() if isinstance(nome, str) else nome,
            categoria=categoria.strip() if isinstance(categoria, str) else categoria,
            fabricante=fabricante.strip() if isinstance(fabricante, str) else fabricante,
            preco_centavos=preco_centavos,
            localizacao=localizacao.strip().upper() if isinstance(localizacao, str) else localizacao,
        )
        if atualizada.localizacao not in self.grafo_deposito.conexoes:
            raise ValueError(
                f"A localização '{atualizada.localizacao}' não existe no mapa. "
                "Cadastre primeiro uma conexão para esse setor no menu do depósito."
            )

        self.banco.atualizar_peca(atualizada)
        self.tabela_hash.inserir(atualizada.sku, atualizada)
        return atualizada

    def buscar_peca_sku(self, sku: str) -> Peca | None:
        """Busca uma peça via Tabela Hash em O(1) médio."""
        return self.tabela_hash.buscar(sku)

    def listar_pecas(self) -> list[Peca]:
        """Retorna todas as peças cadastradas."""
        return self.banco.carregar_todas_pecas()

    def pesquisar_pecas(self, termo: str) -> list[Peca]:
        """Pesquisa peças por nome ou categoria (case-insensitive)."""
        termo_clean = termo.strip().lower()
        if not termo_clean:
            return self.listar_pecas()

        todas = self.listar_pecas()
        return [
            p for p in todas
            if termo_clean in p.nome.lower() or termo_clean in p.categoria.lower() or termo_clean in p.sku.lower()
        ]

    def listar_pecas_ordem_alfabetica(self, por_campo: str = "nome") -> list[Peca]:
        """
        Retorna as peças cadastradas ordenadas alfabeticamente (A-Z).
        Permite ordenar por 'nome' (padrão) ou por 'sku'.
        """
        todas = self.listar_pecas()
        if por_campo.strip().lower() == "sku":
            return sorted(todas, key=lambda p: p.sku)
        return sorted(todas, key=lambda p: p.nome.lower())

    def obter_resumo_estatistico(self) -> dict:
        """
        Gera um relatório consolidado com indicadores estratégicos de desempenho do depósito.
        """
        pecas = self.listar_pecas()
        total_skus = len(pecas)
        total_unidades_fisicas = sum(p.estoque_atual for p in pecas)
        total_unidades_reservadas = sum(p.estoque_reservado for p in pecas)
        valor_patrimonio_centavos = sum(p.preco_centavos * p.estoque_atual for p in pecas)

        reais, centavos = divmod(valor_patrimonio_centavos, 100)
        reais_fmt = f"{reais:,}".replace(",", ".")
        valor_formatado = f"R$ {reais_fmt},{centavos:02d}"

        pecas_abaixo_minimo = [p for p in pecas if p.abaixo_do_minimo]
        peca_mais_valiosa = max(pecas, key=lambda p: p.preco_centavos) if pecas else None

        pedidos = self.banco.carregar_pedidos()
        pedidos_abertos = [p for p in pedidos if p.status == "ABERTO"]
        pedidos_separados = [p for p in pedidos if p.status == "SEPARADO"]
        pedidos_expedidos = [p for p in pedidos if p.status == "EXPEDIDO"]

        return {
            "total_skus": total_skus,
            "total_unidades_fisicas": total_unidades_fisicas,
            "total_unidades_reservadas": total_unidades_reservadas,
            "valor_patrimonio_formatado": valor_formatado,
            "qtd_abaixo_minimo": len(pecas_abaixo_minimo),
            "peca_mais_valiosa": peca_mais_valiosa,
            "qtd_pedidos_abertos": len(pedidos_abertos),
            "qtd_pedidos_separados": len(pedidos_separados),
            "qtd_pedidos_expedidos": len(pedidos_expedidos),
            "setores_cadastrados": len(self.grafo_deposito.conexoes),
        }

    # --- GESTÃO DE ESTOQUE E RASTREABILIDADE ---

    def registrar_entrada(self, sku: str, quantidade: int, observacao: str = "Recebimento de lote") -> Peca:
        """Registra a entrada de novas peças no estoque."""
        peca = self.buscar_peca_sku(sku)
        if not peca:
            raise ValueError(f"Peça com SKU '{sku}' não encontrada.")
        if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade <= 0:
            raise ValueError("A quantidade de entrada deve ser maior que zero.")

        atualizada = self._copiar_peca(peca, estoque_atual=peca.estoque_atual + quantidade)
        mov = Movimentacao(None, peca.sku, quantidade, "ENTRADA", observacao)
        self.banco.salvar_operacao_estoque([atualizada], [mov])
        self.tabela_hash.inserir(atualizada.sku, atualizada)

        # Empilha ação reversível para permitir desfazer
        self.pilha_undo.empilhar(AcaoReversivel("ENTRADA", peca.sku, quantidade, observacao))

        return atualizada

    def registrar_ajuste(self, sku: str, quantidade_ajuste: int, observacao: str = "Ajuste manual de estoque") -> Peca:
        """
        Ajusta o estoque atual de uma peça (pode ser positivo para ganho ou negativo para perda/quebra).
        """
        peca = self.buscar_peca_sku(sku)
        if not peca:
            raise ValueError(f"Peça com SKU '{sku}' não encontrada.")
        if (
            not isinstance(quantidade_ajuste, int)
            or isinstance(quantidade_ajuste, bool)
            or quantidade_ajuste == 0
        ):
            raise ValueError("O ajuste deve ser um inteiro diferente de zero.")

        novo_estoque = peca.estoque_atual + quantidade_ajuste
        if novo_estoque < peca.estoque_reservado:
            raise ValueError(
                f"O estoque atual ({novo_estoque}) não pode ficar abaixo da quantidade reservada para pedidos ({peca.estoque_reservado})."
            )
        if novo_estoque < 0:
            raise ValueError("O estoque atual não pode ser negativo.")

        atualizada = self._copiar_peca(peca, estoque_atual=novo_estoque)

        qtd_mov = abs(quantidade_ajuste)
        mov = Movimentacao(None, peca.sku, qtd_mov, "AJUSTE", f"{observacao} (delta: {quantidade_ajuste:+d})")
        self.banco.salvar_operacao_estoque([atualizada], [mov])
        self.tabela_hash.inserir(atualizada.sku, atualizada)

        # Empilha ação reversível
        self.pilha_undo.empilhar(AcaoReversivel("AJUSTE", peca.sku, quantidade_ajuste, observacao))

        return atualizada

    def listar_movimentacoes(self, sku: str | None = None) -> list[Movimentacao]:
        """Retorna a trilha de movimentações do estoque."""
        return self.banco.carregar_movimentacoes(sku)

    def listar_abaixo_minimo(self) -> list[Peca]:
        """Retorna todas as peças que estão abaixo do nível de estoque mínimo."""
        todas = self.listar_pecas()
        return [p for p in todas if p.abaixo_do_minimo]

    # --- DESFAZER OPERAÇÕES (PILHA LIFO) ---

    def desfazer_ultima_operacao(self) -> str:
        """
        Desfaz a última operação de estoque reversível (ENTRADA ou AJUSTE) mantendo a consistência do banco.
        """
        acao = self.pilha_undo.espiar()
        if not acao:
            raise ValueError("Não há nenhuma operação reversível no histórico para desfazer.")

        peca = self.buscar_peca_sku(acao.sku)
        if not peca:
            raise ValueError(f"Não foi possível desfazer: Peça '{acao.sku}' não encontrada.")

        if acao.tipo_acao == "ENTRADA":
            if peca.estoque_disponivel < acao.quantidade:
                raise ValueError(
                    f"Não é possível desfazer a entrada de {acao.quantidade} unidades do SKU '{peca.sku}' "
                    f"pois parte desse lote já foi reservada ou expedida."
                )
            novo_estoque = peca.estoque_atual - acao.quantidade
            msg = f"Desfeita Entrada de {acao.quantidade}x unidades do SKU '{peca.sku}'."
            mov_tipo = "SAIDA"

        elif acao.tipo_acao == "AJUSTE":
            # Inverte o ajuste
            novo_estoque = peca.estoque_atual - acao.quantidade
            if novo_estoque < peca.estoque_reservado or novo_estoque < 0:
                raise ValueError(f"Não foi possível reverter o ajuste de {acao.quantidade}x do SKU '{peca.sku}': Estoque ficaria inconsistente.")
            msg = f"Desfeito Ajuste de {acao.quantidade:+d} unidades do SKU '{peca.sku}'."
            mov_tipo = "AJUSTE"
        else:
            raise ValueError(f"Tipo de ação desconhecido para desfazer: {acao.tipo_acao}")

        # Grava na trilha de movimentação
        mov = Movimentacao(None, peca.sku, abs(acao.quantidade), mov_tipo, f"[DESFAZER] Reversão da ação de {acao.tipo_acao}")
        atualizada = self._copiar_peca(peca, estoque_atual=novo_estoque)
        self.banco.salvar_operacao_estoque([atualizada], [mov])
        self.pilha_undo.desempilhar()
        self.tabela_hash.inserir(atualizada.sku, atualizada)

        return msg

    # --- GESTÃO DE PEDIDOS E EXPEDIÇÃO ---

    def criar_pedido(self, id_pedido: str, cliente: str, itens: list[tuple[str, int]], urgencia: int = 2) -> Pedido:
        """Cria um novo pedido de peças."""
        if not isinstance(id_pedido, str) or not id_pedido.strip():
            raise ValueError("O ID do pedido não pode ficar vazio.")
        pid = id_pedido.strip().upper()
        pedidos_existentes = self.banco.carregar_pedidos()
        if any(p.id_pedido == pid for p in pedidos_existentes):
            raise ValueError(f"Já existe um pedido com o ID '{pid}'.")

        quantidades: dict[str, int] = {}
        for sku, qtd in itens:
            peca = self.buscar_peca_sku(sku)
            if not peca:
                raise ValueError(f"Item inválido: Peça SKU '{sku}' não encontrada no catálogo.")
            if not isinstance(qtd, int) or isinstance(qtd, bool) or qtd <= 0:
                raise ValueError(f"A quantidade da peça '{peca.sku}' deve ser um inteiro positivo.")
            quantidades[peca.sku] = quantidades.get(peca.sku, 0) + qtd

        itens_pedido = [
            ItemPedido(sku=sku, quantidade=quantidade)
            for sku, quantidade in quantidades.items()
        ]

        self.contador_ordem_pedidos += 1
        pedido = Pedido(
            id_pedido=pid,
            cliente=cliente,
            itens=itens_pedido,
            urgencia=urgencia,
            ordem_chegada=self.contador_ordem_pedidos,
            status="ABERTO",
        )

        self.banco.salvar_pedido(pedido)
        self.heap_pedidos.inserir((pedido.urgencia, pedido.ordem_chegada, pedido.id_pedido))

        return pedido

    def consultar_pedido(self, id_pedido: str) -> Pedido | None:
        """Consulta um pedido por ID."""
        pid = id_pedido.strip().upper()
        pedidos = self.banco.carregar_pedidos()
        for p in pedidos:
            if p.id_pedido == pid:
                return p
        return None

    def listar_pedidos(self) -> list[Pedido]:
        """Retorna todos os pedidos cadastrados."""
        return self.banco.carregar_pedidos()

    def separar_pedido(self, id_pedido: str) -> tuple[Pedido, dict[str, list[str]]]:
        """
        Separa um pedido aberto:
          1. Valida disponibilidade de estoque para todos os itens.
          2. Calcula o percurso de coleta via BFS do Grafo de setores.
          3. Se um setor for inalcançável, bloqueia a separação.
          4. Reserva o estoque das peças e altera o status do pedido para SEPARADO.
        """
        pedido = self.consultar_pedido(id_pedido)
        if not pedido:
            raise ValueError(f"Pedido '{id_pedido}' não encontrado.")
        if pedido.status != "ABERTO":
            raise ValueError(f"Pedido '{pedido.id_pedido}' não está em aberto (status atual: {pedido.status}).")
        proximo = self.heap_pedidos.consultar_min()
        if proximo is None or proximo[2] != pedido.id_pedido:
            if proximo is None:
                raise RuntimeError("A fila de separação está inconsistente: não há pedido aberto na fila.")
            raise ValueError(
                f"O pedido '{proximo[2]}' tem prioridade de separação antes de '{pedido.id_pedido}'."
            )

        # 1. Validação de estoque disponível
        for item in pedido.itens:
            peca = self.buscar_peca_sku(item.sku)
            if not peca or peca.estoque_disponivel < item.quantidade:
                disp = peca.estoque_disponivel if peca else 0
                raise ValueError(
                    f"Estoque insuficiente para a peça '{item.sku}'. "
                    f"Necessário: {item.quantidade}, Disponível: {disp}."
                )

        # 2. Validação de rotas de coleta no depósito (Grafo + BFS)
        rotas_coleta: dict[str, list[str]] = {}
        for item in pedido.itens:
            peca = self.buscar_peca_sku(item.sku)
            rota = self.grafo_deposito.bfs("EXPEDICAO", peca.localizacao)
            if not rota:
                raise ValueError(
                    f"Não foi possível calcular rota até a localização '{peca.localizacao}' da peça '{item.sku}'. "
                    f"O setor pode estar desconectado no layout do depósito."
                )
            rotas_coleta[item.sku] = rota

        # 3. Reserva o estoque das peças
        pecas_atualizadas: dict[str, Peca] = {}
        movimentacoes: list[Movimentacao] = []
        for item in pedido.itens:
            peca = self.buscar_peca_sku(item.sku)
            atualizada = self._copiar_peca(
                peca,
                estoque_reservado=peca.estoque_reservado + item.quantidade,
            )
            pecas_atualizadas[peca.sku] = atualizada
            movimentacoes.append(
                Movimentacao(
                    None,
                    peca.sku,
                    item.quantidade,
                    "RESERVA",
                    f"Reserva para o Pedido #{pedido.id_pedido}",
                )
            )

        # 4. Atualiza status do pedido
        pedido.status = "SEPARADO"
        self.banco.salvar_operacao_estoque(
            list(pecas_atualizadas.values()),
            movimentacoes,
            pedido,
        )
        for peca in pecas_atualizadas.values():
            self.tabela_hash.inserir(peca.sku, peca)

        # Remove do Heap de pendentes
        self.carregar_dados()

        return pedido, rotas_coleta

    def expedir_pedido(self, id_pedido: str) -> Pedido:
        """
        Expede um pedido previamente separado:
          1. Baixa o estoque atual e limpa a reserva (evita contar a saída duas vezes).
          2. Altera o status do pedido para EXPEDIDO.
        """
        pedido = self.consultar_pedido(id_pedido)
        if not pedido:
            raise ValueError(f"Pedido '{id_pedido}' não encontrado.")
        if pedido.status != "SEPARADO":
            raise ValueError(f"Apenas pedidos com status 'SEPARADO' podem ser expedidos (status atual: {pedido.status}).")

        pecas_atualizadas: dict[str, Peca] = {}
        movimentacoes: list[Movimentacao] = []
        for item in pedido.itens:
            peca = self.buscar_peca_sku(item.sku)
            if peca is None:
                raise RuntimeError(f"A peça '{item.sku}' do pedido não existe no catálogo.")
            if peca.estoque_reservado < item.quantidade or peca.estoque_atual < item.quantidade:
                raise RuntimeError(f"A reserva da peça '{item.sku}' está inconsistente.")
            pecas_atualizadas[peca.sku] = self._copiar_peca(
                peca,
                estoque_atual=peca.estoque_atual - item.quantidade,
                estoque_reservado=peca.estoque_reservado - item.quantidade,
            )
            movimentacoes.append(
                Movimentacao(
                    None,
                    peca.sku,
                    item.quantidade,
                    "SAIDA",
                    f"Expedição do Pedido #{pedido.id_pedido}",
                )
            )

        pedido.status = "EXPEDIDO"
        self.banco.salvar_operacao_estoque(
            list(pecas_atualizadas.values()),
            movimentacoes,
            pedido,
        )
        for peca in pecas_atualizadas.values():
            self.tabela_hash.inserir(peca.sku, peca)
        return pedido

    def cancelar_pedido(self, id_pedido: str) -> Pedido:
        """
        Cancela um pedido:
          - Se o pedido estiver SEPARADO, libera a reserva de estoque de volta para o estoque disponível.
          - Altera status para CANCELADO.
        """
        pedido = self.consultar_pedido(id_pedido)
        if not pedido:
            raise ValueError(f"Pedido '{id_pedido}' não encontrado.")
        if pedido.status == "EXPEDIDO":
            raise ValueError("Não é possível cancelar um pedido que já foi expedido.")
        if pedido.status == "CANCELADO":
            raise ValueError("O pedido já está cancelado.")

        pecas_atualizadas: dict[str, Peca] = {}
        movimentacoes: list[Movimentacao] = []
        if pedido.status == "SEPARADO":
            for item in pedido.itens:
                peca = self.buscar_peca_sku(item.sku)
                if peca is None or peca.estoque_reservado < item.quantidade:
                    raise RuntimeError(f"A reserva da peça '{item.sku}' está inconsistente.")
                pecas_atualizadas[peca.sku] = self._copiar_peca(
                    peca,
                    estoque_reservado=peca.estoque_reservado - item.quantidade,
                )
                movimentacoes.append(
                    Movimentacao(
                        None,
                        peca.sku,
                        item.quantidade,
                        "LIBERACAO",
                        f"Cancelamento do Pedido #{pedido.id_pedido}",
                    )
                )

        pedido.status = "CANCELADO"
        self.banco.salvar_operacao_estoque(
            list(pecas_atualizadas.values()),
            movimentacoes,
            pedido,
        )
        for peca in pecas_atualizadas.values():
            self.tabela_hash.inserir(peca.sku, peca)
        self.carregar_dados()
        return pedido
