"""
Testes do módulo principal do sistema TecLogística.
"""

import unittest
from teclogistica import (
    GerenciadorEstoque,
    Grafo,
    ItemPedido,
    MinHeap,
    Movimentacao,
    NoPilha,
    Peca,
    Pedido,
    PilhaOperacoes,
    TabelaHash,
)


class TestesTecLogistica(unittest.TestCase):
    def test_exportacoes_principais_teclogistica(self):
        self.assertIsNotNone(GerenciadorEstoque)
        self.assertIsNotNone(Grafo)
        self.assertIsNotNone(MinHeap)
        self.assertIsNotNone(TabelaHash)
        self.assertIsNotNone(PilhaOperacoes)


if __name__ == "__main__":
    unittest.main()
