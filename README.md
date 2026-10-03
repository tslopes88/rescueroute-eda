# TecLogística — Sistema de Gestão de Estoque e Expedição

- **Trabalho:** Projeto final de Estruturas de Dados e Algoritmos (EDA)
- **Autor:** Thiago da Silva Lopes
- **Linguagem:** Python 3.10 ou superior
- **Banco de dados:** SQLite3

---

## 1. Visão Geral

O **TecLogística** é uma simulação em linha de comando de um pequeno centro de distribuição de peças de computador. Pelo menu, é possível cadastrar produtos, acompanhar o estoque, separar pedidos e registrar vendas. O projeto é acadêmico: não foi pensado para controlar uma operação comercial real.

O objetivo principal é mostrar como as estruturas de dados estudadas em EDA podem ajudar nessas tarefas:

1. **Busca por SKU:** A tabela hash localiza uma peça pelo código, em tempo médio $O(1)$.
2. **Ordem dos pedidos:** A fila de prioridades atende primeiro os pedidos mais urgentes; em caso de empate, vale a ordem de chegada.
3. **Caminho no depósito:** O grafo representa corredores e setores. A busca em largura (BFS) encontra um caminho com o menor número de trechos, em $O(V + E)$.
4. **Desfazer movimentações:** A pilha mantém entradas e ajustes recentes para que a última operação possa ser desfeita, em $O(1)$.

O mapa considera que cada trecho entre dois setores tem o mesmo custo. Por isso, a BFS encontra o caminho com menos trechos, não necessariamente o mais curto em metros ou o mais rápido.

---

## 2. Estruturas de Dados Implementadas

| Estrutura | Aplicação no Sistema | Complexidade | Detalhes de Implementação |
| :--- | :--- | :--- | :--- |
| **`TabelaHash`** | Catálogo de peças indexadas por SKU | $O(1)$ médio | Implementada do zero com encadeamento separado (*chaining*) para tratamento de colisões e redimensionamento dinâmico ao ultrapassar o fator de carga de 0,75. |
| **`MinHeap`** | Fila de prioridades para separação de pedidos | $O(\log n)$ | Min-Heap binária representada sobre vetor. O menor valor numérico indica maior prioridade (1 = Alta, 2 = Média, 3 = Baixa). Desempate por FIFO mantendo a ordem de inserção. |
| **`Grafo`** | Mapeamento dos setores e corredores do galpão | $O(V + E)$ | Representado por Lista de Adjacência. O algoritmo de Busca em Largura (BFS) determina o caminho com menor número de conexões entre a Expedição e a peça. |
| **`PilhaOperacoes`** | Desfazer entradas e ajustes de estoque | $O(1)$ | Pilha LIFO encadeada por nós. A última operação registrada é a primeira que pode ser desfeita. |

### Um pedido do começo ao fim

1. Cadastre as peças que farão parte do pedido.
2. Crie o pedido e informe sua urgência e os itens desejados.
3. Separe o pedido: o sistema verifica o saldo disponível, reserva as peças e calcula as rotas no depósito.
4. Expedir o pedido dá baixa nas unidades reservadas e registra a venda.

---

## 3. Arquitetura e Organização do Código

```text
Projeto_Final/
├── teclogistica.py          # Ponto de entrada principal da aplicação
├── cli.py                   # Interface de usuário via terminal e menus
├── servicos.py              # Camada de serviços e regras de negócio
├── banco.py                 # Persistência e transações relacionais em SQLite
├── estruturas.py            # Implementação manual das 4 estruturas de dados
├── modelos.py               # Classes de domínio (Peca, Pedido, Venda, Movimentacao)
├── rescueroute.py           # Ponto de entrada secundário (compatibilidade)
├── simulador_logistica.py   # Ponto de entrada secundário (compatibilidade)
└── tests/                   # Suíte de testes unitários e de integração
    ├── test_estoque.py
    ├── test_rescueroute.py
    └── test_teclogistica.py
```

---

## 4. Funcionalidades Principais

- **Painel de Indicadores (Dashboard):** Consulta consolidada de total de SKUs, unidades físicas em estoque, total reservado, patrimônio estocado e faturamento.
- **Catálogo de Peças:** Cadastro, consulta direta por SKU em $O(1)$, pesquisa por nome/categoria e ordenação alfabética (A-Z).
- **Movimentação de Estoque:** Registro de entradas (recebimento), ajustes de estoque (ganhos/perdas) e funcionalidade de desfazer a última ação (*undo*).
- **Gestão de Pedidos:** A separação reserva o estoque e calcula as rotas de coleta. Na expedição, a baixa, o histórico e a venda são gravados juntos.
- **Gestão de Vendas:** Registro de vendas diretas (PDV) e relatórios com ranking dos produtos mais vendidos.
- **Controle Financeiro:** Todos os valores monetários são calculados e armazenados em centavos (números inteiros) para evitar imprecisões de ponto flutuante.

---

## 5. Instruções de Execução

### Requisitos
- Python 3.10 ou superior.
- Não é necessária a instalação de dependências externas (utiliza apenas a biblioteca padrão do Python).

### Executar a Aplicação
No terminal, na pasta raiz do projeto:

```bash
python teclogistica.py
```

### Executar os Testes Automatizados
A suíte automatizada verifica as estruturas de dados, as regras de negócio e a persistência, incluindo situações de erro e reversão de operações. Para executá-la:

```bash
python -m unittest discover -v
```
