"""
Estruturas de Dados desenvolvidas do zero para a disciplina de EDA.

Implementações inclusas:
1. TabelaHash com Encadeamento e Redimensionamento Dinâmico (Chaining) - O(1) médio
2. MinHeap Binária em Array para Pedidos com Desempate FIFO - O(log n)
3. Grafo por Lista de Adjacência e Busca em Largura (BFS) - O(V + E)
4. Pilha LIFO Encadeada por Nós (Histórico de Desfazer Operações) - O(1)
"""

from collections import deque
from typing import Any, Tuple


class TabelaHash:
    """
    Tabela Hash personalizada com encadeamento separado (chaining) e redimensionamento dinâmico.
    Indexa objetos pela chave SKU para consulta em tempo médio constante O(1).
    """

    def __init__(self, tamanho: int = 8):
        if not isinstance(tamanho, int) or isinstance(tamanho, bool) or tamanho < 1:
            raise ValueError("O tamanho inicial da tabela hash deve ser um inteiro positivo.")

        self.tamanho = tamanho
        self.baldes: list[list[tuple[str, Any]]] = [[] for _ in range(tamanho)]
        self.quantidade = 0

    def _hash(self, chave: str) -> int:
        if not isinstance(chave, str):
            raise TypeError("A chave da tabela hash deve ser do tipo texto (str).")

        indice = 0
        for caractere in chave:
            indice = (indice * 31 + ord(caractere)) % self.tamanho
        return indice

    def _redimensionar(self) -> None:
        """Duplica a capacidade da tabela hash e re-indexa todos os itens para manter O(1)."""
        itens_antigos = [item for balde in self.baldes for item in balde]
        self.tamanho = self.tamanho * 2 + 1
        self.baldes = [[] for _ in range(self.tamanho)]

        for chave, valor in itens_antigos:
            self.baldes[self._hash(chave)].append((chave, valor))

    def inserir(self, chave: str, valor: Any) -> None:
        """Insere ou atualiza um par (chave, valor) na Tabela Hash."""
        chave_str = str(chave).strip().upper()
        indice = self._hash(chave_str)
        balde = self.baldes[indice]

        for i, (chave_existente, _) in enumerate(balde):
            if chave_existente == chave_str:
                balde[i] = (chave_str, valor)
                return

        balde.append((chave_str, valor))
        self.quantidade += 1

        # Redimensiona quando o fator de carga ultrapassa 0.75
        if self.quantidade / self.tamanho > 0.75:
            self._redimensionar()

    def buscar(self, chave: str) -> Any | None:
        """Busca um item na Tabela Hash pelo valor da chave em O(1) médio."""
        if not chave:
            return None
        chave_str = str(chave).strip().upper()
        balde = self.baldes[self._hash(chave_str)]

        for chave_existente, valor in balde:
            if chave_existente == chave_str:
                return valor
        return None

    def remover(self, chave: str) -> bool:
        """Remove uma chave da Tabela Hash se existir."""
        if not chave:
            return False
        chave_str = str(chave).strip().upper()
        balde = self.baldes[self._hash(chave_str)]

        for i, (chave_existente, _) in enumerate(balde):
            if chave_existente == chave_str:
                balde.pop(i)
                self.quantidade -= 1
                return True
        return False

    def limpar(self) -> None:
        """Reseta a Tabela Hash mantendo sua capacidade original."""
        self.baldes = [[] for _ in range(self.tamanho)]
        self.quantidade = 0

    def __len__(self) -> int:
        return self.quantidade


class MinHeap:
    """
    Min-Heap binária em array que organiza a fila de separação de pedidos.

    Formato dos elementos: (prioridade, ordem_chegada, payload)
      - O menor valor de prioridade possui maior urgência (ex: 1 = Urgência Alta).
      - O atributo ordem_chegada serve como desempate FIFO (estabilidade).
    """

    def __init__(self):
        self.dados: list[Tuple[int, int, Any]] = []

    def _pai(self, i: int) -> int:
        return (i - 1) // 2

    def _filho_esquerdo(self, i: int) -> int:
        return 2 * i + 1

    def _filho_direito(self, i: int) -> int:
        return 2 * i + 2

    def _sobe(self, i: int) -> None:
        while i > 0:
            pai_idx = self._pai(i)
            if self.dados[i] < self.dados[pai_idx]:
                self.dados[i], self.dados[pai_idx] = self.dados[pai_idx], self.dados[i]
                i = pai_idx
            else:
                break

    def _desce(self, i: int) -> None:
        tamanho = len(self.dados)

        while True:
            menor = i
            esq = self._filho_esquerdo(i)
            dir_ = self._filho_direito(i)

            if esq < tamanho and self.dados[esq] < self.dados[menor]:
                menor = esq
            if dir_ < tamanho and self.dados[dir_] < self.dados[menor]:
                menor = dir_

            if menor == i:
                break

            self.dados[i], self.dados[menor] = self.dados[menor], self.dados[i]
            i = menor

    def inserir(self, item: Tuple[int, int, Any]) -> None:
        """Insere uma tupla no Min-Heap e ajusta a posição via _sobe em O(log n)."""
        self.dados.append(item)
        self._sobe(len(self.dados) - 1)

    def consultar_min(self) -> Tuple[int, int, Any] | None:
        """Consulta o elemento raiz de maior prioridade sem removê-lo."""
        return self.dados[0] if self.dados else None

    def extrair_min(self) -> Tuple[int, int, Any] | None:
        """Extrai o elemento de menor valor (maior prioridade) em O(log n)."""
        if not self.dados:
            return None
        if len(self.dados) == 1:
            return self.dados.pop()

        raiz = self.dados[0]
        self.dados[0] = self.dados.pop()
        self._desce(0)
        return raiz

    def esta_vazia(self) -> bool:
        return len(self.dados) == 0

    def __len__(self) -> int:
        return len(self.dados)


class Grafo:
    """
    Grafo não direcionado representado por Lista de Adjacência para o layout de setores/corredores do depósito.
    Utiliza Busca em Largura (BFS) para calcular o menor caminho em número de conexões entre setores.
    """

    def __init__(self):
        self.conexoes: dict[str, list[str]] = {}

    def adicionar_via(self, a: str, b: str) -> None:
        """Cadastra um corredor ou conexão bidirecional entre dois setores do depósito."""
        if not isinstance(a, str) or not a.strip() or not isinstance(b, str) or not b.strip():
            raise ValueError("Os locais da via devem ser textos não vazios.")

        setor_a = a.strip().upper()
        setor_b = b.strip().upper()

        if setor_a == setor_b:
            raise ValueError("Uma via deve conectar dois setores distintos do depósito.")

        vizinhos_a = self.conexoes.setdefault(setor_a, [])
        vizinhos_b = self.conexoes.setdefault(setor_b, [])

        if setor_b not in vizinhos_a:
            vizinhos_a.append(setor_b)
        if setor_a not in vizinhos_b:
            vizinhos_b.append(setor_a)

    def bfs(self, inicio: str, destino: str) -> list[str] | None:
        """
        Calcula o percurso com menor número de passos (nós) do inicio até o destino.
        Retorna a lista de setores no trajeto ou None se o destino for inalcançável/inexistente.
        """
        if not inicio or not destino:
            return None

        origem = inicio.strip().upper()
        alvo = destino.strip().upper()

        if origem not in self.conexoes or alvo not in self.conexoes:
            return None

        if origem == alvo:
            return [origem]

        fila = deque([origem])
        predecessor: dict[str, str | None] = {origem: None}

        encontrado = False
        while fila:
            atual = fila.popleft()

            if atual == alvo:
                encontrado = True
                break

            for vizinho in self.conexoes[atual]:
                if vizinho not in predecessor:
                    predecessor[vizinho] = atual
                    fila.append(vizinho)

        if not encontrado or alvo not in predecessor:
            return None

        caminho = []
        passo: str | None = alvo
        while passo is not None:
            caminho.append(passo)
            passo = predecessor.get(passo)

        caminho.reverse()
        return caminho


class AcaoReversivel:
    """
    Encapsula dados de uma ação de estoque reversível para desfazer com segurança.
    """

    def __init__(self, tipo_acao: str, sku: str, quantidade: int, observacao: str = ""):
        self.tipo_acao = tipo_acao
        self.sku = sku
        self.quantidade = quantidade
        self.observacao = observacao


class NoPilha:
    """
    Nó Encadeado para a Pilha de Operações Reversíveis.
    """

    def __init__(self, dado: AcaoReversivel):
        self.dado = dado
        self.proximo: NoPilha | None = None


class PilhaOperacoes:
    """
    Pilha LIFO Encadeada por Nós para gerenciamento de histórico e desfazer de operações de estoque.
    """

    def __init__(self):
        self.topo: NoPilha | None = None
        self.quantidade = 0

    def empilhar(self, acao: AcaoReversivel) -> None:
        novo_no = NoPilha(acao)
        novo_no.proximo = self.topo
        self.topo = novo_no
        self.quantidade += 1

    def desempilhar(self) -> AcaoReversivel | None:
        if self.topo is None:
            return None
        no_removido = self.topo
        self.topo = self.topo.proximo
        self.quantidade -= 1
        return no_removido.dado

    def espiar(self) -> AcaoReversivel | None:
        return self.topo.dado if self.topo else None

    def esta_vazia(self) -> bool:
        return self.topo is None

    def __len__(self) -> int:
        return self.quantidade
