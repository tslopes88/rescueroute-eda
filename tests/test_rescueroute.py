import io
import unittest
from contextlib import redirect_stdout

from rescueroute import (
    CentroOperacoesResgate,
    ChamadoResgate,
    Grafo,
    MinHeap,
    PilhaDespacho,
    TabelaHash,
)
from simulador_logistica import MinHeap as MinHeapCompat


class CompatibilityTests(unittest.TestCase):
    def test_nome_antigo_reexporta_as_estruturas(self):
        self.assertIs(MinHeapCompat, MinHeap)


class TabelaHashTests(unittest.TestCase):
    def test_colisoes_e_atualizacao_de_chave(self):
        tabela = TabelaHash(tamanho=3)
        primeiro = ChamadoResgate("A", "Local A", 1, "Teste", "Pessoa A")
        segundo = ChamadoResgate("D", "Local D", 2, "Teste", "Pessoa D")
        atualizado = ChamadoResgate("A", "Local novo", 3, "Atualizado", "Pessoa A")

        tabela.inserir("A", primeiro)
        tabela.inserir("D", segundo)
        tabela.inserir("A", atualizado)

        self.assertIs(tabela.buscar("A"), atualizado)
        self.assertIs(tabela.buscar("D"), segundo)
        self.assertEqual(len(tabela), 2)

    def test_redimensiona_sem_perder_registros(self):
        tabela = TabelaHash(tamanho=2)
        chamados = {
            f"RESG-{numero}": ChamadoResgate(
                f"RESG-{numero}", "Local", 2, "Teste", "Pessoa"
            )
            for numero in range(12)
        }

        for codigo, chamado in chamados.items():
            tabela.inserir(codigo, chamado)

        self.assertGreater(tabela.tamanho, 2)
        self.assertEqual(len(tabela), len(chamados))
        for codigo, chamado in chamados.items():
            self.assertIs(tabela.buscar(codigo), chamado)

    def test_rejeita_tamanho_invalido(self):
        for tamanho in (0, -1, True):
            with self.subTest(tamanho=tamanho), self.assertRaises(ValueError):
                TabelaHash(tamanho=tamanho)


class MinHeapTests(unittest.TestCase):
    def test_prioriza_gravidade_e_preserva_ordem_de_chegada(self):
        heap = MinHeap()
        heap.inserir((3, 1, "RESG-1"))
        heap.inserir((1, 3, "RESG-3"))
        heap.inserir((1, 2, "RESG-2"))

        self.assertEqual(heap.consultar_min(), (1, 2, "RESG-2"))
        self.assertEqual(heap.extrair_min(), (1, 2, "RESG-2"))
        self.assertEqual(heap.extrair_min(), (1, 3, "RESG-3"))
        self.assertEqual(heap.extrair_min(), (3, 1, "RESG-1"))
        self.assertIsNone(heap.extrair_min())


class GrafoTests(unittest.TestCase):
    def test_bfs_retorna_caminho_com_menos_trechos(self):
        grafo = Grafo()
        for origem, destino in (
            ("Base", "A"),
            ("A", "Destino"),
            ("Base", "B"),
            ("B", "C"),
            ("C", "Destino"),
            ("Base", "A"),
        ):
            grafo.adicionar_via(origem, destino)

        self.assertEqual(grafo.bfs("Base", "Destino"), ["Base", "A", "Destino"])
        self.assertEqual(grafo.conexoes["Base"].count("A"), 1)

    def test_bfs_indica_locais_sem_rota(self):
        grafo = Grafo()
        grafo.adicionar_via("Base", "Local A")
        grafo.adicionar_via("Local B", "Local C")

        self.assertIsNone(grafo.bfs("Base", "Local C"))


class PilhaTests(unittest.TestCase):
    def test_lifo_e_pilha_vazia(self):
        pilha = PilhaDespacho()
        self.assertIsNone(pilha.desempilhar())

        pilha.empilhar("primeiro")
        pilha.empilhar("segundo")

        self.assertEqual(pilha.desempilhar(), "segundo")
        self.assertEqual(pilha.desempilhar(), "primeiro")
        self.assertIsNone(pilha.desempilhar())


class CentroOperacoesTests(unittest.TestCase):
    def setUp(self):
        self.central = CentroOperacoesResgate()
        self.central.registrar_via("Base-Central", "Local A")

    def test_rejeita_codigo_duplicado_e_gravidade_invalida(self):
        self.central.receber_chamado("RESG-1", "Local A", 1, "Teste", "Pessoa")

        with self.assertRaises(ValueError):
            self.central.receber_chamado("RESG-1", "Local A", 2, "Duplicado", "Pessoa")
        for gravidade in (0, 4, 1.0, True):
            with self.subTest(gravidade=gravidade), self.assertRaises(ValueError):
                self.central.receber_chamado(
                    f"RESG-{gravidade}", "Local A", gravidade, "Teste", "Pessoa"
                )

        self.assertEqual(len(self.central.heap), 1)

    def test_chamado_sem_rota_permanece_pendente(self):
        self.central.receber_chamado("RESG-1", "Local isolado", 1, "Teste", "Pessoa")
        saida = io.StringIO()

        with redirect_stdout(saida):
            resultado = self.central.despachar_proximo()

        self.assertIsNone(resultado)
        self.assertEqual(len(self.central.heap), 1)
        self.assertIn("permanece na fila", saida.getvalue())

        self.central.registrar_via("Base-Central", "Local isolado")
        with redirect_stdout(io.StringIO()):
            resultado = self.central.despachar_proximo()
        self.assertEqual(resultado.codigo, "RESG-1")

    def test_cancelamento_reinsere_chamado_com_ordem_original(self):
        self.central.receber_chamado("RESG-1", "Local A", 2, "Primeiro", "Pessoa")
        self.central.receber_chamado("RESG-2", "Local A", 2, "Segundo", "Pessoa")

        with redirect_stdout(io.StringIO()):
            despachado = self.central.despachar_proximo()
            cancelado = self.central.abortar_ultimo_despacho()
            reinserido = self.central.despachar_proximo()

        self.assertEqual(despachado.codigo, "RESG-1")
        self.assertIs(cancelado, despachado)
        self.assertEqual(reinserido.codigo, "RESG-1")


if __name__ == "__main__":
    unittest.main()
