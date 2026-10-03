"""
TecLogística — Sistema de Logística e Estoque de Peças de Computador
Disciplina: Estruturas de Dados e Algoritmos (EDA)
Autor: Thiago da Silva Lopes
"""

import sys
from cli import InterfaceCLI
from estruturas import Grafo, MinHeap, NoPilha, PilhaOperacoes, TabelaHash
from modelos import ItemPedido, Movimentacao, Peca, Pedido
from servicos import GerenciadorEstoque


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    cli = InterfaceCLI(db_path="estoque.db")
    cli.iniciar()


if __name__ == "__main__":
    main()
