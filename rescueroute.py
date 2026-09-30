"""
===============================================================================
RESCUEROUTE — SISTEMA DE TRIAGEM E DESPACHO TÁTICO DE RESGATE (DEFESA CIVIL / SAMU)
===============================================================================
Disciplina: Estruturas de Dados e Algoritmos (EDA)
Autor: Thiago da Silva Lopes
Ambiente: Python 3.10+ (Executado sem bibliotecas de terceiros)

Estruturas de Dados Implementadas 100% do Zero:
1. TabelaHash (Tabela Hash com Encadeamento Separado / Chaining - O(1) médio)
2. MinHeap (Fila de Prioridade Binária Mapeada em Vetor - O(log n))
3. Grafo (Lista de Adjacência e Busca em Largura / BFS - O(V + E))
4. PilhaDespacho (Pilha Encadeada LIFO baseada em Nós - O(1))
===============================================================================
"""

import sys
from collections import deque
from typing import Dict, List, Optional, Tuple, Any

# Garantir compatibilidade de codificação UTF-8 em consoles Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class ChamadoResgate:
    """
    Entidade de Domínio representando um Chamado Médico de Emergência.

    Atributos:
        codigo_triagem (str): Identificador único da ocorrência (ex: 'RESG-999').
        localizacao (str): Ponto ou bairro onde a vítima se encontra.
        gravidade (int): Nível de urgência médica (1=Crítico/Vermelho, 2=Grave/Amarelo, 3=Estável/Verde).
        descricao_paciente (str): Síntese do quadro clínico e estado da vítima.
        solicitante (str): Nome do responsável pelo acionamento do resgate.
        ordem_chegada (int): Registro cronológico global para garantia de FIFO entre prioridades iguais.
    """

    def __init__(
        self,
        codigo_triagem: str,
        localizacao: str,
        gravidade: int,
        descricao_paciente: str,
        solicitante: str,
        ordem_chegada: int = 0
    ):
        self.codigo_triagem: str = codigo_triagem
        self.localizacao: str = localizacao
        self.gravidade: int = gravidade
        self.descricao_paciente: str = descricao_paciente
        self.solicitante: str = solicitante
        self.ordem_chegada: int = ordem_chegada

    def __repr__(self) -> str:
        return (
            f"<Chamado [{self.codigo_triagem}] Gravidade={self.gravidade} "
            f"Ordem={self.ordem_chegada} Local='{self.localizacao}'>"
        )


class TabelaHash:
    """
    Tabela Hash com Encadeamento Separado (Chaining) para armazenamento dos prontuários.

    Mecanismo Interno:
        - Array fixo de baldes (buckets): [ [ [chave, objeto_chamado], ... ], ... ].
        - Módulo da soma ASCII: _hash(chave) = sum(ord(c)) % tamanho.
        - Trata colisões anexando pares [chave, valor] na sublista correspondente.

    Complexidade:
        - Tempo (Busca e Inserção): O(1) Médio / O(n) Pior Caso (se houver colisões universais).
        - Espaço: O(n) proporcional ao número de ocorrências cadastradas.
    """

    def __init__(self, tamanho: int = 8):
        self.tamanho: int = tamanho
        self.baldes: List[List[List[Any]]] = [[] for _ in range(self.tamanho)]
        self._total_elementos: int = 0

    def _hash(self, chave: str) -> int:
        """
        Calcula o índice do balde via soma dos códigos ASCII dos caracteres módulo tamanho.
        Complexidade: O(k), onde k é o comprimento da string da chave.
        """
        return sum(ord(c) for c in str(chave)) % self.tamanho

    def inserir(self, codigo: str, ficha: ChamadoResgate) -> None:
        """
        Insere ou atualiza o chamado na Tabela Hash.
        Complexidade: O(1) Médio.
        """
        indice = self._hash(codigo)
        balde = self.baldes[indice]

        for item in balde:
            if item[0] == codigo:
                item[1] = ficha  # Atualização de prontuário existente
                return

        balde.append([codigo, ficha])
        self._total_elementos += 1

    def buscar(self, codigo: str) -> Optional[ChamadoResgate]:
        """
        Recupera a ficha médica do chamado pelo código de triagem.
        Complexidade: O(1) Médio.
        """
        indice = self._hash(codigo)
        balde = self.baldes[indice]

        for item in balde:
            if item[0] == codigo:
                return item[1]

        return None

    def remover(self, codigo: str) -> bool:
        """
        Remove um prontuário da Tabela Hash.
        Complexidade: O(1) Médio.
        """
        indice = self._hash(codigo)
        balde = self.baldes[indice]

        for i, item in enumerate(balde):
            if item[0] == codigo:
                balde.pop(i)
                self._total_elementos -= 1
                return True
        return False

    def __len__(self) -> int:
        return self._total_elementos


class MinHeap:
    """
    Min-Heap Binária mapeada em Vetor (Array) representando a Fila de Prioridade Médica.

    Indexação Matemática em Array (sem ponteiros explícitos):
        - Pai de i: (i - 1) // 2
        - Filho Esquerdo de i: 2 * i + 1
        - Filho Direito de i: 2 * i + 2

    Estrutura dos Elementos:
        - Tupla: (gravidade, ordem_chegada, codigo_triagem)
        - O menor número numérico indica a maior urgência médica (1 = Risco Iminente de Óbito).
        - O atributo ordem_chegada atua como critério de desempate estável (FIFO entre iguais).

    Complexidade:
        - Inserção (inserir): O(log n) via subida de nó (_sobe).
        - Extração do Mínimo (extrair_min): O(log n) via descida de nó (_desce).
        - Espaço: O(n).
    """

    def __init__(self):
        self.dados: List[Tuple[int, int, str]] = []

    def _pai(self, i: int) -> int:
        return (i - 1) // 2

    def _filho_esquerdo(self, i: int) -> int:
        return 2 * i + 1

    def _filho_direito(self, i: int) -> int:
        return 2 * i + 2

    def _sobe(self, i: int) -> None:
        """
        Move o elemento no índice i para cima (bubble-up) até restaurar a propriedade de Min-Heap.
        Complexidade: O(log n).
        """
        while i > 0 and self.dados[i] < self.dados[self._pai(i)]:
            pai_idx = self._pai(i)
            self.dados[i], self.dados[pai_idx] = self.dados[pai_idx], self.dados[i]
            i = pai_idx

    def _desce(self, i: int) -> None:
        """
        Move o elemento no índice i para baixo (bubble-down): compara o pai com seus
        filhos esquerdo e direito e troca estritamente com o filho de menor valor.
        Complexidade: O(log n).
        """
        tamanho = len(self.dados)

        while True:
            menor = i
            esq = self._filho_esquerdo(i)
            dir_ = self._filho_direito(i)

            # Valida e compara com o filho esquerdo
            if esq < tamanho and self.dados[esq] < self.dados[menor]:
                menor = esq

            # Valida e compara estritamente com o menor atual (entre pai e filho esquerdo)
            if dir_ < tamanho and self.dados[dir_] < self.dados[menor]:
                menor = dir_

            # Se a menor chave continua sendo o próprio elemento, o Heap está válido
            if menor == i:
                break

            # Promove o menor filho e continua rebaixando o elemento
            self.dados[i], self.dados[menor] = self.dados[menor], self.dados[i]
            i = menor

    def inserir(self, item: Tuple[int, int, str]) -> None:
        """
        Insere uma nova ocorrência (gravidade, ordem_chegada, codigo) na fila.
        Complexidade: O(log n).
        """
        self.dados.append(item)
        self._sobe(len(self.dados) - 1)

    def extrair_min(self) -> Optional[Tuple[int, int, str]]:
        """
        Extrai o chamado de maior urgência (raiz do Heap em dados[0]).
        Substitui a raiz pelo último elemento do array e executa _desce(0).
        Complexidade: O(log n).
        """
        if not self.dados:
            return None

        if len(self.dados) == 1:
            return self.dados.pop()

        raiz = self.dados[0]
        self.dados[0] = self.dados.pop()  # Substituição da raiz
        self._desce(0)  # Reajuste estrutural da árvore binária
        return raiz

    def esta_vazio(self) -> bool:
        return len(self.dados) == 0

    def __len__(self) -> int:
        return len(self.dados)


class Grafo:
    """
    Grafo não direcionado representado por Lista de Adjacência para a Malha Viária Urbana.

    Modelagem de Trajeto (BFS):
        - A Busca em Largura (BFS) explora as conexões em camadas concêntricas.
        - Utiliza fila (collections.deque) com popleft() em O(1).
        - Mantém o dicionário predecessor = {no: pai} para reconstrução do trajeto mínimo em arestas.

    Complexidade:
        - Tempo da BFS: O(V + E), onde V é o número de locais e E o número de vias.
        - Espaço: O(V + E) para armazenamento do grafo e O(V) para controle de predecessores.
    """

    def __init__(self):
        self.conexoes: Dict[str, List[str]] = {}

    def adicionar_vertice(self, vertice: str) -> None:
        if vertice not in self.conexoes:
            self.conexoes[vertice] = []

    def adicionar_via(self, ponto_a: str, ponto_b: str) -> None:
        """
        Cadastra uma via de trânsito livre bidirecional entre dois pontos.
        """
        self.adicionar_vertice(ponto_a)
        self.adicionar_vertice(ponto_b)

        if ponto_b not in self.conexoes[ponto_a]:
            self.conexoes[ponto_a].append(ponto_b)
        if ponto_a not in self.conexoes[ponto_b]:
            self.conexoes[ponto_b].append(ponto_a)

    def calcular_rota_bfs(self, base: str, destino: str) -> Optional[List[str]]:
        """
        Calcula a rota com o menor número de vias entre a Base e o Destino.
        Contém guarda estrita contra locais não cadastrados ou componentes desconexos.
        Complexidade: O(V + E).
        """
        if base not in self.conexoes or destino not in self.conexoes:
            return None

        if base == destino:
            return [base]

        fila = deque([base])
        predecessor: Dict[str, Optional[str]] = {base: None}

        encontrado = False
        while fila:
            atual = fila.popleft()

            if atual == destino:
                encontrado = True
                break

            for vizinho in self.conexoes[atual]:
                if vizinho not in predecessor:
                    predecessor[vizinho] = atual
                    fila.append(vizinho)

        # Guarda contra destinos inalcançáveis (evita KeyError na reconstrução)
        if not encontrado or destino not in predecessor:
            return None

        # Reconstrução linear do caminho do destino até a base
        caminho = []
        passo: Optional[str] = destino
        while passo is not None:
            caminho.append(passo)
            passo = predecessor.get(passo)

        caminho.reverse()
        return caminho


class NoPilha:
    """
    Nó Encadeado para a Pilha de Histórico de Despachos.
    """

    def __init__(self, dado: ChamadoResgate):
        self.dado: ChamadoResgate = dado
        self.proximo: Optional['NoPilha'] = None


class PilhaDespacho:
    """
    Pilha LIFO (Last-In, First-Out) encadeada por Nós para Histórico e Cancelamento Tático.

    Operação:
        - Empilha o chamado no topo quando um despacho é efetuado.
        - Desempilha o topo em O(1) na ação de "Abortar Último Despacho".

    Complexidade:
        - Tempo (empilhar / desempilhar): O(1) constante.
        - Espaço: O(k), onde k é o número de despachos ativos no histórico.
    """

    def __init__(self):
        self.topo: Optional[NoPilha] = None
        self._tamanho: int = 0

    def empilhar(self, chamado: ChamadoResgate) -> None:
        """
        Empilha um chamado despachado no topo da pilha.
        Complexidade: O(1).
        """
        novo_no = NoPilha(chamado)
        novo_no.proximo = self.topo
        self.topo = novo_no
        self._tamanho += 1

    def desempilhar(self) -> Optional[ChamadoResgate]:
        """
        Remove e retorna o último chamado despachado (topo da pilha).
        Complexidade: O(1).
        """
        if self.topo is None:
            return None

        no_removido = self.topo
        self.topo = self.topo.proximo
        self._tamanho -= 1
        return no_removido.dado

    def espiar(self) -> Optional[ChamadoResgate]:
        return self.topo.dado if self.topo else None

    def esta_vazia(self) -> bool:
        return self.topo is None

    def __len__(self) -> int:
        return self._tamanho


class CentroOperacoesResgate:
    """
    Classe Integradora do Sistema RescueRoute.
    Orquestra a TabelaHash, MinHeap, Grafo e PilhaDespacho para a triagem tática.
    """

    def __init__(self, capacidade_hash: int = 8):
        self.grafo = Grafo()
        self.tabela_hash = TabelaHash(tamanho=capacidade_hash)
        self.heap_prioridade = MinHeap()
        self.pilha_despachos = PilhaDespacho()
        self.contador_ordem: int = 0

    def registrar_via(self, origem: str, destino: str) -> None:
        """
        Cadastra uma via urbana livre para trânsito no Grafo.
        """
        self.grafo.adicionar_via(origem, destino)

    def receber_chamado(self, codigo: str, local: str, gravidade: int, descricao: str, solicitante: str) -> None:
        """
        Recebe e realiza a triagem inicial da ocorrência médica:
        1. Incrementa o contador de ordem de chegada global.
        2. Instancia ChamadoResgate mantendo a ordem_chegada original.
        3. Armazena os metadados na TabelaHash em O(1).
        4. Insere a chave de prioridade na MinHeap em O(log n).
        """
        self.contador_ordem += 1

        chamado = ChamadoResgate(
            codigo_triagem=codigo,
            localizacao=local,
            gravidade=gravidade,
            descricao_paciente=descricao,
            solicitante=solicitante,
            ordem_chegada=self.contador_ordem
        )

        # Guarda prontuário na Tabela Hash
        self.tabela_hash.inserir(codigo, chamado)

        # Enfileira prioridade no MinHeap
        self.heap_prioridade.inserir((gravidade, chamado.ordem_chegada, codigo))

    def despachar_proximo_resgate(self, base: str = "Base-Central") -> Optional[Dict[str, Any]]:
        """
        Processa e despacha a equipe para o chamado de maior prioridade médica:
        1. Extrai a menor chave da MinHeap em O(log n).
        2. Recupera o prontuário na TabelaHash em O(1).
        3. Calcula a menor rota em vias via BFS no Grafo em O(V + E).
        4. Empilha o atendimento na PilhaDespacho em O(1).
        """
        if self.heap_prioridade.esta_vazio():
            print("⚠️ Nenhum chamado pendente na fila de resgate.")
            return None

        item_heap = self.heap_prioridade.extrair_min()
        if not item_heap:
            return None

        gravidade, ordem_chegada, codigo = item_heap
        chamado = self.tabela_hash.buscar(codigo)

        if not chamado:
            print(f"❌ Erro Crítico: Prontuário do chamado '{codigo}' não encontrado na Tabela Hash!")
            return None

        # Cálculo de rota tática via BFS
        rota = self.grafo.calcular_rota_bfs(base, chamado.localizacao)

        # Registra despacho na pilha LIFO
        self.pilha_despachos.empilhar(chamado)

        mapa_gravidade = {
            1: "🔴 RED (Gravidade 1 - Risco Iminente de Óbito)",
            2: "🟡 YELLOW (Gravidade 2 - Quadro Grave / Sem Risco Iminente)",
            3: "🟢 GREEN (Gravidade 3 - Quadro Estável / Ferimentos Leves)"
        }

        desc_gravidade = mapa_gravidade.get(chamado.gravidade, f"Nível {chamado.gravidade}")
        str_rota = " ➔ ".join(rota) if rota else "Nenhuma rota encontrada (Ponto Inalcançável)"
        num_vias = (len(rota) - 1) if rota else -1

        print(f"🚑 [DESPACHO EFETUADO] Código Triagem: {chamado.codigo_triagem}")
        print(f" ├─ Solicitante     : {chamado.solicitante}")
        print(f" ├─ Situação        : {chamado.descricao_paciente}")
        print(f" ├─ Classificação   : {desc_gravidade}")
        print(f" ├─ Ordem Chegada   : #{chamado.ordem_chegada}")
        print(f" ├─ Local de Destino: {chamado.localizacao}")
        print(f" ├─ Vias Transitadas: {num_vias} trecho(s)")
        print(f" └─ Trajeto Tático  : {str_rota}")
        print("-" * 75)

        return {
            "codigo": chamado.codigo_triagem,
            "chamado": chamado,
            "rota": rota,
            "trechos": num_vias
        }

    def abortar_ultimo_despacho(self) -> Optional[ChamadoResgate]:
        """
        DIFERENCIAL TÁTICO: Aborta/desfaz o último despacho realizado (LIFO).
        Desempilha o chamado da PilhaDespacho e o reinsere no MinHeap PRESERVANDO
        sua ordem_chegada original para manter a estabilidade da triagem.
        """
        print("\n" + "⚠️ " * 3 + "OPERAÇÃO TÁTICA: ABORTAR ÚLTIMO DESPACHO SOLICITADO" + " ⚠️ " * 3)

        chamado_abortado = self.pilha_despachos.desempilhar()
        if not chamado_abortado:
            print("❌ Falha: Não há despachos recentes no histórico para abortar.")
            return None

        print(f"🚨 CANCELAMENTO DE EMERGÊNCIA: Redirecionando equipe do chamado '{chamado_abortado.codigo_triagem}'!")
        print(f"   • Solicitante   : {chamado_abortado.solicitante}")
        print(f"   • Local         : {chamado_abortado.localizacao}")
        print(f"   • Ordem Origem  : #{chamado_abortado.ordem_chegada}")
        print(f"   • Motivo        : Equipe re-encaminhada para atendimento emergencial.")

        # Reinsere a ocorrência no Heap preservando a ordem de chegada original
        self.heap_prioridade.inserir(
            (chamado_abortado.gravidade, chamado_abortado.ordem_chegada, chamado_abortado.codigo_triagem)
        )
        print(f"✅ Chamado '{chamado_abortado.codigo_triagem}' reintegrado com sucesso ao MinHeap (Ordem Original #{chamado_abortado.ordem_chegada}).\n")

        return chamado_abortado


# =============================================================================
# BLOCO DE DEMONSTRAÇÃO REAL / CENÁRIO TÁTICO (IF __NAME__ == "__MAIN__")
# =============================================================================
if __name__ == "__main__":
    print("=" * 75)
    print("   RESCUEROUTE — SISTEMA TÁTICO DE RESGATE E TRIAGEM (DEFESA CIVIL / SAMU)")
    print("=" * 75)

    # 1. Instanciação do Centro Operacional
    central = CentroOperacoesResgate(capacidade_hash=8)

    # 2. Cadastro da Malha Viária Urbana (Grafo não direcionado)
    print("\n🗺️  [1/4] CADASTRANDO MALHA VIÁRIA (GRAFO POR LISTA DE ADJACÊNCIA)...")
    vias_urbanas = [
        ("Base-Central", "Hospital Regional"),
        ("Base-Central", "Setor Comercial"),
        ("Hospital Regional", "Ponte Norte"),
        ("Setor Comercial", "Morro Alto"),
        ("Ponte Norte", "Bairro Ribeirinho"),
        ("Morro Alto", "Bairro Ribeirinho")
    ]

    for orig, dest in vias_urbanas:
        central.registrar_via(orig, dest)
        print(f"  • Via liberada: {orig} ↔ {dest}")

    # Exibe estrutura interna do Grafo
    print("\n  [Estrutura Interna do Grafo (Lista de Adjacência)]:")
    for vertice, vizinhos in central.grafo.conexoes.items():
        print(f"    - {vertice}: {vizinhos}")

    # 3. Entrada dos Chamados de Socorro
    # REQUISITO CRÍTICO DE PROVA: O chamado de emergência vital (Gravidade 1),
    # inserido por ÚLTIMO, DEVE ser despachado PRIMEIRO.
    print("\n📞 [2/4] RECEBENDO CHAMADOS DE EMERGÊNCIA (TRIAGEM E TABELA HASH)...")

    chamados_iniciais = [
        ("RESG-101", "Morro Alto", 3, "Queda de galho / Vítima com escoriações leves", "João Silva"),
        ("RESG-102", "Hospital Regional", 2, "Falta de insumo de oxigênio / Paciente grave", "Dra. Ana"),
        ("RESG-103", "Bairro Ribeirinho", 3, "Família ilhada pela enchente / Sem feridos", "Maria Souza"),
        # Chamado crítico inserido por ÚLTIMO no sistema
        ("RESG-999", "Bairro Ribeirinho", 1, "Criança soterrada por deslizamento / RISCO DE ÓBITO", "Pedro Santos")
    ]

    for cod, loc, grav, desc, sol in chamados_iniciais:
        central.receber_chamado(cod, loc, grav, desc, sol)
        print(f"  • Registrado: ID={cod} | Gravidade={grav} | Local={loc} | '{desc}'")

    print("\n🔍 Teste de Busca O(1) na Tabela Hash (Metadados do RESG-999):")
    ficha_teste = central.tabela_hash.buscar("RESG-999")
    hash_idx = central.tabela_hash._hash("RESG-999")
    print(f"  • RESG-999 -> Índice Hash #{hash_idx}: {ficha_teste}")

    print("\n📊 Estado Interno da Fila de Prioridades (MinHeap Array):")
    print(f"  • Heap Array: {central.heap_prioridade.dados}")
    print("    (Note que a raiz dados[0] é o chamado crítico RESG-999 de Gravidade 1)")

    # 4. Despacho Sequencial das Equipes de Resgate
    print("\n🚨 [3/4] INICIANDO DESPACHO TÁTICO DAS EQUIPES DE SOCORRO...")
    print("=" * 75)

    despacho_1 = central.despachar_proximo_resgate(base="Base-Central")
    despacho_2 = central.despachar_proximo_resgate(base="Base-Central")

    # 5. Prova do Diferencial: Operação de "Abortar/Desfazer Último Despacho" via Pilha LIFO
    print("\n🔄 [4/4] DEMONSTRAÇÃO DO DIFERENCIAL TÁTICO: PILHA LIFO DE DESPACHO...")
    print(f"  • Total de despachos empilhados na Pilha: {len(central.pilha_despachos)} chamado(s)")
    print(f"  • Topo da Pilha LIFO (Último despachado): {central.pilha_despachos.espiar().codigo_triagem}")

    # Aciona a operação de abortar último despacho
    central.abortar_ultimo_despacho()

    # Processa os chamados restantes na fila
    print("🚨 PROCESSANDO FILA REINTEGRADA APÓS CANCELAMENTO TÁTICO:")
    print("=" * 75)
    despacho_3 = central.despachar_proximo_resgate(base="Base-Central")
    despacho_4 = central.despachar_proximo_resgate(base="Base-Central")
    despacho_5 = central.despachar_proximo_resgate(base="Base-Central")

    # 6. Validação das Regras do Negócio
    print("=" * 75)
    print("🏆 VALIDAÇÃO FINAL DAS REGRAS DO PROJETO (RESCUEROUTE):")
    print(f"  • Último chamado registrado na Triagem : RESG-999 (Gravidade 1 - Crítico)")
    print(f"  • Primeiro chamado despachado no Heap  : {despacho_1['codigo']}")

    if despacho_1["codigo"] == "RESG-999":
        print("  ✅ TESTE MIN-HEAP APROVADO: O chamado médico emergencial inserido por último foi atendido em PRIMEIRO lugar!")
    else:
        print("  ❌ TESTE MIN-HEAP FALHOU!")

    if despacho_3["codigo"] == "RESG-102":
        print("  ✅ TESTE PILHA LIFO APROVADO: O chamado abortado (RESG-102) manteve a ordem original e foi despachado imediatamente após a reintegração.")
    else:
        print("  ❌ TESTE PILHA LIFO FALHOU!")

    print("=" * 75)
