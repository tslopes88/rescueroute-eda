"""
Testes de regressão e compatibilidade para o sistema TecLogística / Controle de Estoque.
"""

import unittest
from teclogistica import (
    GerenciadorEstoque,
    Grafo,
    MinHeap,
    NoPilha,
    Peca,
    PilhaOperacoes,
    TabelaHash,
)
from rescueroute import MinHeap as MinHeapRescueRoute
from simulador_logistica import MinHeap as MinHeapSimulador


class TestesCompatibilidade(unittest.TestCase):
    def test_reexportacao_modulos_compatibilidade(self):
        self.assertIs(MinHeapRescueRoute, MinHeap)
        self.assertIs(MinHeapSimulador, MinHeap)

    def test_instanciacao_estruturas_basicas(self):
        tabela = TabelaHash()
        heap = MinHeap()
        grafo = Grafo()
        pilha = PilhaOperacoes()

        self.assertEqual(len(tabela), 0)
        self.assertEqual(len(heap), 0)
        self.assertEqual(len(pilha), 0)


if __name__ == "__main__":
    unittest.main()
