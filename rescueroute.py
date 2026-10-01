"""
RescueRoute — Sistema Tático de Triagem e Despacho de Resgate
Disciplina: Estruturas de Dados e Algoritmos (PBL)
Aluno: Thiago da Silva Lopes
"""

import sys
from collections import deque


# 1. ENTIDADE DE DOMÍNIO
class ChamadoResgate:
    def __init__(self, codigo: str, local: str, gravidade: int, descricao: str, solicitante: str, ordem: int = 0):
        self.codigo = codigo
        self.local = local
        self.gravidade = gravidade  # 1 = Crítico, 2 = Grave, 3 = Estável
        self.descricao = descricao
        self.solicitante = solicitante
        self.ordem = ordem  # Preserva estabilidade FIFO entre prioridades iguais

    def __repr__(self):
        return f"<Chamado {self.codigo} | Gravidade {self.gravidade} | Local '{self.local}'>"


# 2. TABELA HASH COM ENCADEAMENTO (Chaining) - O(1)
class TabelaHash:
    def __init__(self, tamanho: int = 8):
        if not isinstance(tamanho, int) or isinstance(tamanho, bool) or tamanho < 1:
            raise ValueError("O tamanho da tabela deve ser um inteiro positivo.")
        self.tamanho = tamanho
        self.baldes = [[] for _ in range(tamanho)]
        self.quantidade = 0

    def _hash(self, chave: str) -> int:
        if not isinstance(chave, str):
            raise TypeError("A chave da tabela hash deve ser texto.")
        indice = 0
        for caractere in chave:
            indice = (indice * 31 + ord(caractere)) % self.tamanho
        return indice

    def _redimensionar(self) -> None:
        itens = [item for balde in self.baldes for item in balde]
        self.tamanho = self.tamanho * 2 + 1
        self.baldes = [[] for _ in range(self.tamanho)]
        for chave, valor in itens:
            self.baldes[self._hash(chave)].append((chave, valor))

    def inserir(self, chave: str, valor: ChamadoResgate) -> None:
        balde = self.baldes[self._hash(chave)]
        for indice, (chave_existente, _) in enumerate(balde):
            if chave_existente == chave:
                balde[indice] = (chave, valor)
                return
        balde.append((chave, valor))
        self.quantidade += 1
        if self.quantidade / self.tamanho > 0.75:
            self._redimensionar()

    def buscar(self, chave: str) -> ChamadoResgate | None:
        for item in self.baldes[self._hash(chave)]:
            if item[0] == chave:
                return item[1]
        return None

    def __len__(self) -> int:
        return self.quantidade


# 3. MIN-HEAP EM ARRAY (Fila de Prioridade) - O(log n)
class MinHeap:
    def __init__(self):
        self.dados = []

    def _sobe(self, i: int) -> None:
        while i > 0:
            pai = (i - 1) // 2
            if self.dados[i] < self.dados[pai]:
                self.dados[i], self.dados[pai] = self.dados[pai], self.dados[i]
                i = pai
            else:
                break

    def _desce(self, i: int) -> None:
        tamanho = len(self.dados)
        while True:
            menor = i
            esq, dir_ = 2 * i + 1, 2 * i + 2
            if esq < tamanho and self.dados[esq] < self.dados[menor]:
                menor = esq
            if dir_ < tamanho and self.dados[dir_] < self.dados[menor]:
                menor = dir_
            if menor == i:
                break
            self.dados[i], self.dados[menor] = self.dados[menor], self.dados[i]
            i = menor

    def inserir(self, item: tuple) -> None:
        self.dados.append(item)
        self._sobe(len(self.dados) - 1)

    def consultar_min(self) -> tuple | None:
        return self.dados[0] if self.dados else None

    def extrair_min(self) -> tuple | None:
        if not self.dados:
            return None
        if len(self.dados) == 1:
            return self.dados.pop()
        raiz = self.dados[0]
        self.dados[0] = self.dados.pop()
        self._desce(0)
        return raiz

    def __len__(self) -> int:
        return len(self.dados)


# 4. GRAFO POR LISTA DE ADJACÊNCIA E BFS - O(V + E)
class Grafo:
    def __init__(self):
        self.conexoes = {}

    def adicionar_via(self, a: str, b: str) -> None:
        if not isinstance(a, str) or not a.strip() or not isinstance(b, str) or not b.strip():
            raise ValueError("Os locais da via devem ser textos não vazios.")
        if a == b:
            raise ValueError("Uma via deve conectar dois locais diferentes.")
        vizinhos_a = self.conexoes.setdefault(a, [])
        vizinhos_b = self.conexoes.setdefault(b, [])
        if b not in vizinhos_a:
            vizinhos_a.append(b)
        if a not in vizinhos_b:
            vizinhos_b.append(a)

    def bfs(self, inicio: str, destino: str) -> list[str] | None:
        if inicio not in self.conexoes or destino not in self.conexoes:
            return None
        fila = deque([inicio])
        predecessor = {inicio: None}

        while fila:
            atual = fila.popleft()
            if atual == destino:
                break
            for vizinho in self.conexoes[atual]:
                if vizinho not in predecessor:
                    predecessor[vizinho] = atual
                    fila.append(vizinho)

        if destino not in predecessor:
            return None

        caminho, passo = [], destino
        while passo is not None:
            caminho.append(passo)
            passo = predecessor[passo]
        return caminho[::-1]


# 5. PILHA LIFO ENCADEADA (Histórico / Cancelamento Tático) - O(1)
class NoPilha:
    def __init__(self, dado):
        self.dado = dado
        self.proximo = None


class PilhaDespacho:
    def __init__(self):
        self.topo = None

    def empilhar(self, dado) -> None:
        novo = NoPilha(dado)
        novo.proximo = self.topo
        self.topo = novo

    def desempilhar(self):
        if not self.topo:
            return None
        removido = self.topo.dado
        self.topo = self.topo.proximo
        return removido


# 6. CENTRAL OPERACIONAL (Integração das 4 Estruturas)
class CentroOperacoesResgate:
    def __init__(self):
        self.grafo = Grafo()
        self.tabela_hash = TabelaHash()
        self.heap = MinHeap()
        self.pilha = PilhaDespacho()
        self.contador = 0

    def registrar_via(self, a: str, b: str) -> None:
        self.grafo.adicionar_via(a, b)

    def receber_chamado(self, codigo: str, local: str, gravidade: int, descricao: str, solicitante: str) -> None:
        if not isinstance(codigo, str) or not codigo.strip():
            raise ValueError("O código do chamado não pode ficar vazio.")
        if self.tabela_hash.buscar(codigo) is not None:
            raise ValueError(f"Já existe um chamado com o código {codigo}.")
        if not isinstance(gravidade, int) or isinstance(gravidade, bool) or gravidade not in (1, 2, 3):
            raise ValueError("A gravidade deve ser 1 (crítica), 2 (grave) ou 3 (estável).")
        if not isinstance(local, str) or not local.strip():
            raise ValueError("O local do chamado não pode ficar vazio.")
        self.contador += 1
        chamado = ChamadoResgate(codigo, local, gravidade, descricao, solicitante, self.contador)
        self.tabela_hash.inserir(codigo, chamado)
        self.heap.inserir((gravidade, chamado.ordem, codigo))

    def despachar_proximo(self, base: str = "Base-Central") -> ChamadoResgate | None:
        item = self.heap.consultar_min()
        if not item:
            print("⚠️ Nenhum chamado pendente.")
            return None

        gravidade, _, codigo = item
        chamado = self.tabela_hash.buscar(codigo)
        if chamado is None:
            raise RuntimeError(f"O chamado {codigo} não foi encontrado na tabela de consulta.")
        rota = self.grafo.bfs(base, chamado.local)
        if rota is None:
            print(f"⚠️ Sem rota entre {base} e {chamado.local}; o chamado {codigo} permanece na fila.")
            return None

        self.heap.extrair_min()
        self.pilha.empilhar(chamado)

        labels = {1: "🔴 CRÍTICO", 2: "🟡 GRAVE", 3: "🟢 ESTÁVEL"}
        str_rota = " ➔ ".join(rota)

        print(f"🚑 [DESPACHO] {chamado.codigo} | {labels.get(gravidade, 'NÍVEL ' + str(gravidade))} | Solicitante: {chamado.solicitante}")
        print(f"   Situação: {chamado.descricao} | Destino: {chamado.local}")
        print(f"   Rota Tática: {str_rota}\n" + "-" * 55)
        return chamado

    def abortar_ultimo_despacho(self) -> ChamadoResgate | None:
        chamado = self.pilha.desempilhar()
        if not chamado:
            print("❌ Nenhum despacho recente para abortar.")
            return None
        print(f"🚨 [CANCELAMENTO TÁTICO] Redirecionando equipe do chamado {chamado.codigo} ({chamado.solicitante})!")
        print(f"   Reintegrando ao MinHeap com Ordem Original #{chamado.ordem}\n" + "-" * 55)
        self.heap.inserir((chamado.gravidade, chamado.ordem, chamado.codigo))
        return chamado


# DEMONSTRAÇÃO DO SISTEMA
def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 60)
    print("   RESCUEROUTE — SISTEMA TÁTICO DE RESGATE (DEFESA CIVIL)")
    print("=" * 60 + "\n")

    central = CentroOperacoesResgate()

    # 1. Malha Viária (Grafo)
    vias = [
        ("Base-Central", "Hospital Regional"),
        ("Base-Central", "Setor Comercial"),
        ("Hospital Regional", "Ponte Norte"),
        ("Setor Comercial", "Morro Alto"),
        ("Ponte Norte", "Bairro Ribeirinho"),
        ("Morro Alto", "Bairro Ribeirinho")
    ]
    for orig, dest in vias:
        central.registrar_via(orig, dest)

    # 2. Entrada de Chamados (Triagem e Hash)
    print("📞 REGISTRANDO CHAMADOS DE EMERGÊNCIA...")
    central.receber_chamado("RESG-101", "Morro Alto", 3, "Queda de galho", "João Silva")
    central.receber_chamado("RESG-102", "Hospital Regional", 2, "Falta de O2", "Dra. Ana")
    central.receber_chamado("RESG-103", "Bairro Ribeirinho", 3, "Família ilhada", "Maria Souza")
    central.receber_chamado("RESG-999", "Bairro Ribeirinho", 1, "Criança soterrada", "Pedro Santos")  # INSERIDO POR ÚLTIMO
    print("✅ 4 Chamados registrados com sucesso na Tabela Hash e MinHeap.\n")

    # 3. Despacho Prioritário (MinHeap + BFS)
    print("🚨 --- INICIANDO DESPACHOS TÁTICOS ---")
    d1 = central.despachar_proximo()  # Despacha RESG-999 (Gravidade 1 - Crítico)
    d2 = central.despachar_proximo()  # Despacha RESG-102 (Gravidade 2 - Grave)

    # 4. Abortar Último Despacho (Pilha LIFO)
    central.abortar_ultimo_despacho()  # Aborta RESG-102

    print("🚨 --- DESPACHANDO RESTANTES APÓS CANCELAMENTO ---")
    central.despachar_proximo()  # Re-despacha RESG-102
    central.despachar_proximo()  # Despacha RESG-101
    central.despachar_proximo()  # Despacha RESG-103

    print("=" * 60)
    print("🏆 PROVA CONCLUÍDA: O chamado mais urgente (RESG-999) saiu primeiro,")
    print("   e a Pilha LIFO permitiu desfazer o último despacho com sucesso.")
    print("=" * 60)


if __name__ == "__main__":
    main()
