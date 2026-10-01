# 🚚 TechDepot Logistics — Sistema Tático de Logística e Estoque de Hardware

> **Projeto Final Integrado (PBL)** — Disciplina de Estruturas de Dados e Algoritmos (EDA)
> **Autor:** Thiago da Silva Lopes
> **Ambiente:** Python 3.10+ (Biblioteca Padrão) | SQLite3 Relacional | 0 Dependências Externas

---

```text
  ████████╗███████╗██╗  ██╗██████╗ ███████╗██████╗  ██████╗ ████████╗
  ╚══██╔══╝██╔════╝██║  ██║██╔══██╗██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝
     ██║   █████╗  ███████║██║  ██║█████╗  ██████╔╝██║   ██║   ██║   
     ██║   ██╔══╝  ██╔══██║██║  ██║██╔══╝  ██╔═══╝ ██║   ██║   ██║   
     ██║   ███████╗██║  ██║██████╔╝███████╗██║     ╚██████╔╝   ██║   
     ╚═╝   ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝      ╚═════╝    ╚═╝   
       LOGISTICS — SISTEMA TÁTICO DE ESTOQUE E EXPEDIÇÃO DE HARDWARE
```

---

## 📌 1. Visão Geral do Projeto

O **TechDepot Logistics** é uma solução completa de terminal CLI desenvolvida do zero para simular um centro de distribuição e logística de peças de computador.

O sistema resolve quatro desafios centrais de armazenagem e e-commerce:
1. **Indexação e Busca Instantânea:** Acesso a peças por SKU em tempo constante $O(1)$.
2. **Despacho Prioritário por Urgência:** Fila de prioridades com desempate FIFO para separação de pedidos em $O(\log n)$.
3. **Rotas Otimizadas no Depósito:** Cálculo do menor trajeto entre a Expedição e os corredores via **Busca em Largura (BFS)** em Grafos $O(V + E)$.
4. **Rastreabilidade e Reversão (Undo):** Pilha encadeada $O(1)$ para auditoria e reversão de lançamentos incorretos.

---

## 🧰 2. As 4 Estruturas de Dados Fundamentais (Desenvolvidas do Zero)

| Estrutura | Aplicação no Sistema | Complexidade | Funcionamento Interno |
| :--- | :--- | :--- | :--- |
| **`TabelaHash`** | Catálogo de peças indexadas por SKU | $O(1)$ médio | Tratamento de colisões por encadeamento (*chaining*) e redimensionamento automático de capacidade quando o fator de carga ultrapassa 0.75. |
| **`MinHeap`** | Fila de prioridades de separação de pedidos | $O(\log n)$ | Min-Heap binária armazenada em vetor. O menor valor numérico representa maior urgência, e a ordem de chegada desempata em caso de empate (FIFO). |
| **`Grafo`** | Layout de corredores e setores do depósito | $O(V + E)$ | Representação por Lista de Adjacência. Executa a Busca em Largura (BFS) para determinar o menor caminho em número de saltos entre setores. |
| **`PilhaOperacoes`** | Histórico e mecanismo de desfazer (Undo) | $O(1)$ | Pilha LIFO encadeada por Nós (`NoPilha`) para reverter entradas e ajustes com consistência e registro na trilha de auditoria. |

---

## 🏗️ 3. Diagrama do Fluxo de Dados e Arquitetura

```mermaid
flowchart TD
    A[Terminal CLI / Menu Interativo] --> B[GerenciadorEstoque - Camada de Serviços]
    B --> C[TabelaHash - Busca SKU O(1)]
    B --> D[MinHeap - Prioridade Pedidos O(log n)]
    B --> E[Grafo - Rotas de Coleta BFS O(V+E)]
    B --> F[PilhaOperacoes - Desfazer Operações O(1)]
    B --> G[(SQLite - Persistência Relacional)]
```

---

## 🚀 4. Principais Funcionalidades

- **📊 Dashboard de Indicadores em Tempo Real:** Painel consolidado com total de SKUs, unidades físicas, patrimônio total em Reais (R$), itens críticos e métricas de expedição.
- **🔤 Procura e Ordenação Alfabética (A-Z):** Consulta dinâmica por ordenação alfabética por Nome do Produto ou SKU.
- **💰 Valores Monetários sem Ponto Flutuante:** Custo e preço armazenados como inteiros em centavos para eliminar erros de precisão decimal.
- **🛡️ Validações Estritas:** Impede duplicidade de SKU, saldo negativo de estoque e separações de pedidos com itens inalcançáveis no depósito.
- **🔄 Carga Demonstrativa Opcional:** Função para incluir 17 produtos de exemplo; não altera SKUs já cadastrados. O arquivo `estoque.db` incluído no repositório já vem com um catálogo demonstrativo.

---

## 💻 5. Instruções de Execução

### Pré-requisitos
- **Python 3.10 ou superior**.
- Nenhuma instalação de biblioteca externa é necessária.

### Executar a Aplicação (CLI)
No terminal da pasta do projeto:
```bash
python rescueroute.py
```
*(Ou utilize o ponto de entrada secundário `python simulador_logistica.py`)*

### Executar a Suíte de Testes Automatizados (28 Testes)
```bash
python -m unittest discover -v
```

---

## 📋 6. Exemplo de Ciclo de Vida de um Pedido

1. **Criação:** Cliente solicita o Pedido `#PED-101` contendo `2x GPU-RTX-4060` com Urgência Alta (1).
2. **MinHeap:** O pedido entra na posição de topo do MinHeap por conta de sua urgência máxima.
3. **Separação & BFS:** O operador aciona "Separar Pedido". O sistema valida o saldo livre, gera a rota BFS (`EXPEDICAO` $\to$ `RECEBIMENTO` $\to$ `CORREDOR-A` $\to$ `SETOR-PLACAS`) e reserva o estoque.
4. **Expedição:** Na expedição final, o estoque físico é baixado e a reserva é zerada de forma atômica no SQLite.
