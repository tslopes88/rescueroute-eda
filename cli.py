"""
Interface em Linha de Comando (CLI) para o sistema de controle de estoque de peças de computador.
"""

from decimal import Decimal, InvalidOperation

from servicos import GerenciadorEstoque


def ler_inteiro(
    mensagem: str,
    minimo: int | None = None,
    maximo: int | None = None,
) -> int:
    """Lê um número inteiro da entrada do usuário com tratamento de exceções."""
    while True:
        try:
            valor_raw = input(mensagem).strip()
            valor = int(valor_raw)
            if minimo is not None and valor < minimo:
                print(f"⚠️ O valor deve ser no mínimo {minimo}.")
                continue
            if maximo is not None and valor > maximo:
                print(f"⚠️ O valor deve ser no máximo {maximo}.")
                continue
            return valor
        except ValueError:
            print("⚠️ Entrada inválida. Por favor, digite um número inteiro válido.")


def ler_float_centavos(mensagem: str) -> int:
    """Lê Reais em formato brasileiro ou decimal com ponto e retorna centavos exatos."""
    while True:
        try:
            return converter_reais_centavos(input(mensagem))
        except ValueError as err:
            print(f"⚠️ {err}")


def converter_reais_centavos(texto: str) -> int:
    """Converte uma quantia digitada para centavos sem arredondamento implícito."""
    valor_txt = texto.strip().upper().replace("R$", "").replace(" ", "")
    try:
        if "," in valor_txt:
            valor_txt = valor_txt.replace(".", "").replace(",", ".")
        valor = Decimal(valor_txt)
    except InvalidOperation as err:
        raise ValueError("Digite Reais (ex: 1.299,90 ou 1299.90).") from err
    if not valor.is_finite():
        raise ValueError("O valor precisa ser um número finito.")
    if valor < 0:
        raise ValueError("O valor monetário não pode ser negativo.")
    if valor.as_tuple().exponent < -2:
        raise ValueError("Informe no máximo duas casas decimais.")
    return int(valor * 100)


class InterfaceCLI:
    """
    Controlador do menu interativo do terminal.
    """

    def __init__(self, db_path: str = "estoque.db"):
        self.gerenciador = GerenciadorEstoque(db_path)

    def iniciar(self) -> None:
        """Inicia o loop principal do menu."""

        banner_ascii = r"""
  ████████╗███████╗██╗  ██╗██████╗ ███████╗██████╗  ██████╗ ████████╗
  ╚══██╔══╝██╔════╝██║  ██║██╔══██╗██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝
     ██║   █████╗  ███████║██║  ██║█████╗  ██████╔╝██║   ██║   ██║   
     ██║   ██╔══╝  ██╔══██║██║  ██║██╔══╝  ██╔═══╝ ██║   ██║   ██║   
     ██║   ███████╗██║  ██║██████╔╝███████╗██║     ╚██████╔╝   ██║   
     ╚═╝   ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝      ╚═════╝    ╚═╝   
       LOGISTICS — SISTEMA TÁTICO DE ESTOQUE E EXPEDIÇÃO DE HARDWARE
"""
        print(banner_ascii)
        print("╔" + "═" * 67 + "╗")
        print("║  👉 BEM-VINDO AO TECHDEPOT LOGISTICS!                              ║")
        print("║     DIGITE 1 A QUALQUER MOMENTO PARA O GUIA E PASSO A PASSO.       ║")
        print("╚" + "═" * 67 + "╝")

        if not self.gerenciador.listar_pecas():
            print(
                "\nℹ️ O catálogo está vazio. Cadastre suas peças ou use a opção 8 "
                "para carregar itens de demonstração."
            )

        ver_guia = input("\n👉 Deseja visualizar o PASSO A PASSO de uso agora? [S/n]: ").strip().lower()
        if ver_guia in ("", "s", "sim", "y", "1"):
            self.menu_tutorial()

        while True:
            print("\n" + "=" * 69)
            print("  💻 TECHDEPOT LOGISTICS — MENU PRINCIPAL DE GESTÃO DE HARDWARE")
            print("=" * 69)
            print("1. ❓ PASSO A PASSO E GUIA DE USO DO SISTEMA (TUTORIAL COMPLETO)")
            print("2. 📊 Dashboard e Indicadores Gerais do Depósito (Visão Geral)")
            print("3. 📦 Catálogo de Peças (Cadastrar, Consultar SKU, Pesquisar, A-Z)")
            print("4. 📋 Gestão de Estoque (Entradas, Ajustes, Histórico e Desfazer)")
            print("5. 📑 Gestão de Pedidos (Criar, Separar com Rota BFS, Expedir)")
            print("6. 🗺️  Layout do Depósito e Rotas de Coleta")
            print("7. ⚠️ Alertas e Relatório de Estoque Mínimo")
            print("8. 🔄 Carregar Peças de Demonstração (opcional)")
            print("0. 🚪 Sair")
            print("-" * 69)

            opcao = input("Escolha uma opção (0-8): ").strip()

            if opcao == "1":
                self.menu_tutorial()
            elif opcao == "2":
                self.menu_dashboard()
            elif opcao == "3":
                self.menu_catalogo()
            elif opcao == "4":
                self.menu_estoque()
            elif opcao == "5":
                self.menu_pedidos()
            elif opcao == "6":
                self.menu_deposito()
            elif opcao == "7":
                self.menu_alertas()
            elif opcao == "8":
                self._popular_dados_demonstrativos()
            elif opcao == "0":
                print("\n👋 Encerrando o sistema TechDepot Logistics. Até logo!")
                break
            else:
                print("⚠️ Opção inválida. Digite um número de 0 a 8.")

    def menu_dashboard(self) -> None:
        """Exibe o painel estatístico com indicadores estratégicos do depósito."""
        dados = self.gerenciador.obter_resumo_estatistico()
        print("\n" + "=" * 69)
        print("  📊 TECHDEPOT LOGISTICS — DASHBOARD E INDICADORES GERAIS")
        print("=" * 69)
        print(f"  📦 Total de Peças (SKUs Distintos): {dados['total_skus']}")
        print(f"  🏭 Total de Unidades Físicas:       {dados['total_unidades_fisicas']} unidades")
        print(f"  🔒 Unidades Reservadas em Pedidos: {dados['total_unidades_reservadas']} unidades")
        print(f"  💰 Valor Patrimonial em Estoque:    {dados['valor_patrimonio_formatado']}")
        print(f"  ⚠️ Peças em Estoque Crítico:       {dados['qtd_abaixo_minimo']} item(ns)")
        print(f"  🗺️  Setores Conectados no Depósito: {dados['setores_cadastrados']}")
        print("-" * 69)
        print(f"  📑 Pedidos Pendentes (Em Aberto):  {dados['qtd_pedidos_abertos']}")
        print(f"  📦 Pedidos Separados (Reservados): {dados['qtd_pedidos_separados']}")
        print(f"  🚚 Pedidos Expedidos (Concluídos):  {dados['qtd_pedidos_expedidos']}")
        if dados["peca_mais_valiosa"]:
            pm = dados["peca_mais_valiosa"]
            print(f"  💎 Peça de Maior Valor Unitário:   [{pm.sku}] {pm.nome} ({pm.preco_formatado})")
        print("=" * 69)
        input("\nPressione ENTER para voltar ao Menu Principal...")

    def _popular_dados_demonstrativos(self) -> None:
        """Inclui peças de demonstração apenas quando o usuário escolhe essa opção."""
        print("\n[*] Incluindo peças de demonstração que ainda não existem no catálogo...")

        pecas_demo = [
            ("RAM-DDR4-8GB", "Memória RAM DDR4 8GB 3200MHz", "Memória", "Kingston", 14990, 25, 10, "CORREDOR-A"),
            ("RAM-DDR5-32GB", "Memória RAM DDR5 32GB (2x16GB) 6000MHz", "Memória", "Corsair", 89990, 18, 6, "CORREDOR-A"),
            ("SSD-NVME-1TB", "SSD NVMe M.2 1TB PCIe 4.0", "Armazenamento", "Crucial", 38900, 12, 5, "CORREDOR-B"),
            ("SSD-SATA-480GB", "SSD SATA III 480GB 2.5\"", "Armazenamento", "SanDisk", 21990, 35, 10, "CORREDOR-B"),
            ("GPU-RTX-4060", "Placa de Vídeo GeForce RTX 4060 8GB", "Placa de Vídeo", "ASUS", 219900, 4, 5, "SETOR-PLACAS"),
            ("GPU-RX-7600", "Placa de Vídeo Radeon RX 7600 8GB", "Placa de Vídeo", "ASRock", 169900, 6, 4, "SETOR-PLACAS"),
            ("CPU-I5-13400", "Processador Intel Core i5-13400F", "Processadores", "Intel", 115000, 8, 3, "CORREDOR-C"),
            ("CPU-RYZEN-5700X", "Processador AMD Ryzen 7 5700X 3.4GHz", "Processadores", "AMD", 119900, 15, 4, "CORREDOR-C"),
            ("PLACA-B550M-MSI", "Placa-Mãe MSI B550M Pro-VDH WiFi", "Placa-Mãe", "MSI", 68990, 10, 3, "SETOR-PLACAS"),
            ("PLACA-Z790-ASUS", "Placa-Mãe ASUS ROG Strix Z790-F Gaming", "Placa-Mãe", "ASUS", 249900, 3, 2, "SETOR-PLACAS"),
            ("FONTE-750W", "Fonte de Alimentação 750W 80 Plus Gold", "Energia", "Corsair", 52000, 2, 4, "SETOR-NO-BREAKS"),
            ("FONTE-650W-MSI", "Fonte MSI MAG A650BN 650W 80 Plus Bronze", "Energia", "MSI", 28990, 14, 5, "SETOR-NO-BREAKS"),
            ("COOLER-AG400", "Air Cooler para Processador DeepCool AG400", "Refrigeração", "DeepCool", 13990, 20, 5, "CORREDOR-A"),
            ("WATER-240MM", "Water Cooler 240mm ARGB", "Refrigeração", "Cooler Master", 42990, 7, 3, "CORREDOR-A"),
            ("GABINETE-AIR", "Gabinete Gamer Mid Tower Vidro Temperado", "Gabinetes", "Redragon", 29990, 9, 3, "CORREDOR-C"),
            ("PASTA-TERMICA", "Pasta Térmica High Performance 4g", "Acessórios", "Arctic", 4990, 50, 15, "CORREDOR-A"),
            ("MONITOR-144HZ", "Monitor Gamer 24\" Full HD 144Hz 1ms", "Monitores", "LG", 89900, 8, 3, "CORREDOR-C"),
        ]

        locais_necessarios = {item[7] for item in pecas_demo}
        locais_ausentes = sorted(locais_necessarios - self.gerenciador.grafo_deposito.conexoes.keys())
        if locais_ausentes:
            print(
                "⚠️ Antes de carregar os exemplos, conecte estes setores ao mapa: "
                + ", ".join(locais_ausentes)
            )
            return

        adicionadas = 0
        existentes = 0
        for sku, nome, cat, fab, preco, est, est_min, loc in pecas_demo:
            if self.gerenciador.buscar_peca_sku(sku) is not None:
                existentes += 1
                continue
            self.gerenciador.cadastrar_peca(
                sku=sku,
                nome=nome,
                categoria=cat,
                fabricante=fab,
                preco_centavos=preco,
                estoque_atual=est,
                estoque_minimo=est_min,
                localizacao=loc,
            )
            adicionadas += 1

        print(f"✅ {adicionadas} nova(s) peça(s) agregada(s) ao estoque com sucesso!")
        if existentes:
            print(f"ℹ️ {existentes} peça(s) de demonstração já estavam cadastradas e não foram alteradas.")
        print(f"📦 Total atual no catálogo: {len(self.gerenciador.listar_pecas())} itens.")

    # --- MENUS SECUNDÁRIOS ---

    def menu_catalogo(self) -> None:
        while True:
            print("\n--- 📦 MENU DE CATÁLOGO DE PEÇAS ---")
            print("1. Cadastrar Nova Peça")
            print("2. Consultar Peça por SKU (Tabela Hash O(1))")
            print("3. Pesquisar por Nome/Categoria")
            print("4. Listar Todas as Peças")
            print("5. Atualizar Dados de uma Peça")
            print("6. Listar Peças em Ordem Alfabética (A-Z)")
            print("0. Voltar ao Menu Principal")

            op = input("Escolha uma opção (0-6): ").strip()
            if op == "1":
                sku = input("Digite o SKU único (ex: GPU-RTX-3060): ").strip()
                nome = input("Nome do produto: ").strip()
                categoria = input("Categoria (ex: Placa de Vídeo, RAM): ").strip()
                fabricante = input("Fabricante: ").strip()
                preco_c = ler_float_centavos("Preço em Reais (ex: 299.90): ")
                est_atual = ler_inteiro("Estoque Inicial: ", minimo=0)
                est_min = ler_inteiro("Estoque Mínimo para Alerta: ", minimo=0)
                local = input("Setor/Corredor no Depósito (ex: CORREDOR-A): ").strip()

                try:
                    peca = self.gerenciador.cadastrar_peca(
                        sku=sku,
                        nome=nome,
                        categoria=categoria,
                        fabricante=fabricante,
                        preco_centavos=preco_c,
                        estoque_atual=est_atual,
                        estoque_minimo=est_min,
                        localizacao=local,
                    )
                    print(f"\n✅ Peça cadastrada com sucesso! {peca}")
                except ValueError as err:
                    print(f"❌ Erro ao cadastrar peça: {err}")

            elif op == "2":
                sku = input("Digite o SKU para busca direta na Tabela Hash: ").strip()
                peca = self.gerenciador.buscar_peca_sku(sku)
                if peca:
                    print("\n🔍 Resultado da Tabela Hash O(1):")
                    print(f"  • SKU: {peca.sku}")
                    print(f"  • Nome: {peca.nome}")
                    print(f"  • Categoria: {peca.categoria} | Fabricante: {peca.fabricante}")
                    print(f"  • Preço: {peca.preco_formatado}")
                    print(f"  • Estoque Físico: {peca.estoque_atual} | Reservado: {peca.estoque_reservado} | Livre: {peca.estoque_disponivel}")
                    print(f"  • Localização no Depósito: {peca.localizacao}")
                else:
                    print(f"⚠️ Nenhuma peça encontrada com o SKU '{sku}'.")

            elif op == "3":
                termo = input("Digite o nome ou categoria para pesquisar: ").strip()
                res = self.gerenciador.pesquisar_pecas(termo)
                print(f"\nEncontradas {len(res)} peça(s):")
                for p in res:
                    print(f"  - [{p.sku}] {p.nome} ({p.categoria}) | Preço: {p.preco_formatado} | Est: {p.estoque_atual} | Local: {p.localizacao}")

            elif op == "4":
                pecas = self.gerenciador.listar_pecas()
                print(f"\n--- TOTAL DE PEÇAS NO CATÁLOGO: {len(pecas)} ---")
                for p in pecas:
                    alert = " ⚠️ [ESTOQUE BAIXO]" if p.abaixo_do_minimo else ""
                    print(f"  - [{p.sku:<16}] {p.nome:<45} | {p.preco_formatado:<11} | Est: {p.estoque_atual:<3} (Livre: {p.estoque_disponivel:<3}) | Local: {p.localizacao}{alert}")

            elif op == "5":
                sku = input("SKU da peça que deseja atualizar: ").strip()
                atual = self.gerenciador.buscar_peca_sku(sku)
                if atual is None:
                    print(f"⚠️ Nenhuma peça encontrada com o SKU '{sku}'.")
                    continue
                print("Deixe um campo em branco para manter o valor atual.")
                nome = input(f"Nome [{atual.nome}]: ").strip() or atual.nome
                categoria = input(f"Categoria [{atual.categoria}]: ").strip() or atual.categoria
                fabricante = input(f"Fabricante [{atual.fabricante}]: ").strip() or atual.fabricante
                preco_txt = input(f"Preço em Reais [{atual.preco_formatado}]: ").strip()
                if preco_txt:
                    try:
                        preco_centavos = converter_reais_centavos(preco_txt)
                    except ValueError as err:
                        print(f"⚠️ {err}")
                        continue
                else:
                    preco_centavos = atual.preco_centavos
                localizacao = input(f"Setor [{atual.localizacao}]: ").strip() or atual.localizacao
                try:
                    atualizada = self.gerenciador.atualizar_peca(
                        sku, nome, categoria, fabricante, preco_centavos, localizacao
                    )
                    print(f"✅ Dados atualizados: {atualizada}")
                except ValueError as err:
                    print(f"❌ Erro ao atualizar peça: {err}")

            elif op == "6":
                print("\n--- 🔤 PEÇAS EM ORDEM ALFABÉTICA (A-Z) ---")
                print("1. Ordenar por Nome do Produto")
                print("2. Ordenar por SKU")
                c_op = input("Escolha o campo de ordenação (1 ou 2): ").strip()
                campo = "sku" if c_op == "2" else "nome"
                pecas_ord = self.gerenciador.listar_pecas_ordem_alfabetica(por_campo=campo)
                print(f"\n--- {len(pecas_ord)} PEÇA(S) ORDENADA(S) POR {campo.upper()} (A-Z) ---")
                for p in pecas_ord:
                    alert = " ⚠️ [ESTOQUE BAIXO]" if p.abaixo_do_minimo else ""
                    print(f"  - [{p.sku:<16}] {p.nome:<45} | {p.preco_formatado:<11} | Est: {p.estoque_atual:<3} | Local: {p.localizacao}{alert}")

            elif op == "0":
                break
            else:
                print("⚠️ Opção inválida. Escolha uma opção entre 0 e 6.")

    def menu_estoque(self) -> None:
        while True:
            print("\n--- 📊 MENU DE GESTÃO DE ESTOQUE E RASTREABILIDADE ---")
            print("1. Registrar Entrada de Mercadoria (Recebimento)")
            print("2. Registrar Ajuste Manual de Estoque (Ganho/Perda)")
            print("3. Ver Histórico de Movimentações (Trilha de Rastreabilidade)")
            print("4. ↩️ Desfazer Última Operação (Pilha LIFO Encadeada)")
            print("0. Voltar ao Menu Principal")

            op = input("Escolha uma opção (0-4): ").strip()
            if op == "1":
                sku = input("SKU da peça recebida: ").strip()
                qtd = ler_inteiro("Quantidade recebida: ", minimo=1)
                obs = input("Observação/Nota Fiscal (opcional): ").strip()
                try:
                    peca = self.gerenciador.registrar_entrada(sku, qtd, obs or "Recebimento")
                    print(f"✅ Entrada registrada com sucesso! Novo estoque de '{peca.sku}': {peca.estoque_atual}")
                except ValueError as err:
                    print(f"❌ Erro ao registrar entrada: {err}")

            elif op == "2":
                sku = input("SKU da peça para ajuste: ").strip()
                print("Digite a variação (ex: 5 para adicionar 5 unidades, -2 para remover 2 por avaria):")
                qtd_delta = ler_inteiro("Variação do ajuste: ")
                obs = input("Motivo do ajuste: ").strip()
                try:
                    peca = self.gerenciador.registrar_ajuste(sku, qtd_delta, obs or "Ajuste manual")
                    print(f"✅ Ajuste realizado! Novo estoque atual de '{peca.sku}': {peca.estoque_atual}")
                except ValueError as err:
                    print(f"❌ Erro ao realizar ajuste: {err}")

            elif op == "3":
                sku_filtro = input("Filtrar por SKU (deixe em branco para ver todos): ").strip()
                movs = self.gerenciador.listar_movimentacoes(sku_filtro if sku_filtro else None)
                print(f"\n--- HISTÓRICO DE MOVIMENTAÇÕES ({len(movs)} registros) ---")
                for m in movs:
                    print(f"  [{m.timestamp}] {m.tipo:<9} | SKU: {m.sku:<16} | Qtd: {m.quantidade:<3} | Obs: {m.observacao}")

            elif op == "4":
                try:
                    msg = self.gerenciador.desfazer_ultima_operacao()
                    print(f"✅ {msg}")
                except ValueError as err:
                    print(f"⚠️ Não foi possível desfazer: {err}")

            elif op == "0":
                break
            else:
                print("⚠️ Opção inválida. Escolha uma opção entre 0 e 4.")

    def menu_pedidos(self) -> None:
        while True:
            print("\n--- 📑 MENU DE GESTÃO DE PEDIDOS E EXPEDIÇÃO ---")
            print("1. Criar Novo Pedido de Clientes")
            print("2. Separar Pedido (Reservar Estoque e Gerar Rota BFS no Grafo)")
            print("3. Expedir Pedido (Baixar Estoque Físico e Finalizar)")
            print("4. Cancelar Pedido (Liberar Reserva)")
            print("5. Listar Todos os Pedidos")
            print("0. Voltar ao Menu Principal")

            op = input("Escolha uma opção (0-5): ").strip()
            if op == "1":
                pid = input("Código do Pedido (ex: PED-1001): ").strip()
                cliente = input("Nome do Cliente: ").strip()
                print("Escolha a urgência do pedido:")
                print("  1 - Alta (Urgente / Prioridade Máxima no Heap)")
                print("  2 - Média (Normal)")
                print("  3 - Baixa")
                urg = ler_inteiro("Urgência (1-3): ", minimo=1, maximo=3)

                itens = []
                while True:
                    sku_item = input("\nSKU do item a adicionar (ou deixe em branco para finalizar itens): ").strip()
                    if not sku_item:
                        if not itens:
                            print("⚠️ O pedido precisa de pelo menos 1 item.")
                            continue
                        break
                    peca = self.gerenciador.buscar_peca_sku(sku_item)
                    if not peca:
                        print(f"⚠️ Peça '{sku_item}' não encontrada no catálogo.")
                        continue
                    qtd_item = ler_inteiro(f"Quantidade de '{peca.sku}' ({peca.nome}): ", minimo=1)
                    itens.append((peca.sku, qtd_item))

                try:
                    pedido = self.gerenciador.criar_pedido(pid, cliente, itens, urgencia=urg)
                    print(f"✅ Pedido #{pedido.id_pedido} criado com sucesso e adicionado ao MinHeap de prioridades!")
                except ValueError as err:
                    print(f"❌ Erro ao criar pedido: {err}")

            elif op == "2":
                pid = input("ID do Pedido a separar: ").strip()
                try:
                    pedido, rotas = self.gerenciador.separar_pedido(pid)
                    print(f"\n✅ Pedido #{pedido.id_pedido} SEPARADO e estoque RESERVADO!")
                    print("🗺️  ROTAS DE COLETA CALCULADAS NO DEPÓSITO VIA BFS (Grafo):")
                    for sku, rota in rotas.items():
                        print(f"  • Item SKU [{sku}] -> Rota: {' ➔ '.join(rota)}")
                except ValueError as err:
                    print(f"❌ Falha ao separar pedido: {err}")

            elif op == "3":
                pid = input("ID do Pedido a expedir: ").strip()
                try:
                    pedido = self.gerenciador.expedir_pedido(pid)
                    print(f"✅ Pedido #{pedido.id_pedido} EXPEDIDO com sucesso! Estoque baixado.")
                except ValueError as err:
                    print(f"❌ Erro ao expedir pedido: {err}")

            elif op == "4":
                pid = input("ID do Pedido a cancelar: ").strip()
                try:
                    pedido = self.gerenciador.cancelar_pedido(pid)
                    print(f"✅ Pedido #{pedido.id_pedido} CANCELADO e reservas liberadas.")
                except ValueError as err:
                    print(f"❌ Erro ao cancelar pedido: {err}")

            elif op == "5":
                pedidos = self.gerenciador.listar_pedidos()
                print(f"\n--- LISTA DE PEDIDOS ({len(pedidos)} cadastrados) ---")
                for p in pedidos:
                    itens_str = ", ".join([f"{it.quantidade}x {it.sku}" for it in p.itens])
                    print(f"  • Pedido #{p.id_pedido} | Cliente: {p.cliente} | Status: {p.status:<9} | Urgência: {p.urgencia} | Itens: [{itens_str}]")

            elif op == "0":
                break
            else:
                print("⚠️ Opção inválida. Escolha uma opção entre 0 e 5.")

    def menu_deposito(self) -> None:
        while True:
            print("\n--- 🗺️  MENU DE LAYOUT DO DEPÓSITO E GRAFOS ---")
            print("1. Visualizar Corredores Conectados (Grafo)")
            print("2. Cadastrar Novo Corredor / Conexão no Depósito")
            print("3. Testar Rota BFS entre Dois Setores")
            print("0. Voltar ao Menu Principal")

            op = input("Escolha uma opção (0-3): ").strip()
            if op == "1":
                print("\nMAPA DE ADJACÊNCIA DO DEPÓSITO (GRAFO POR LISTA DE ADJACÊNCIA):")
                for setor, vizinhos in self.gerenciador.grafo_deposito.conexoes.items():
                    print(f"  • Setor [{setor}] ↔ Vizinhos: {', '.join(vizinhos)}")

            elif op == "2":
                p_a = input("Setor Origem (ex: CORREDOR-A): ").strip()
                p_b = input("Setor Destino (ex: CORREDOR-D): ").strip()
                try:
                    self.gerenciador.banco.salvar_via_deposito(p_a, p_b)
                    self.gerenciador.grafo_deposito.adicionar_via(p_a, p_b)
                    print(f"✅ Via cadastrada entre '{p_a.upper()}' e '{p_b.upper()}'.")
                except ValueError as err:
                    print(f"❌ Erro: {err}")

            elif op == "3":
                origem = input("Setor de Origem (ex: EXPEDICAO): ").strip()
                destino = input("Setor de Destino (ex: SETOR-PLACAS): ").strip()
                rota = self.gerenciador.grafo_deposito.bfs(origem, destino)
                if rota:
                    print(f"\n✅ Menor trajeto em conexões (BFS): {' ➔ '.join(rota)} ({len(rota)-1} passos)")
                else:
                    print(f"⚠️ Não há rota acessível entre '{origem}' e '{destino}'.")

            elif op == "0":
                break
            else:
                print("⚠️ Opção inválida. Escolha uma opção entre 0 e 3.")

    def menu_alertas(self) -> None:
        print("\n--- ⚠️ RELATÓRIO DE REPOSIÇÃO E ESTOQUE MÍNIMO ---")
        abaixo = self.gerenciador.listar_abaixo_minimo()
        if not abaixo:
            print("✅ Excelente! Todas as peças estão com níveis de estoque acima do limite mínimo.")
        else:
            print(f"⚠️ ATENÇÃO: {len(abaixo)} peça(s) necessitam de reposição imediata:")
            for p in abaixo:
                print(f"  - SKU: {p.sku:<16} | Nome: {p.nome:<45} | Atual: {p.estoque_atual:<3} | Mínimo: {p.estoque_minimo:<3} | Local: {p.localizacao}")

    def menu_tutorial(self) -> None:
        """Exibe o passo a passo super didático e fácil de entender para iniciantes."""
        print("\n" + "=" * 71)
        print("  [?] GUIA COMPLETO E DIDÁTICO DE USO - TECHDEPOT LOGISTICS")
        print("=" * 71)
        print("Este guia foi feito para você entender o sistema passo a passo,\n"
              "mesmo que nunca tenha trabalhado com logística ou programação!\n")

        print("------------ 💡 1. GLOSSÁRIO DE SIGLAS E TERMOS FÁCEIS ------------")
        print(" • SKU (Stock Keeping Unit): Código único da peça (ex: RAM-DDR4-8GB).")
        print(" • Tabela Hash: Lista de busca rápida que acha o produto direto pelo SKU.")
        print(" • MinHeap (Fila de Urgência): Fila que coloca o pedido urgente no topo.")
        print(" • BFS (Busca em Largura): Algoritmo que acha o menor caminho no depósito.")
        print(" • Pilha LIFO (Último a entrar, Primeiro a sair): Mecanismo de 'Desfazer'.")
        print(" • FIFO (Primeiro a entrar, Primeiro a sair): Ordem de chegada do pedido.\n")

        print("------------ 📌 2. PASSO A PASSO PRÁTICO EM 4 ETAPAS ------------")
        print("ETAPA 1: O CATÁLOGO DE PEÇAS (Opção 3 do Menu Principal)")
        print("  1. Cadastre a peça informando o SKU (ex: GPU-4060), Nome, Preço e Local.")
        print("  2. Para ver todas as peças em ordem alfabética (A-Z), escolha a opção 6.")
        print("  3. Para achar uma peça rápido pelo SKU em tempo recorde, use a opção 2.\n")

        print("ETAPA 2: MOVIMENTAÇÃO E AUDITORIA DE ESTOQUE (Opção 4 do Menu Principal)")
        print("  1. 'Entrada de Mercadoria': Use quando chegarem novas peças da fábrica.")
        print("  2. 'Ajuste Manual': Use se perder uma peça ou precisar corrigir o saldo.")
        print("  3. 'Desfazer Operação': Errou um lançamento? O sistema cancela a última")
        print("     alteração e devolve a quantidade correta para o estoque!\n")

        print("ETAPA 3: O CICLO COMPLETO DE UM PEDIDO DE CLIENTE (Opção 5 do Menu Principal)")
        print("  Passo A (Criar Pedido): Digite o cliente, a Urgência (1-Alta, 2-Média, 3-Baixa)")
        print("          e as peças. O pedido vai para a Fila de Urgência (MinHeap).")
        print("  Passo B (Separar Pedido): O sistema reserva as peças para o cliente e")
        print("          desenha no mapa do depósito o caminho mais curto para coletá-las.")
        print("  Passo C (Expedir Pedido): As peças saem do galpão para entrega e a baixa")
        print("          é finalizada no banco de dados com segurança!\n")

        print("ETAPA 4: NAVEGAÇÃO NO DEPÓSITO E ALERTAS (Opções 2, 6 e 7 do Menu)")
        print("  • Use a Opção 2 (Dashboard) para ver o valor total do estoque em R$.")
        print("  • Use a Opção 6 para ver quais corredores estão conectados no depósito.")
        print("  • Use a Opção 7 para ver o relatório de peças que precisam de reposição.")
        print("=" * 71)
        input("\nPressione ENTER para voltar ao Menu Principal...")
