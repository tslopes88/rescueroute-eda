"""
Testes de regressão e compatibilidade para o sistema RescueRoute / Controle de Estoque.
"""

import unittest
from rescueroute import (
    GerenciadorEstoque,
    Grafo,
    MinHeap,
    NoPilha,
    Peca,
    PilhaOperacoes,
    TabelaHash,
)
from simulador_logistica import MinHeap as MinHeapCompat


class CompatibilityTests(unittest.TestCase):
    def test_nome_antigo_reexporta_as_estruturas(self):
        self.assertIs(MinHeapCompat, MinHeap)

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
