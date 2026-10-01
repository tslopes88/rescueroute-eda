"""
Suíte de testes automatizados para o sistema de logística e controle de estoque de peças.
"""

import io
import os
import sqlite3
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from cli import InterfaceCLI, converter_reais_centavos, ler_inteiro
from estruturas import AcaoReversivel, Grafo, MinHeap, PilhaOperacoes, TabelaHash
from modelos import ItemPedido, Peca, Pedido
from servicos import GerenciadorEstoque


class TabelaHashEstoqueTests(unittest.TestCase):
    def test_insercao_busca_e_atualizacao(self):
        tabela = TabelaHash(tamanho=4)
        p1 = Peca("GPU-1060", "GTX 1060", "GPU", "Nvidia", 50000, 5, 0, 2, "SETOR-A")
        p1_up = Peca("GPU-1060", "GTX 1060 V2", "GPU", "Nvidia", 55000, 8, 0, 2, "SETOR-A")

        tabela.inserir("GPU-1060", p1)
        self.assertEqual(tabela.buscar("GPU-1060").nome, "GTX 1060")

        tabela.inserir("GPU-1060", p1_up)
        self.assertEqual(tabela.buscar("GPU-1060").nome, "GTX 1060 V2")
        self.assertEqual(len(tabela), 1)

    def test_colisao_e_redimensionamento_dinamico(self):
        tabela = TabelaHash(tamanho=2)
        skus = [f"SKU-{i}" for i in range(10)]
        for s in skus:
            tabela.inserir(s, Peca(s, f"Peça {s}", "Cat", "Fab", 1000, 10, 0, 2, "LOCAL"))

        self.assertGreater(tabela.tamanho, 2)
        self.assertEqual(len(tabela), 10)
        for s in skus:
            self.assertIsNotNone(tabela.buscar(s))


class MinHeapEstoqueTests(unittest.TestCase):
    def test_prioridade_e_desempate_fifo(self):
        heap = MinHeap()
        # (urgencia, ordem_chegada, id_pedido)
        heap.inserir((2, 1, "PED-1"))
        heap.inserir((1, 3, "PED-URGENTE-2"))
        heap.inserir((1, 2, "PED-URGENTE-1"))
        heap.inserir((3, 4, "PED-BAIXA"))

        self.assertEqual(heap.extrair_min(), (1, 2, "PED-URGENTE-1"))
        self.assertEqual(heap.extrair_min(), (1, 3, "PED-URGENTE-2"))
        self.assertEqual(heap.extrair_min(), (2, 1, "PED-1"))
        self.assertEqual(heap.extrair_min(), (3, 4, "PED-BAIXA"))
        self.assertIsNone(heap.extrair_min())


class GrafoDepositoBFSTests(unittest.TestCase):
    def setUp(self):
        self.grafo = Grafo()
        self.grafo.adicionar_via("EXPEDICAO", "CORREDOR-A")
        self.grafo.adicionar_via("CORREDOR-A", "CORREDOR-B")
        self.grafo.adicionar_via("CORREDOR-B", "SETOR-PLACAS")
        self.grafo.adicionar_via("ISOLADO-1", "ISOLADO-2")

    def test_bfs_caminho_existente(self):
        rota = self.grafo.bfs("EXPEDICAO", "SETOR-PLACAS")
        self.assertEqual(rota, ["EXPEDICAO", "CORREDOR-A", "CORREDOR-B", "SETOR-PLACAS"])

    def test_bfs_localizacao_desconectada(self):
        self.assertIsNone(self.grafo.bfs("EXPEDICAO", "ISOLADO-2"))

    def test_bfs_localizacao_inexistente(self):
        self.assertIsNone(self.grafo.bfs("EXPEDICAO", "CORREDOR-INEXISTENTE"))


class GerenciadorEstoqueIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db_path = os.path.join(self.temp_dir, "test_estoque.db")
        self.gerenciador = GerenciadorEstoque(db_path=self.temp_db_path)

        self.gerenciador.cadastrar_peca(
            sku="RAM-8GB",
            nome="Memória 8GB",
            categoria="RAM",
            fabricante="Kingston",
            preco_centavos=15000,
            estoque_atual=20,
            estoque_minimo=5,
            localizacao="CORREDOR-A",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ordenacao_alfabetica_por_nome_e_sku(self):
        self.gerenciador.cadastrar_peca(
            sku="SSD-256GB",
            nome="SSD SATA 256GB",
            categoria="SSD",
            fabricante="Crucial",
            preco_centavos=20000,
            estoque_atual=10,
            estoque_minimo=2,
            localizacao="CORREDOR-B",
        )
        self.gerenciador.cadastrar_peca(
            sku="CPU-I7",
            nome="Processador Intel Core i7",
            categoria="CPU",
            fabricante="Intel",
            preco_centavos=120000,
            estoque_atual=5,
            estoque_minimo=1,
            localizacao="CORREDOR-C",
        )

        # Ordenar por nome (A-Z)
        por_nome = self.gerenciador.listar_pecas_ordem_alfabetica(por_campo="nome")
        nomes = [p.nome for p in por_nome]
        self.assertEqual(nomes, ["Memória 8GB", "Processador Intel Core i7", "SSD SATA 256GB"])

        # Ordenar por SKU (A-Z)
        por_sku = self.gerenciador.listar_pecas_ordem_alfabetica(por_campo="sku")
        skus = [p.sku for p in por_sku]
        self.assertEqual(skus, ["CPU-I7", "RAM-8GB", "SSD-256GB"])

    def test_obter_resumo_estatistico_dashboard(self):
        resumo = self.gerenciador.obter_resumo_estatistico()
        self.assertEqual(resumo["total_skus"], 1)
        self.assertEqual(resumo["total_unidades_fisicas"], 20)
        self.assertIn("R$", resumo["valor_patrimonio_formatado"])

    def test_cadastro_sku_duplicado_rejeitado(self):
        with self.assertRaises(ValueError):
            self.gerenciador.cadastrar_peca("RAM-8GB", "Outra RAM", "RAM", "Fab", 1000)

    def test_atualizar_peca_preserva_saldos_e_persiste(self):
        atualizada = self.gerenciador.atualizar_peca(
            "RAM-8GB",
            "Memória nova 8GB",
            "Memória",
            "Corsair",
            17500,
            "CORREDOR-B",
        )

        self.assertEqual(atualizada.nome, "Memória nova 8GB")
        self.assertEqual(atualizada.estoque_atual, 20)
        reiniciado = GerenciadorEstoque(db_path=self.temp_db_path)
        carregada = reiniciado.buscar_peca_sku("RAM-8GB")
        self.assertEqual(carregada.nome, "Memória nova 8GB")
        self.assertEqual(carregada.localizacao, "CORREDOR-B")

    def test_localizacao_desconhecida_exige_cadastro_de_conexao(self):
        with self.assertRaisesRegex(ValueError, "não existe no mapa"):
            self.gerenciador.cadastrar_peca(
                "GPU-1", "Placa de vídeo", "GPU", "Marca", 1000, localizacao="SETOR-NOVO"
            )
        self.gerenciador.banco.salvar_via_deposito("CORREDOR-A", "SETOR-NOVO")
        self.gerenciador.grafo_deposito.adicionar_via("CORREDOR-A", "SETOR-NOVO")
        peca = self.gerenciador.cadastrar_peca(
            "GPU-1", "Placa de vídeo", "GPU", "Marca", 1000, localizacao="SETOR-NOVO"
        )
        self.assertEqual(peca.localizacao, "SETOR-NOVO")

    def test_entradas_saidas_e_alerta_minimo(self):
        peca = self.gerenciador.registrar_entrada("RAM-8GB", 10, "Entrada extra")
        self.assertEqual(peca.estoque_atual, 30)

        peca_ajuste = self.gerenciador.registrar_ajuste("RAM-8GB", -27, "Perda por avaria")
        self.assertEqual(peca_ajuste.estoque_atual, 3)

        abaixo = self.gerenciador.listar_abaixo_minimo()
        self.assertEqual(len(abaixo), 1)
        self.assertEqual(abaixo[0].sku, "RAM-8GB")

    def test_ciclo_de_vida_do_pedido_reserva_e_expedicao(self):
        pedido = self.gerenciador.criar_pedido("PED-1", "Cliente A", [("RAM-8GB", 5)], urgencia=1)
        self.assertEqual(pedido.status, "ABERTO")

        # Separar pedido -> Reserva estoque
        ped_sep, rotas = self.gerenciador.separar_pedido("PED-1")
        self.assertEqual(ped_sep.status, "SEPARADO")
        self.assertIn("RAM-8GB", rotas)

        peca = self.gerenciador.buscar_peca_sku("RAM-8GB")
        self.assertEqual(peca.estoque_atual, 20)
        self.assertEqual(peca.estoque_reservado, 5)
        self.assertEqual(peca.estoque_disponivel, 15)

        # Expedir pedido -> Baixa estoque e limpa reserva
        ped_exp = self.gerenciador.expedir_pedido("PED-1")
        self.assertEqual(ped_exp.status, "EXPEDIDO")

        peca_exp = self.gerenciador.buscar_peca_sku("RAM-8GB")
        self.assertEqual(peca_exp.estoque_atual, 15)
        self.assertEqual(peca_exp.estoque_reservado, 0)
        self.assertEqual(peca_exp.estoque_disponivel, 15)

    def test_cancelamento_de_pedido_libera_reserva(self):
        self.gerenciador.criar_pedido("PED-2", "Cliente B", [("RAM-8GB", 10)], urgencia=2)
        self.gerenciador.separar_pedido("PED-2")

        peca_res = self.gerenciador.buscar_peca_sku("RAM-8GB")
        self.assertEqual(peca_res.estoque_reservado, 10)

        self.gerenciador.cancelar_pedido("PED-2")

        peca_lib = self.gerenciador.buscar_peca_sku("RAM-8GB")
        self.assertEqual(peca_lib.estoque_reservado, 0)
        self.assertEqual(peca_lib.estoque_disponivel, 20)

    def test_estoque_insuficiente_impede_separacao(self):
        self.gerenciador.criar_pedido("PED-GRANDE", "Cliente C", [("RAM-8GB", 50)])
        with self.assertRaises(ValueError):
            self.gerenciador.separar_pedido("PED-GRANDE")

    def test_persistencia_apos_reiniciar_reconstruindo_hash_table(self):
        # Reinicia o Gerenciador usando o mesmo banco temporário
        novo_gerenciador = GerenciadorEstoque(db_path=self.temp_db_path)
        peca_carregada = novo_gerenciador.buscar_peca_sku("RAM-8GB")

        self.assertIsNotNone(peca_carregada)
        self.assertEqual(peca_carregada.nome, "Memória 8GB")
        self.assertEqual(len(novo_gerenciador.tabela_hash), 1)

    def test_desfazer_operacao_estoque(self):
        self.gerenciador.registrar_entrada("RAM-8GB", 15, "Lote 2")
        peca_antes = self.gerenciador.buscar_peca_sku("RAM-8GB")
        self.assertEqual(peca_antes.estoque_atual, 35)

        msg = self.gerenciador.desfazer_ultima_operacao()
        self.assertIn("Desfeita Entrada", msg)

        peca_depois = self.gerenciador.buscar_peca_sku("RAM-8GB")
        self.assertEqual(peca_depois.estoque_atual, 20)
        movimentacoes = self.gerenciador.listar_movimentacoes("RAM-8GB")
        self.assertEqual([mov.tipo for mov in movimentacoes], ["ENTRADA", "SAIDA"])

    def test_undo_falhado_nao_descarta_acao_da_pilha(self):
        self.gerenciador.registrar_entrada("RAM-8GB", 5)
        self.gerenciador.criar_pedido("PED-RESERVA", "Cliente", [("RAM-8GB", 22)])
        self.gerenciador.separar_pedido("PED-RESERVA")

        with self.assertRaisesRegex(ValueError, "(?i)não é possível desfazer"):
            self.gerenciador.desfazer_ultima_operacao()
        self.assertEqual(len(self.gerenciador.pilha_undo), 1)

        self.gerenciador.cancelar_pedido("PED-RESERVA")
        self.gerenciador.desfazer_ultima_operacao()
        self.assertEqual(self.gerenciador.buscar_peca_sku("RAM-8GB").estoque_atual, 20)

    def test_operacao_com_multiplas_movimentacoes_faz_rollback_integral(self):
        self.gerenciador.cadastrar_peca(
            "SSD-1", "SSD", "Armazenamento", "Marca", 5000, 5, 1, "CORREDOR-B"
        )
        self.gerenciador.criar_pedido(
            "PED-ATOMIC", "Cliente", [("RAM-8GB", 2), ("SSD-1", 1)]
        )
        with self.gerenciador.banco.get_conexao() as conn:
            conn.execute(
                """
                CREATE TRIGGER falha_movimentacao
                BEFORE INSERT ON movimentacoes
                WHEN NEW.sku = 'SSD-1'
                BEGIN
                    SELECT RAISE(ABORT, 'falha de teste');
                END;
                """
            )

        with self.assertRaises(sqlite3.IntegrityError):
            self.gerenciador.separar_pedido("PED-ATOMIC")

        self.assertEqual(self.gerenciador.consultar_pedido("PED-ATOMIC").status, "ABERTO")
        self.assertEqual(self.gerenciador.buscar_peca_sku("RAM-8GB").estoque_reservado, 0)
        self.assertEqual(self.gerenciador.buscar_peca_sku("SSD-1").estoque_reservado, 0)
        self.assertEqual(self.gerenciador.listar_movimentacoes(), [])

    def test_prioridade_da_heap_e_obrigatoria_na_separacao(self):
        self.gerenciador.criar_pedido("PED-NORMAL", "Cliente A", [("RAM-8GB", 1)], urgencia=2)
        self.gerenciador.criar_pedido("PED-URGENTE", "Cliente B", [("RAM-8GB", 1)], urgencia=1)

        with self.assertRaisesRegex(ValueError, "tem prioridade"):
            self.gerenciador.separar_pedido("PED-NORMAL")

        separado, _ = self.gerenciador.separar_pedido("PED-URGENTE")
        self.assertEqual(separado.id_pedido, "PED-URGENTE")

    def test_fila_de_prioridade_e_reconstruida_apos_reiniciar(self):
        self.gerenciador.criar_pedido("PED-NORMAL", "Cliente A", [("RAM-8GB", 1)], urgencia=2)
        self.gerenciador.criar_pedido("PED-URGENTE", "Cliente B", [("RAM-8GB", 1)], urgencia=1)
        reiniciado = GerenciadorEstoque(db_path=self.temp_db_path)

        self.assertEqual(
            reiniciado.heap_pedidos.consultar_min(),
            (1, 2, "PED-URGENTE"),
        )

    def test_itens_repetidos_sao_consolidados_antes_de_reservar(self):
        pedido = self.gerenciador.criar_pedido(
            "PED-DUP", "Cliente", [("RAM-8GB", 12), ("ram-8gb", 12)]
        )
        self.assertEqual(len(pedido.itens), 1)
        with self.assertRaisesRegex(ValueError, "Estoque insuficiente"):
            self.gerenciador.separar_pedido("PED-DUP")
        self.assertEqual(self.gerenciador.buscar_peca_sku("RAM-8GB").estoque_reservado, 0)


class EntradaCLItests(unittest.TestCase):
    def test_conversao_monetaria_brasileira_e_com_ponto(self):
        self.assertEqual(converter_reais_centavos("1.299,90"), 129990)
        self.assertEqual(converter_reais_centavos("1299.90"), 129990)
        self.assertEqual(converter_reais_centavos("R$ 49,9"), 4990)

    def test_conversao_monetaria_rejeita_precisao_excessiva(self):
        with self.assertRaisesRegex(ValueError, "duas casas"):
            converter_reais_centavos("1,999")

    def test_estoque_demonstrativo_nao_e_inserido_automaticamente(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        cli = InterfaceCLI(db_path=os.path.join(temp_dir, "vazio.db"))

        with patch("builtins.input", return_value="0"), redirect_stdout(io.StringIO()):
            cli.iniciar()

        self.assertEqual(cli.gerenciador.listar_pecas(), [])

    def test_leitura_de_inteiro_aplica_limites(self):
        with patch("builtins.input", side_effect=["4", "2"]):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(ler_inteiro("Urgência: ", minimo=1, maximo=3), 2)


if __name__ == "__main__":
    unittest.main()
