# 🚑 Simulação de Despacho para Atendimento de Emergências

Este projeto foi desenvolvido como trabalho final da disciplina de **Estruturas de Dados e Algoritmos**. O objetivo é aplicar estruturas fundamentais na triagem de ocorrências e na busca de rotas entre pontos de um mapa fictício. A aplicação roda no terminal e tem propósito exclusivamente didático.

## 🧭 Funcionamento

1. Cada chamado é registrado com identificador, local e nível de gravidade.
2. A fila de prioridade organiza os atendimentos pela urgência. Em caso de empate, vale a ordem de chegada.
3. O sistema calcula uma rota entre a base de atendimento e o local do chamado.
4. Se o último despacho for cancelado, a ocorrência retorna à fila com sua prioridade original.
5. Se não houver rota até o destino, o chamado permanece na fila aguardando a liberação de um caminho.

## 🧰 Estruturas de dados utilizadas

- **Tabela hash** 🔎 — armazena os chamados e permite buscá-los pelo código. A consulta tem custo médio O(1), mas pode chegar a O(n) no pior caso, quando há muitas colisões.
- **Min-heap (fila de prioridade)** 🚨 — organiza os atendimentos pela gravidade e pela ordem de chegada.
- **Grafo e busca em largura (BFS)** 🗺️ — representa as conexões entre os locais e encontra uma rota com o menor número de trechos.
- **Pilha (LIFO)** ↩️ — registra os despachos e permite cancelar o mais recente.

As estruturas foram implementadas no próprio código, sem pacotes externos, para praticar os conceitos estudados na disciplina.

## ▶️ Execução

O projeto requer **Python 3.10 ou superior** e usa apenas a biblioteca padrão.

Para iniciar a aplicação:

```bash
python rescueroute.py
```

O script antigo `simulador_logistica.py` também continua funcionando.

### 🧪 Testes automatizados

Os testes verificam a prioridade dos chamados, mapas sem rota, colisões na tabela hash e o cancelamento de despachos. Para executá-los:

```bash
python -m unittest discover -v
```

## 💡 Limitações do modelo de rotas

O mapa é simplificado e não atribui pesos às conexões, como distância ou tempo de deslocamento. Por isso, a BFS encontra o trajeto com menos trechos, que não é necessariamente o mais rápido ou o mais curto na cidade real. A simulação também não considera trânsito, limites de velocidade ou disponibilidade de viaturas.

**Autor:** Thiago da Silva Lopes

**Contexto:** Projeto final de Estruturas de Dados e Algoritmos (EDA)
