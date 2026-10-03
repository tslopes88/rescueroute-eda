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
                print(f"[AVISO] O valor deve ser no mínimo {minimo}.")
                continue
            if maximo is not None and valor > maximo:
                print(f"[AVISO] O valor deve ser no máximo {maximo}.")
                continue
            return valor
        except ValueError:
            print("[AVISO] Entrada inválida. Por favor, digite um número inteiro válido.")


def ler_float_centavos(mensagem: str) -> int:
    """Lê Reais em formato brasileiro ou decimal com ponto e retorna centavos exatos."""
    while True:
        try:
            return converter_reais_centavos(input(mensagem))
        except ValueError as err:
            print(f"[AVISO] {err}")


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
    Controlador do menu interativo no terminal.
    """

    def __init__(self, db_path: str = "estoque.db"):
        self.gerenciador = GerenciadorEstoque(db_path)

    def iniciar(self) -> None:
        """Inicia o loop principal do menu."""

        banner = """
===================================================================
                  TECLOGÍSTICA — SISTEMA DE ESTOQUE
       Projeto Final da Disciplina de Estruturas de Dados (EDA)
===================================================================
"""
        print(banner)
        print("+-----------------------------------------------------------------+")
        print("|  BEM-VINDO AO TECLOGÍSTICA                                      |")
        print("|  No menu principal, escolha 1 para abrir o Guia de Uso.         |")
        print("+-----------------------------------------------------------------+")

        if not self.gerenciador.listar_pecas():
            print(
                "\n[INFO] O catálogo está vazio. Cadastre peças ou use a opção 9 "
                "para carregar itens de demonstração."
            )

        ver_guia = input("\nDeseja visualizar o Guia de Uso agora? [S/n]: ").strip().lower()
        if ver_guia in ("", "s", "sim", "y", "1"):
            self.menu_tutorial()

        while True:
            print("\n" + "=" * 67)
            print("  TECLOGÍSTICA — MENU PRINCIPAL DE GESTÃO DE ESTOQUE E LOGÍSTICA")
            print("=" * 67)
            print("1. Guia de Uso e Passo a Passo do Sistema")
            print("2. Dashboard e Indicadores Gerais do Depósito")
            print("3. Catálogo de Peças (Cadastrar, Consultar SKU, Pesquisar, A-Z)")
            print("4. Gestão de Estoque (Entradas, Ajustes, Histórico e Desfazer)")
            print("5. Gestão de Pedidos (Criar, Separar com Rota BFS, Expedir)")
            print("6. Gestão de Vendas e Faturamento (Venda Direta, Relatórios e Ranking)")
            print("7. Layout do Depósito e Rotas de Coleta")
            print("8. Relatório de Estoque Mínimo")
            print("9. Carregar Peças de Demonstração (opcional)")
            print("0. Sair")
            print("-" * 67)

            opcao = input("Escolha uma opção (0-9): ").strip()

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
                self.menu_vendas()
            elif opcao == "7":
                self.menu_deposito()
            elif opcao == "8":
                self.menu_alertas()
            elif opcao == "9":
                self._popular_dados_demonstrativos()
            elif opcao == "0":
                print("\nEncerrando o sistema TecLogística. Até logo!")
                break
            else:
                print("[AVISO] Opção inválida. Digite um número de 0 a 9.")

    def menu_dashboard(self) -> None:
        """Exibe o painel estatístico com indicadores gerais do depósito."""
        dados = self.gerenciador.obter_resumo_estatistico()
        print("\n" + "=" * 67)
        print("  TECLOGÍSTICA — DASHBOARD E INDICADORES GERAIS")
        print("=" * 67)
        print(f"  Total de Peças (SKUs Distintos): {dados['total_skus']}")
        print(f"  Total de Unidades Físicas:       {dados['total_unidades_fisicas']} unidades")
        print(f"  Unidades Reservadas em Pedidos: {dados['total_unidades_reservadas']} unidades")
        print(f"  Valor Patrimonial em Estoque:    {dados['valor_patrimonio_formatado']}")
        print(f"  Peças em Estoque Crítico:       {dados['qtd_abaixo_minimo']} item(ns)")
        print(f"  Setores Conectados no Depósito: {dados['setores_cadastrados']}")
        print("-" * 67)
        print(f"  Faturamento Total de Vendas:     {dados['faturamento_total_formatado']}")
        print(f"  Total de Vendas Realizadas:      {dados['qtd_vendas_realizadas']} venda(s)")
        print(f"  Pedidos Pendentes (Em Aberto):  {dados['qtd_pedidos_abertos']}")
        print(f"  Pedidos Separados (Reservados): {dados['qtd_pedidos_separados']}")
        print(f"  Pedidos Expedidos (Concluídos):  {dados['qtd_pedidos_expedidos']}")
        if dados["peca_mais_valiosa"]:
            pm = dados["peca_mais_valiosa"]
            print(f"  Peça de Maior Valor Unitário:   [{pm.sku}] {pm.nome} ({pm.preco_formatado})")
        print("=" * 67)
        input("\nPressione ENTER para voltar ao Menu Principal...")

    def _popular_dados_demonstrativos(self) -> None:
        """Inclui peças de demonstração apenas quando o usuário escolhe essa opção."""
        print("\n[+] Incluindo peças de demonstração no catálogo...")

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
                "[AVISO] Antes de carregar os exemplos, conecte estes setores ao mapa: "
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

        print(f"[OK] {adicionadas} nova(s) peça(s) adicionada(s) ao estoque com sucesso!")
        if existentes:
            print(f"[INFO] {existentes} peça(s) de demonstração já estavam cadastradas e não foram alteradas.")
        print(f"[INFO] Total atual no catálogo: {len(self.gerenciador.listar_pecas())} itens.")

    # --- MENUS SECUNDÁRIOS ---

    def menu_catalogo(self) -> None:
        while True:
            print("\n--- MENU DE CATÁLOGO DE PEÇAS ---")
            print("1. Cadastrar Nova Peça")
            print("2. Consultar Peça por SKU (Tabela Hash O(1))")
            print("3. Pesquisar por Nome/Categoria")
            print("4. Listar Todas as Peças")
            print("5. Atualizar Dados de uma Peça")
            print("6. Listar Peças em Ordem Alfabética (A-Z)")
            print("0. Voltar ao Menu Principal")

            op = input("Escolha uma opção (0-6): ").strip()
            if op == "1":
                sku = input("Digite o SKU único (ex: GPU-RTX-3060) [ou ENTER para cancelar]: ").strip()
                if not sku or sku.upper() in ("CANCELAR", "VOLTAR"):
                    print("[INFO] Cadastro cancelado.")
                    continue
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
                    print(f"\n[OK] Peça cadastrada com sucesso! {peca}")
                except ValueError as err:
                    print(f"[ERRO] Erro ao cadastrar peça: {err}")

            elif op == "2":
                sku = input("Digite o SKU para busca na Tabela Hash [ou '?' para buscar por nome]: ").strip()
                if not sku or sku.upper() in ("CANCELAR", "VOLTAR"):
                    continue
                if sku.upper() in ("?", "BUSCAR", "PESQUISAR", "LISTAR"):
                    termo = input("Pesquisar produto por Nome/Categoria (ENTER para ver todos): ").strip()
                    res = self.gerenciador.pesquisar_pecas(termo)
                    print(f"\n--- RESULTADO DA BUSCA ({len(res)} itens) ---")
                    for p in res:
                        print(f"  • SKU: {p.sku:<16} | {p.nome:<40} | Preço: {p.preco_formatado} | Estoque: {p.estoque_atual}")
                    sku = input("\nDigite o SKU desejado da lista acima: ").strip()
                    if not sku:
                        continue

                peca = self.gerenciador.buscar_peca_sku(sku)
                if peca:
                    print("\n[RESULTADO] Consulta na Tabela Hash O(1):")
                    print(f"  • SKU: {peca.sku}")
                    print(f"  • Nome: {peca.nome}")
                    print(f"  • Categoria: {peca.categoria} | Fabricante: {peca.fabricante}")
                    print(f"  • Preço: {peca.preco_formatado}")
                    print(f"  • Estoque Físico: {peca.estoque_atual} | Reservado: {peca.estoque_reservado} | Livre: {peca.estoque_disponivel}")
                    print(f"  • Localização no Depósito: {peca.localizacao}")
                else:
                    print(f"[AVISO] Nenhuma peça encontrada com o SKU '{sku}'.")

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
                    alert = " [ESTOQUE BAIXO]" if p.abaixo_do_minimo else ""
                    print(f"  - [{p.sku:<16}] {p.nome:<45} | {p.preco_formatado:<11} | Est: {p.estoque_atual:<3} (Livre: {p.estoque_disponivel:<3}) | Local: {p.localizacao}{alert}")

            elif op == "5":
                sku = input("SKU da peça que deseja atualizar [ou '?' para buscar]: ").strip()
                if not sku or sku.upper() in ("CANCELAR", "VOLTAR"):
                    continue
                if sku.upper() in ("?", "BUSCAR", "PESQUISAR", "LISTAR"):
                    termo = input("Pesquisar produto por Nome/Categoria (ENTER para ver todos): ").strip()
                    res = self.gerenciador.pesquisar_pecas(termo)
                    print(f"\n--- RESULTADO DA BUSCA ({len(res)} itens) ---")
                    for p in res:
                        print(f"  • SKU: {p.sku:<16} | {p.nome:<40} | Local: {p.localizacao}")
                    sku = input("\nSKU da peça que deseja atualizar: ").strip()
                    if not sku:
                        continue

                atual = self.gerenciador.buscar_peca_sku(sku)
                if atual is None:
                    print(f"[AVISO] Nenhuma peça encontrada com o SKU '{sku}'.")
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
                        print(f"[AVISO] {err}")
                        continue
                else:
                    preco_centavos = atual.preco_centavos
                localizacao = input(f"Setor [{atual.localizacao}]: ").strip() or atual.localizacao
                try:
                    atualizada = self.gerenciador.atualizar_peca(
                        sku, nome, categoria, fabricante, preco_centavos, localizacao
                    )
                    print(f"[OK] Dados atualizados: {atualizada}")
                except ValueError as err:
                    print(f"[ERRO] Erro ao atualizar peça: {err}")

            elif op == "6":
                print("\n--- PEÇAS EM ORDEM ALFABÉTICA (A-Z) ---")
                print("1. Ordenar por Nome do Produto")
                print("2. Ordenar por SKU")
                c_op = input("Escolha o campo de ordenação (1 ou 2): ").strip()
                campo = "sku" if c_op == "2" else "nome"
                pecas_ord = self.gerenciador.listar_pecas_ordem_alfabetica(por_campo=campo)
                print(f"\n--- {len(pecas_ord)} PEÇA(S) ORDENADA(S) POR {campo.upper()} (A-Z) ---")
                for p in pecas_ord:
                    alert = " [ESTOQUE BAIXO]" if p.abaixo_do_minimo else ""
                    print(f"  - [{p.sku:<16}] {p.nome:<45} | {p.preco_formatado:<11} | Est: {p.estoque_atual:<3} | Local: {p.localizacao}{alert}")

            elif op == "0":
                break
            else:
                print("[AVISO] Opção inválida. Escolha uma opção entre 0 e 6.")

    def menu_estoque(self) -> None:
        while True:
            print("\n--- MENU DE GESTÃO DE ESTOQUE E RASTREABILIDADE ---")
            print("1. Registrar Entrada de Mercadoria (Recebimento)")
            print("2. Registrar Ajuste Manual de Estoque (Ganho/Perda)")
            print("3. Ver Histórico de Movimentações (Trilha de Rastreabilidade)")
            print("4. Desfazer Última Operação (Pilha LIFO Encadeada)")
            print("0. Voltar ao Menu Principal")

            op = input("Escolha uma opção (0-4): ").strip()
            if op == "1":
                sku = input("SKU da peça recebida [? para buscar / ENTER para cancelar]: ").strip()
                if not sku or sku.upper() in ("CANCELAR", "VOLTAR"):
                    print("[INFO] Operação cancelada.")
                    continue
                if sku.upper() in ("?", "BUSCAR", "PESQUISAR", "LISTAR"):
                    termo = input("Pesquisar produto por Nome/Categoria (ENTER para ver todos): ").strip()
                    res = self.gerenciador.pesquisar_pecas(termo)
                    print(f"\n--- RESULTADO DA BUSCA ({len(res)} itens) ---")
                    for p in res:
                        print(f"  • SKU: {p.sku:<16} | {p.nome:<40} | Estoque Atual: {p.estoque_atual}")
                    sku = input("\nSKU da peça recebida [ENTER para cancelar]: ").strip()
                    if not sku or sku.upper() in ("CANCELAR", "VOLTAR"):
                        print("[INFO] Operação cancelada.")
                        continue

                qtd = ler_inteiro("Quantidade recebida: ", minimo=1)
                obs = input("Observação/Nota Fiscal (opcional): ").strip()
                try:
                    peca = self.gerenciador.registrar_entrada(sku, qtd, obs or "Recebimento")
                    print(f"[OK] Entrada registrada com sucesso! Novo estoque de '{peca.sku}': {peca.estoque_atual}")
                except ValueError as err:
                    print(f"[ERRO] Erro ao registrar entrada: {err}")

            elif op == "2":
                sku = input("SKU da peça para ajuste [? para buscar / ENTER para cancelar]: ").strip()
                if not sku or sku.upper() in ("CANCELAR", "VOLTAR"):
                    print("[INFO] Operação cancelada.")
                    continue
                if sku.upper() in ("?", "BUSCAR", "PESQUISAR", "LISTAR"):
                    termo = input("Pesquisar produto por Nome/Categoria (ENTER para ver todos): ").strip()
                    res = self.gerenciador.pesquisar_pecas(termo)
                    print(f"\n--- RESULTADO DA BUSCA ({len(res)} itens) ---")
                    for p in res:
                        print(f"  • SKU: {p.sku:<16} | {p.nome:<40} | Estoque Atual: {p.estoque_atual}")
                    sku = input("\nSKU da peça para ajuste [ENTER para cancelar]: ").strip()
                    if not sku or sku.upper() in ("CANCELAR", "VOLTAR"):
                        print("[INFO] Operação cancelada.")
                        continue

                print("Digite a variação (ex: 5 para adicionar 5 unidades, -2 para remover 2 por avaria):")
                qtd_delta = ler_inteiro("Variação do ajuste: ")
                obs = input("Motivo do ajuste: ").strip()
                try:
                    peca = self.gerenciador.registrar_ajuste(sku, qtd_delta, obs or "Ajuste manual")
                    print(f"[OK] Ajuste realizado! Novo estoque atual de '{peca.sku}': {peca.estoque_atual}")
                except ValueError as err:
                    print(f"[ERRO] Erro ao realizar ajuste: {err}")

            elif op == "3":
                sku_filtro = input("Filtrar por SKU (deixe em branco para ver todos): ").strip()
                movs = self.gerenciador.listar_movimentacoes(sku_filtro if sku_filtro else None)
                print(f"\n--- HISTÓRICO DE MOVIMENTAÇÕES ({len(movs)} registros) ---")
                for m in movs:
                    print(f"  [{m.timestamp}] {m.tipo:<9} | SKU: {m.sku:<16} | Qtd: {m.quantidade:<3} | Obs: {m.observacao}")

            elif op == "4":
                try:
                    msg = self.gerenciador.desfazer_ultima_operacao()
                    print(f"[OK] {msg}")
                except ValueError as err:
                    print(f"[AVISO] Não foi possível desfazer: {err}")

            elif op == "0":
                break
            else:
                print("[AVISO] Opção inválida. Escolha uma opção entre 0 e 4.")

    def menu_pedidos(self) -> None:
        while True:
            print("\n--- MENU DE GESTÃO DE PEDIDOS E EXPEDIÇÃO ---")
            print("1. Criar Novo Pedido de Clientes")
            print("2. Separar Pedido (Reservar Estoque e Gerar Rota BFS no Grafo)")
            print("3. Expedir Pedido (Baixar Estoque Físico e Finalizar)")
            print("4. Cancelar Pedido (Liberar Reserva)")
            print("5. Listar Todos os Pedidos")
            print("0. Voltar ao Menu Principal")

            op = input("Escolha uma opção (0-5): ").strip()
            if op == "1":
                pid = input("Código do Pedido (ex: PED-1001) [ou ENTER para cancelar]: ").strip()
                if not pid or pid.upper() in ("CANCELAR", "VOLTAR"):
                    print("[INFO] Operação de criação de pedido cancelada.")
                    continue

                cliente = input("Nome do Cliente [ou ENTER para cancelar]: ").strip()
                if not cliente or cliente.upper() in ("CANCELAR", "VOLTAR"):
                    print("[INFO] Operação de criação de pedido cancelada.")
                    continue

                print("Escolha a urgência do pedido:")
                print("  1 - Alta (Urgente / Prioridade Máxima no Heap)")
                print("  2 - Média (Normal)")
                print("  3 - Baixa")
                urg = ler_inteiro("Urgência (1-3): ", minimo=1, maximo=3)

                itens = []
                cancelou = False
                while True:
                    print("\n[Dica: Digite '?' para buscar o SKU, 'CANCELAR' para sair ou ENTER para concluir]")
                    sku_item = input("SKU do item a adicionar: ").strip()

                    if sku_item.upper() in ("?", "BUSCAR", "PESQUISAR", "LISTAR"):
                        termo = input("Pesquisar produto por Nome/Categoria (ENTER para ver todos): ").strip()
                        res = self.gerenciador.pesquisar_pecas(termo)
                        print(f"\n--- RESULTADO DA BUSCA ({len(res)} itens) ---")
                        for p in res:
                            print(f"  • SKU: {p.sku:<16} | {p.nome:<40} | Preço: {p.preco_formatado} | Estoque: {p.estoque_atual}")
                        continue

                    if sku_item.upper() in ("CANCELAR", "VOLTAR"):
                        print("[INFO] Operação de pedido cancelada.")
                        cancelou = True
                        break

                    if not sku_item:
                        if not itens:
                            confirma = input("Nenhum item adicionado. Deseja cancelar o pedido? [S/n]: ").strip().lower()
                            if confirma in ("", "s", "sim", "y"):
                                print("[INFO] Operação de pedido cancelada.")
                                cancelou = True
                                break
                            continue
                        break

                    peca = self.gerenciador.buscar_peca_sku(sku_item)
                    if not peca:
                        print(f"[AVISO] Peça '{sku_item}' não encontrada. Digite '?' para buscar o SKU correto.")
                        continue
                    qtd_item = ler_inteiro(f"Quantidade de '{peca.sku}' ({peca.nome}): ", minimo=1)
                    itens.append((peca.sku, qtd_item))

                if cancelou or not itens:
                    continue

                try:
                    pedido = self.gerenciador.criar_pedido(pid, cliente, itens, urgencia=urg)
                    print(f"[OK] Pedido #{pedido.id_pedido} criado com sucesso e adicionado ao MinHeap de prioridades!")
                except ValueError as err:
                    print(f"[ERRO] Erro ao criar pedido: {err}")

            elif op == "2":
                pid = input("ID do Pedido a separar: ").strip()
                try:
                    pedido, rotas = self.gerenciador.separar_pedido(pid)
                    print(f"\n[OK] Pedido #{pedido.id_pedido} SEPARADO e estoque RESERVADO!")
                    print("ROTAS DE COLETA CALCULADAS NO DEPÓSITO VIA BFS (Grafo):")
                    for sku, rota in rotas.items():
                        print(f"  • Item SKU [{sku}] -> Rota: {' -> '.join(rota)}")
                except ValueError as err:
                    print(f"[ERRO] Falha ao separar pedido: {err}")

            elif op == "3":
                pid = input("ID do Pedido a expedir: ").strip()
                try:
                    pedido = self.gerenciador.expedir_pedido(pid)
                    print(f"[OK] Pedido #{pedido.id_pedido} EXPEDIDO com sucesso! Estoque baixado.")
                except ValueError as err:
                    print(f"[ERRO] Erro ao expedir pedido: {err}")

            elif op == "4":
                pid = input("ID do Pedido a cancelar: ").strip()
                try:
                    pedido = self.gerenciador.cancelar_pedido(pid)
                    print(f"[OK] Pedido #{pedido.id_pedido} CANCELADO e reservas liberadas.")
                except ValueError as err:
                    print(f"[ERRO] Erro ao cancelar pedido: {err}")

            elif op == "5":
                pedidos = self.gerenciador.listar_pedidos()
                print(f"\n--- LISTA DE PEDIDOS ({len(pedidos)} cadastrados) ---")
                for p in pedidos:
                    itens_str = ", ".join([f"{it.quantidade}x {it.sku}" for it in p.itens])
                    print(f"  • Pedido #{p.id_pedido} | Cliente: {p.cliente} | Status: {p.status:<9} | Urgência: {p.urgencia} | Itens: [{itens_str}]")

            elif op == "0":
                break
            else:
                print("[AVISO] Opção inválida. Escolha uma opção entre 0 e 5.")

    def menu_vendas(self) -> None:
        while True:
            print("\n--- MENU DE GESTÃO DE VENDAS E FATURAMENTO ---")
            print("1. Registrar Venda Direta (Balcão / PDV)")
            print("2. Consultar Histórico de Vendas Faturadas")
            print("3. Relatório de Faturamento e Ranking de Peças Mais Vendidas")
            print("0. Voltar ao Menu Principal")

            op = input("Escolha uma opção (0-3): ").strip()
            if op == "1":
                vid = input("Código da Venda (ex: VND-5001) [ou ENTER para cancelar]: ").strip()
                if not vid or vid.upper() in ("CANCELAR", "VOLTAR"):
                    print("[INFO] Operação de venda cancelada.")
                    continue

                cliente = input("Nome do Cliente [ou ENTER para cancelar]: ").strip()
                if not cliente or cliente.upper() in ("CANCELAR", "VOLTAR"):
                    print("[INFO] Operação de venda cancelada.")
                    continue

                itens = []
                cancelou = False
                while True:
                    print("\n[Dica: Digite '?' para buscar o SKU, 'CANCELAR' para sair ou ENTER para concluir]")
                    sku_item = input("SKU do item a vender: ").strip()

                    if sku_item.upper() in ("?", "BUSCAR", "PESQUISAR", "LISTAR"):
                        termo = input("Pesquisar produto por Nome/Categoria (ENTER para ver todos): ").strip()
                        res = self.gerenciador.pesquisar_pecas(termo)
                        print(f"\n--- RESULTADO DA BUSCA ({len(res)} itens) ---")
                        for p in res:
                            print(f"  • SKU: {p.sku:<16} | {p.nome:<40} | R$: {p.preco_formatado} | Livre: {p.estoque_disponivel}")
                        continue

                    if sku_item.upper() in ("CANCELAR", "VOLTAR"):
                        print("[INFO] Operação de venda cancelada.")
                        cancelou = True
                        break

                    if not sku_item:
                        if not itens:
                            confirma = input("Nenhum item adicionado. Deseja cancelar a venda? [S/n]: ").strip().lower()
                            if confirma in ("", "s", "sim", "y"):
                                print("[INFO] Operação de venda cancelada.")
                                cancelou = True
                                break
                            continue
                        break

                    peca = self.gerenciador.buscar_peca_sku(sku_item)
                    if not peca:
                        print(f"[AVISO] Peça '{sku_item}' não encontrada. Digite '?' para buscar o SKU correto.")
                        continue
                    qtd_item = ler_inteiro(
                        f"Quantidade de '{peca.sku}' ({peca.nome}) [Disponível: {peca.estoque_disponivel}]: ",
                        minimo=1,
                    )
                    itens.append((peca.sku, qtd_item))

                if cancelou or not itens:
                    continue

                try:
                    venda = self.gerenciador.registrar_venda_direta(vid, cliente, itens)
                    print(f"[OK] Venda #{venda.id_venda} registrada com sucesso! Total: {venda.valor_total_formatado}")
                except ValueError as err:
                    print(f"[ERRO] Erro ao registrar venda: {err}")

            elif op == "2":
                vendas = self.gerenciador.listar_vendas()
                print(f"\n--- HISTÓRICO DE VENDAS FATURADAS ({len(vendas)} registradas) ---")
                for v in vendas:
                    origem = f" | Pedido Origem: #{v.id_pedido_origem}" if v.id_pedido_origem else " | Venda Direta"
                    itens_str = ", ".join([f"{it.quantidade}x {it.sku} ({it.subtotal_formatado})" for it in v.itens])
                    print(f"  • Venda #{v.id_venda} | Cliente: {v.cliente}{origem} | Total: {v.valor_total_formatado} | Data: {v.data_venda}")
                    print(f"    Itens: [{itens_str}]")

            elif op == "3":
                rel = self.gerenciador.obter_relatorio_vendas()
                print("\n" + "=" * 67)
                print("  RELATÓRIO DE FATURAMENTO E PERFORMANCE DE VENDAS")
                print("=" * 67)
                print(f"  Faturamento Total Acumulado: {rel['faturamento_total_formatado']}")
                print(f"  Total de Vendas Realizadas:  {rel['total_vendas']} vendas")
                print(f"  Ticket Médio por Venda:     {rel['ticket_medio_formatado']}")
                print("-" * 67)
                print("  RANKING DAS PEÇAS MAIS VENDIDAS:")
                if not rel["ranking_vendas_sku"]:
                    print("     (Nenhuma venda registrada até o momento)")
                else:
                    for pos, (sku, info) in enumerate(rel["ranking_vendas_sku"], 1):
                        peca = self.gerenciador.buscar_peca_sku(sku)
                        nome_peca = peca.nome if peca else sku
                        f_r, f_c = divmod(info['faturamento_centavos'], 100)
                        f_fmt = f"R$ {f_r:,},{f_c:02d}".replace(",", ".")
                        print(f"     {pos:2d}º [{sku:<16}] {nome_peca:<35} | Qtd Vendida: {info['quantidade']:<4} | Faturamento: {f_fmt}")
                print("=" * 67)
                input("\nPressione ENTER para voltar...")

            elif op == "0":
                break
            else:
                print("[AVISO] Opção inválida. Escolha uma opção entre 0 e 3.")

    def menu_deposito(self) -> None:
        while True:
            print("\n--- MENU DE LAYOUT DO DEPÓSITO E GRAFOS ---")
            print("1. Visualizar Corredores Conectados (Grafo)")
            print("2. Cadastrar Novo Corredor / Conexão no Depósito")
            print("3. Testar Rota BFS entre Dois Setores")
            print("0. Voltar ao Menu Principal")

            op = input("Escolha uma opção (0-3): ").strip()
            if op == "1":
                print("\nMAPA DE ADJACÊNCIA DO DEPÓSITO (GRAFO POR LISTA DE ADJACÊNCIA):")
                for setor, vizinhos in self.gerenciador.grafo_deposito.conexoes.items():
                    print(f"  • Setor [{setor}] <-> Vizinhos: {', '.join(vizinhos)}")

            elif op == "2":
                p_a = input("Setor Origem (ex: CORREDOR-A): ").strip()
                p_b = input("Setor Destino (ex: CORREDOR-D): ").strip()
                try:
                    self.gerenciador.banco.salvar_via_deposito(p_a, p_b)
                    self.gerenciador.grafo_deposito.adicionar_via(p_a, p_b)
                    print(f"[OK] Via cadastrada entre '{p_a.upper()}' e '{p_b.upper()}'.")
                except ValueError as err:
                    print(f"[ERRO] Erro: {err}")

            elif op == "3":
                origem = input("Setor de Origem (ex: EXPEDICAO): ").strip()
                destino = input("Setor de Destino (ex: SETOR-PLACAS): ").strip()
                rota = self.gerenciador.grafo_deposito.bfs(origem, destino)
                if rota:
                    print(f"\n[OK] Menor trajeto em conexões (BFS): {' -> '.join(rota)} ({len(rota)-1} passos)")
                else:
                    print(f"[AVISO] Não há rota acessível entre '{origem}' e '{destino}'.")

            elif op == "0":
                break
            else:
                print("[AVISO] Opção inválida. Escolha uma opção entre 0 e 3.")

    def menu_alertas(self) -> None:
        print("\n--- RELATÓRIO DE REPOSIÇÃO E ESTOQUE MÍNIMO ---")
        abaixo = self.gerenciador.listar_abaixo_minimo()
        if not abaixo:
            print("[OK] Todas as peças estão com níveis de estoque acima do limite mínimo.")
        else:
            print(f"[ATENÇÃO] {len(abaixo)} peça(s) necessitam de reposição imediata:")
            for p in abaixo:
                print(f"  - SKU: {p.sku:<16} | Nome: {p.nome:<45} | Atual: {p.estoque_atual:<3} | Mínimo: {p.estoque_minimo:<3} | Local: {p.localizacao}")

    def menu_tutorial(self) -> None:
        """Exibe o manual de instruções e fluxo operacional do sistema."""
        print("\n" + "=" * 73)
        print("  GUIA COMPLETO E PASSO A PASSO DE USO — TECLOGÍSTICA")
        print("=" * 73)
        print("\n  Este guia apresenta a estrutura funcional e as etapas operacionais do sistema.\n")

        print("+-----------------------------------------------------------------------+")
        print("| 1. CONCEITOS E ESTRUTURAS UTILIZADAS                                  |")
        print("+-----------------------------------------------------------------------+")
        print("  • SKU (Stock Keeping Unit): Código único de identificação da peça.")
        print("    Exemplo: RAM-DDR4-8GB ou GPU-RTX-4060.\n")
        print("  • Tabela Hash: Estrutura para busca rápida (O(1) médio) pelo SKU da peça.\n")
        print("  • MinHeap (Fila de Urgência): Fila de prioridades para ordenação de pedidos.\n")
        print("  • BFS (Busca em Largura): Algoritmo de rotas mais curtas entre setores no depósito.\n")
        print("  • Pilha LIFO: Histórico encadeado para desfazer a última movimentação de estoque.\n")
        print("  • FIFO (Ordem de Chegada): Critério de desempate para pedidos de mesma urgência.\n")

        print("+-----------------------------------------------------------------------+")
        print("| 2. FLUXO OPERACIONAL DO SISTEMA                                       |")
        print("+-----------------------------------------------------------------------+\n")

        print("  [Etapa 1] Gestão do Catálogo de Peças (Opção 3)")
        print("     1. Cadastre a peça informando SKU, Nome, Categoria, Preço e Localização.")
        print("     2. Para visualizar todas as peças em Ordem Alfabética (A-Z), use a opção 6.")
        print("     3. Para consultar uma peça pelo SKU, use a opção 2.\n")

        print("  [Etapa 2] Movimentação de Estoque e Auditoria (Opção 4)")
        print("     1. 'Entrada de Mercadoria': Registra recebimento de novas unidades.")
        print("     2. 'Ajuste Manual': Correção de saldo (perdas, avarias ou acréscimos).")
        print("     3. 'Desfazer Operação': Desfaz a última ação de entrada/ajuste de estoque.\n")

        print("  [Etapa 3] Processamento de Pedidos (Opção 5)")
        print("     1. Criar Pedido: Define cliente, urgência (1-Alta, 2-Média, 3-Baixa) e itens.")
        print("     2. Separar Pedido: Reserva estoque e gera rota de coleta via BFS.")
        print("     3. Expedir Pedido: Baixa definitiva do estoque e geração de venda faturada.\n")

        print("  [Etapa 4] Dashboard, Relatórios e Depósito (Opções 2, 6, 7 e 8)")
        print("     - Opção 2: Indicadores patrimoniais e contadores do sistema.")
        print("     - Opção 7: Visualização e cadastro de corredores e conexões do galpão.")
        print("     - Opção 8: Relatório de peças que estão abaixo do estoque mínimo.")

        print("\n" + "=" * 73)
        input("\nPressione ENTER para retornar ao Menu Principal...")
