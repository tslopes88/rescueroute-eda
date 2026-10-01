"""
RescueRoute — Sistema Tático de Triagem e Despacho de Resgate
Disciplina: Estruturas de Dados e Algoritmos (PBL)
Aluno: Thiago da Silva Lopes
"""

import sys
from collections import deque

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


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
        self.tamanho = tamanho
        self.baldes = [[] for _ in range(tamanho)]

    def _hash(self, chave: str) -> int:
        return sum(ord(c) for c in str(chave)) % self.tamanho

    def inserir(self, chave: str, valor: ChamadoResgate) -> None:
        balde = self.baldes[self._hash(chave)]
        for item in balde:
            if item[0] == chave:
                item[1] = valor
                return
        balde.append([chave, valor])

    def buscar(self, chave: str):
        for item in self.baldes[self._hash(chave)]:
            if item[0] == chave:
                return item[1]
        return None


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

    def extrair_min(self):
        if not self.dados:
            return None
        if len(self.dados) == 1:
            return self.dados.pop()
        raiz = self.dados[0]
        self.dados[0] = self.dados.pop()
        self._desce(0)
        return raiz


# 4. GRAFO POR LISTA DE ADJACÊNCIA E BFS - O(V + E)
class Grafo:
    def __init__(self):
        self.conexoes = {}

    def adicionar_via(self, a: str, b: str) -> None:
        self.conexoes.setdefault(a, []).append(b)
        self.conexoes.setdefault(b, []).append(a)

    def bfs(self, inicio: str, destino: str):
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
        self.contador += 1
        chamado = ChamadoResgate(codigo, local, gravidade, descricao, solicitante, self.contador)
        self.tabela_hash.inserir(codigo, chamado)
        self.heap.inserir((gravidade, chamado.ordem, codigo))

    def despachar_proximo(self, base: str = "Base-Central"):
        item = self.heap.extrair_min()
        if not item:
            print("⚠️ Nenhum chamado pendente.")
            return None

        gravidade, ordem, codigo = item
        chamado = self.tabela_hash.buscar(codigo)
        rota = self.grafo.bfs(base, chamado.local)
        self.pilha.empilhar(chamado)

        labels = {1: "🔴 CRÍTICO", 2: "🟡 GRAVE", 3: "🟢 ESTÁVEL"}
        str_rota = " ➔ ".join(rota) if rota else "Sem rota"

        print(f"🚑 [DESPACHO] {chamado.codigo} | {labels.get(gravidade, 'NÍVEL ' + str(gravidade))} | Solicitante: {chamado.solicitante}")
        print(f"   Situação: {chamado.descricao} | Destino: {chamado.local}")
        print(f"   Rota Tática: {str_rota}\n" + "-" * 55)
        return chamado

    def abortar_ultimo_despacho(self):
        chamado = self.pilha.desempilhar()
        if not chamado:
            print("❌ Nenhum despacho recente para abortar.")
            return None
        print(f"🚨 [CANCELAMENTO TÁTICO] Redirecionando equipe do chamado {chamado.codigo} ({chamado.solicitante})!")
        print(f"   Reintegrando ao MinHeap com Ordem Original #{chamado.ordem}\n" + "-" * 55)
        self.heap.inserir((chamado.gravidade, chamado.ordem, chamado.codigo))
        return chamado


# DEMONSTRAÇÃO DO SISTEMA
if __name__ == "__main__":
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
