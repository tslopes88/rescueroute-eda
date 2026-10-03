# 📦 TecLogística — Sistema de Gestão de Estoque e Expedição

> 🖥️ **Do cadastro à expedição:** uma simulação prática de logística para peças de computador.
>
> 🔎 Encontre peças · 🚦 Priorize pedidos · 🗺️ Planeje rotas · 📦 Controle o estoque

- 🎓 **Trabalho:** Projeto final de Estruturas de Dados e Algoritmos (EDA)
- 👨‍💻 **Autor:** Thiago da Silva Lopes
- 🐍 **Linguagem:** Python 3.10 ou superior
- 🗄️ **Banco de dados:** SQLite3

---

## 👋 1. Visão Geral

O **TecLogística** é uma simulação em linha de comando de um pequeno centro de distribuição de peças de computador. Pelo menu, dá para cadastrar produtos, acompanhar o estoque, separar pedidos e registrar vendas.

🎓 **É um projeto acadêmico**, criado para praticar estruturas de dados — não para controlar uma operação comercial real.

💡 A ideia é mostrar como essas estruturas ajudam no dia a dia do sistema:

1. 🔎 **Busca por SKU:** A tabela hash localiza uma peça pelo código, em tempo médio $O(1)$.
2. 🚦 **Ordem dos pedidos:** A fila de prioridades atende primeiro os pedidos mais urgentes; em caso de empate, vale a ordem de chegada.
3. 🗺️ **Caminho no depósito:** O grafo representa corredores e setores. A busca em largura (BFS) encontra um caminho com o menor número de trechos, em $O(V + E)$.
4. ↩️ **Desfazer movimentações:** A pilha mantém entradas e ajustes recentes para que a última operação possa ser desfeita, em $O(1)$.

> 🧭 **Sobre as rotas:** cada trecho do mapa tem o mesmo custo. A BFS encontra o caminho com menos trechos, não necessariamente o mais curto em metros ou o mais rápido.

---

## 🧩 2. Estruturas de Dados

| Estrutura | Aplicação no Sistema | Complexidade | Detalhes de Implementação |
| :--- | :--- | :--- | :--- |
| **`TabelaHash`** | Catálogo de peças indexadas por SKU | $O(1)$ médio | Implementada do zero com encadeamento separado (*chaining*) para tratamento de colisões e redimensionamento dinâmico ao ultrapassar o fator de carga de 0,75. |
| **`MinHeap`** | Fila de prioridades para separação de pedidos | $O(\log n)$ | Min-Heap binária representada sobre vetor. O menor valor numérico indica maior prioridade (1 = Alta, 2 = Média, 3 = Baixa). Desempate por FIFO mantendo a ordem de inserção. |
| **`Grafo`** | Mapeamento dos setores e corredores do galpão | $O(V + E)$ | Representado por Lista de Adjacência. O algoritmo de Busca em Largura (BFS) determina o caminho com menor número de conexões entre a Expedição e a peça. |
| **`PilhaOperacoes`** | Desfazer entradas e ajustes de estoque | $O(1)$ | Pilha LIFO encadeada por nós. A última operação registrada é a primeira que pode ser desfeita. |

### 🛒 Pedido em 4 passos

1. 🧰 Cadastre as peças que farão parte do pedido.
2. 📝 Crie o pedido e informe a urgência e os itens.
3. 🗺️ Separe o pedido: o sistema confere o estoque, reserva as peças e calcula as rotas.
4. 🚚 Faça a expedição: o sistema dá baixa nas unidades e registra a venda.

✅ **Pronto!** O estoque e a venda ficam atualizados juntos.

---

## 🛠️ 3. Organização do Código

```text
Projeto_Final/
├── teclogistica.py          # Ponto de entrada principal da aplicação
├── cli.py                   # Interface de usuário via terminal e menus
├── servicos.py              # Camada de serviços e regras de negócio
├── banco.py                 # Persistência e transações relacionais em SQLite
├── estruturas.py            # Implementação manual das 4 estruturas de dados
├── modelos.py               # Classes de domínio (Peca, Pedido, Venda, Movimentacao)
├── rescueroute.py           # Ponto de entrada secundário (compatibilidade)
└── simulador_logistica.py   # Ponto de entrada secundário (compatibilidade)
```

---

## ✨ 4. O que dá para fazer

- 📊 **Painel de indicadores:** Consulta de produtos, unidades, reservas, valor em estoque e faturamento.
- 🧰 **Catálogo de peças:** Cadastro, busca por SKU, pesquisa por nome ou categoria e ordenação alfabética.
- 📥 **Movimentação de estoque:** Registro de entradas e ajustes, com opção para desfazer a última operação.
- 📦 **Pedidos e expedição:** Reserva de peças, cálculo de rotas e registro da saída e da venda.
- 💰 **Vendas:** Registro de vendas no balcão e relatório dos produtos mais vendidos.
- 🧮 **Valores certinhos:** Preços são guardados em centavos inteiros para evitar imprecisão nos cálculos.

---

## 🚀 5. Como executar

### 📋 O que você precisa
- Python 3.10 ou superior.
- Nenhuma biblioteca extra: o projeto usa recursos que já vêm com o Python.

### ▶️ Abrir o sistema
Abra o terminal na pasta do projeto e rode:

```bash
python teclogistica.py
```

✨ **Bom estudo e boas expedições!**
