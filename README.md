# 🚑 RescueRoute — Sistema Tático de Triagem e Despacho de Resgate

> **Projeto Final Integrado (PBL)**  
> **Disciplina:** Estruturas de Dados e Algoritmos (EDA)  
> **Autor:** Thiago da Silva Lopes  
> **Linguagem:** Python 3.10+ (Executado de forma nativa sem bibliotecas externas)

---

## 📌 1. Introdução e Contexto do Problema

Em situações de catástrofes urbanas (como enchentes e deslizamentos de terra), a central de emergências da Defesa Civil e do SAMU recebe chamados ininterruptos com gravidades médicas heterogêneas.

O uso de filas tradicionais First-In, First-Out (FIFO) falha gravemente nesses cenários: se uma vítima presa em deslizamento com risco de óbito acionar o socorro por último, ela ficaria aguardando no fim da fila atrás de ocorrências de ferimentos leves recebidas anteriormente.

O **RescueRoute** foi projetado para resolver essa lacuna através de um sistema de despacho tático automatizado em terminal. O software unifica **quatro estruturas de dados fundamentais construídas 100% do zero**, sem abstrações de bibliotecas como `heapq` ou `networkx`, evidenciando o gerenciamento direto de vetores, indexação matemática e travessias em memória RAM.

---

## 🧠 2. Fundamentação Teórica e Defesa das Estruturas de Dados

Para a avaliação em banca acadêmica, a escolha de cada estrutura de dados é fundamentada nos princípios de complexidade assintótica e eficiência estrutural:

### 🔹 2.1. Tabela Hash com Encadeamento Separado (`TabelaHash`) — Prontuários Médicos
* **Modelagem Teórica:** Para acessar instantaneamente o prontuário de um chamado (`localização`, `gravidade`, `descrição médica`, `solicitante`) a partir do seu `codigo_triagem` (ex: `RESG-999`), a busca linear em listas simples demandaria tempo $O(n)$.
* **Função Hash Modular:** Implementamos a função hash através da soma dos códigos ASCII dos caracteres da chave módulo o tamanho da tabela:
  $$\text{hash}(k) = \left( \sum_{c \in k} \text{ord}(c) \right) \bmod \text{tamanho}$$
* **Tratamento de Colisões:** Colisões são tratadas por encadeamento separado (*chaining*), onde cada balde (*bucket*) contém uma sublista contendo pares `[chave, objeto_chamado]`.
* **Defesa contra BST:** Uma Árvore Binária de Busca (BST) exigiria custo $O(\log n)$ e sobrecarga de rotações AVL para evitar degeneração. Como a ordenação alfabética dos códigos é irrelevante, o tempo médio constante $O(1)$ da Tabela Hash é a solução ótima.

### 🔹 2.2. Min-Heap Binária em Array (`MinHeap`) — Fila de Prioridade Médica
* **Modelagem Teórica:** A propriedade de Min-Heap garante que a raiz armazene sempre o elemento de menor valor numérico de gravidade (1 = Risco Iminente de Óbito / Vermelho).
* **Mapeamento em Vetor (Sem Ponteiros):** A árvore binária quase completa é mapeada em um array (`dados = []`) utilizando navegação por índices matemáticos:
  - **Pai de $i$:** $\lfloor \frac{i - 1}{2} \rfloor$
  - **Filho Esquerdo de $i$:** $2i + 1$
  - **Filho Direito de $i$:** $2i + 2$
* **Garantia de Estabilidade:** Os elementos são armazenados como tuplas `(gravidade, ordem_chegada, codigo_triagem)`. O atributo `ordem_chegada` atua como critério de desempate estável (FIFO) entre chamados de urgência idêntica.
* **Complexidade:** As operações de subida (`_sobe`) na inserção e descida (`_desce`) na remoção da raiz operam estritamente em $O(\log n)$, reajustando a altura da árvore binária.

### 🔹 2.3. Grafo e Busca em Largura (`Grafo` + BFS) — Malha Viária e Rota Mínima
* **Modelagem Teórica:** A malha urbana é representada por um Grafo não direcionado via Lista de Adjacência (`self.conexoes = {}`), otimizada para grafos esparsos com consumo espacial $O(V + E)$.
* **Algoritmo de Busca em Largura (BFS):** Explora o grafo em camadas concêntricas a partir da Base Operacional utilizando uma fila FIFO (`collections.deque` com `popleft()` em $O(1)$) e um dicionário de mapeamento `predecessor = {vertice: pai}`.
* **Prova de Optimalidade:** A BFS garante matematicamente a descoberta do caminho com o **menor número de vias/arestas** até o destino em tempo $O(V + E)$. O algoritmo possui guarda contra nós inalcançáveis para evitar exceções em componentes desconexos.

### 🔹 2.4. Pilha Encadeada LIFO (`PilhaDespacho`) — Cancelamento Tático
* **Modelagem Teórica:** Em operações táticas, o envio de uma equipe para uma ocorrência grave (Gravidade 2) pode precisar ser abortado se um chamado com risco imediato de óbito (Gravidade 1) for recebido no instante seguinte.
* **Estrutura Encadeada:** Modelada com nós dinâmicos (`NoPilha`) e ponteiro de `topo`. O método `empilhar` registra cada envio em $O(1)$, enquanto a operação `abortar_ultimo_despacho()` remove o topo em $O(1)$ e reinsere a ocorrência no Min-Heap **preservando sua `ordem_chegada` original**.

---

## ⏱️ 3. Tabela Formal de Complexidade Assintótica

| Estrutura de Dados | Operação / Método | Melhor Caso | Caso Médio | Pior Caso | Complexidade Espacial |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **TabelaHash** | `inserir(codigo, ficha)` | $O(1)$ | $O(1)$ | $O(n)$ | $O(n)$ |
| **TabelaHash** | `buscar(codigo)` | $O(1)$ | $O(1)$ | $O(n)$ | $O(n)$ |
| **MinHeap** | `inserir(item)` (`_sobe`) | $O(1)$ | $O(\log n)$ | $O(\log n)$ | $O(n)$ |
| **MinHeap** | `extrair_min()` (`_desce`) | $O(1)$ | $O(\log n)$ | $O(\log n)$ | $O(n)$ |
| **Grafo** | `adicionar_via(a, b)` | $O(1)$ | $O(1)$ | $O(1)$ | $O(V + E)$ |
| **Grafo** | `calcular_rota_bfs(origem, dest)` | $O(1)$ | $O(V + E)$ | $O(V + E)$ | $O(V)$ |
| **PilhaDespacho** | `empilhar()` / `desempilhar()` | $O(1)$ | $O(1)$ | $O(1)$ | $O(k)$ |

---

## 💻 4. Guia de Reprodução e Execução

### Pré-requisitos
- Python 3.10 ou superior instalado na máquina.
- Nenhuma biblioteca externa necessária (utiliza apenas os módulos nativos `sys` e `collections`).

### Passo a Passo via Terminal
1. Clone este repositório público:
   ```bash
   git clone https://github.com/thiagoslopes/rescueroute-eda.git
   cd rescueroute-eda
   ```
2. Execute o arquivo do simulador:
   ```bash
   python simulador_logistica.py
   ```
   *(ou `python rescueroute.py`)*

---

## 🔬 5. Roteiro de Demonstração e Logs Reais do Terminal

No bloco de teste interativo, o sistema simula a seguinte sequência operacional:
1. **Malha Viária Cadastrada (6 Nós):** `Base-Central` $\leftrightarrow$ `Hospital Regional` $\leftrightarrow$ `Ponte Norte` $\leftrightarrow$ `Bairro Ribeirinho` $\leftrightarrow$ `Morro Alto` $\leftrightarrow$ `Setor Comercial`.
2. **Entrada de Chamados:**
   - `RESG-101` (Morro Alto) $\to$ Gravidade 3 (Verde / Estável)
   - `RESG-102` (Hospital Regional) $\to$ Gravidade 2 (Amarelo / Grave)
   - `RESG-103` (Bairro Ribeirinho) $\to$ Gravidade 3 (Verde / Estável)
   - **`RESG-999` (Bairro Ribeirinho) $\to$ Gravidade 1 (VERMELHO / RISCO DE ÓBITO) — Inserido por ÚLTIMO.**

### Saída Oficial do Terminal:
```plaintext
===========================================================================
   RESCUEROUTE — SISTEMA TÁTICO DE RESGATE E TRIAGEM (DEFESA CIVIL / SAMU)
===========================================================================

🗺️  [1/4] CADASTRANDO MALHA VIÁRIA (GRAFO POR LISTA DE ADJACÊNCIA)...
  • Via liberada: Base-Central ↔ Hospital Regional
  • Via liberada: Base-Central ↔ Setor Comercial
  • Via liberada: Hospital Regional ↔ Ponte Norte
  • Via liberada: Setor Comercial ↔ Morro Alto
  • Via liberada: Ponte Norte ↔ Bairro Ribeirinho
  • Via liberada: Morro Alto ↔ Bairro Ribeirinho

📞 [2/4] RECEBENDO CHAMADOS DE EMERGÊNCIA (TRIAGEM E TABELA HASH)...
  • Registrado: ID=RESG-101 | Gravidade=3 | Local=Morro Alto | 'Queda de galho / Vítima com escoriações leves'
  • Registrado: ID=RESG-102 | Gravidade=2 | Local=Hospital Regional | 'Falta de insumo de oxigênio / Paciente grave'
  • Registrado: ID=RESG-103 | Gravidade=3 | Local=Bairro Ribeirinho | 'Família ilhada pela enchente / Sem feridos'
  • Registrado: ID=RESG-999 | Gravidade=1 | Local=Bairro Ribeirinho | 'Criança soterrada por deslizamento / RISCO DE ÓBITO'

🚨 [3/4] INICIANDO DESPACHO TÁTICO DAS EQUIPES DE SOCORRO...
===========================================================================
🚑 [DESPACHO EFETUADO] Código Triagem: RESG-999
 ├─ Solicitante     : Pedro Santos
 ├─ Situação        : Criança soterrada por deslizamento / RISCO DE ÓBITO
 ├─ Classificação   : 🔴 RED (Gravidade 1 - Risco Iminente de Óbito)
 ├─ Ordem Chegada   : #4
 ├─ Local de Destino: Bairro Ribeirinho
 ├─ Vias Transitadas: 3 trecho(s)
 └─ Trajeto Tático  : Base-Central ➔ Hospital Regional ➔ Ponte Norte ➔ Bairro Ribeirinho
---------------------------------------------------------------------------
🚑 [DESPACHO EFETUADO] Código Triagem: RESG-102
 ├─ Solicitante     : Dra. Ana
 ├─ Situação        : Falta de insumo de oxigênio / Paciente grave
 ├─ Classificação   : 🟡 YELLOW (Gravidade 2 - Quadro Grave / Sem Risco Iminente)
 ├─ Ordem Chegada   : #2
 ├─ Local de Destino: Hospital Regional
 ├─ Vias Transitadas: 1 trecho(s)
 └─ Trajeto Tático  : Base-Central ➔ Hospital Regional
---------------------------------------------------------------------------

🔄 [4/4] DEMONSTRAÇÃO DO DIFERENCIAL TÁTICO: PILHA LIFO DE DESPACHO...
⚠️ OPERAÇÃO TÁTICA: ABORTAR ÚLTIMO DESPACHO SOLICITADO ⚠️
🚨 CANCELAMENTO DE EMERGÊNCIA: Redirecionando equipe do chamado 'RESG-102'!
✅ Chamado 'RESG-102' reintegrado com sucesso ao MinHeap (Ordem Original #2).

===========================================================================
🏆 VALIDAÇÃO FINAL DAS REGRAS DO PROJETO (RESCUEROUTE):
  • Último chamado registrado na Triagem : RESG-999 (Gravidade 1 - Crítico)
  • Primeiro chamado despachado no Heap  : RESG-999
  ✅ TESTE MIN-HEAP APROVADO: O chamado médico emergencial inserido por último foi atendido em PRIMEIRO lugar!
  ✅ TESTE PILHA LIFO APROVADO: O chamado abortado (RESG-102) manteve a ordem original e foi despachado imediatamente após a reintegração.
===========================================================================
```

---

## ⚙️ 6. Delimitação de Escopo (Decisões de Projeto)

1. **Ausência de Pesos em Distância (Algoritmo de Dijkstra):** As vias urbanas possuem peso de aresta unitário ($1$). O algoritmo de busca em largura (BFS) é a escolha ideal para grafos não ponderados. Grafos ponderados via Dijkstra foram omitidos por extrapolarem o foco acadêmico do trabalho.
2. **Interface em Linha de Comando (CLI):** O projeto prioriza a clareza e a observabilidade das estruturas de dados em memória RAM via terminal formatado, sem contaminação com frameworks gráficos (GUI) ou web.
3. **Persistência em Memória RAM:** Os dados residem em memória principal durante a execução, eliminando latências de I/O e focando estritamente na análise assintótica.
