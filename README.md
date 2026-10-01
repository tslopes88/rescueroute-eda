# 🚑 RescueRoute

### Uma simulação simples de atendimento a chamados de resgate

Este projeto nasceu como meu trabalho final de **Estruturas de Dados e Algoritmos**. A ideia é mostrar, na prática, como algumas estruturas ajudam a organizar chamados e encontrar caminhos entre locais.

Tudo roda no terminal e usa informações inventadas. É um projeto para aprender — **não é um sistema real de emergência**.

## 🧭 Como funciona?

1. Um chamado chega com um local e um nível de gravidade.
2. O sistema coloca os mais urgentes na frente. Se dois têm a mesma gravidade, vale quem chegou primeiro.
3. A simulação procura um caminho entre a base e o chamado.
4. Se um despacho for cancelado, o chamado volta para a fila mantendo sua prioridade.

Se ainda não houver caminho até um local, o chamado não se perde: continua aguardando na fila.

## 🧰 As estruturas por trás do projeto

- **Tabela hash** 🔎 — ajuda a encontrar um chamado pelo código.
- **Min-heap** 🚨 — organiza a fila pela gravidade e pela ordem de chegada.
- **Grafo + busca em largura (BFS)** 🗺️ — representa as ligações entre locais e encontra um caminho com menos trechos.
- **Pilha** ↩️ — guarda os despachos mais recentes para permitir o cancelamento do último.

Essas estruturas foram implementadas no próprio projeto para praticar o conteúdo da disciplina. Em resumo, a tabela hash facilita consultas, a heap mantém a prioridade, o grafo representa o mapa e a pilha segue a regra “o último a entrar é o primeiro a sair”.

## ▶️ Quer executar?

Você precisa do **Python 3.10 ou mais recente**. Não é necessário instalar bibliotecas extras.

```bash
python rescueroute.py
```

O nome antigo também continua funcionando:

```bash
python simulador_logistica.py
```

## 🧪 Testes

Para rodar as verificações do projeto:

```bash
python -m unittest discover -v
```

Os testes conferem, por exemplo, a prioridade dos chamados, caminhos disponíveis ou não, colisões na tabela hash e o cancelamento do último despacho.

## 💡 Um detalhe importante sobre as rotas

A demonstração usa um mapa pequeno, com trechos sem distância ou tempo definidos. Por isso, a BFS encontra o caminho com **menos ligações**, não necessariamente o mais rápido ou curto na vida real. O mapa também não representa trânsito, equipes disponíveis ou situações reais de emergência.

## 👨‍🎓 Sobre o trabalho

Projeto final de **Estruturas de Dados e Algoritmos (EDA)**, desenvolvido por **Thiago da Silva Lopes**.

📚 Consulte também a documentação oficial do Python sobre [heap](https://docs.python.org/3/library/heapq.html), [filas](https://docs.python.org/3/library/collections.html#collections.deque) e [testes](https://docs.python.org/3/library/unittest.html).
