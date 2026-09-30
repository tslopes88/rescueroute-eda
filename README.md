# RescueRoute

### Projeto final de Estruturas de Dados e Algoritmos

O RescueRoute é uma simulação em Python de uma central que recebe chamados de resgate, organiza o atendimento por gravidade e calcula um caminho pela malha viária cadastrada.

Desenvolvi este projeto para colocar em prática algumas estruturas estudadas na disciplina e mostrar como elas podem trabalhar juntas em um mesmo problema. A demonstração é executada pelo terminal e usa dados fictícios.

> **Importante:** este é um projeto acadêmico. Ele não é um sistema operacional de emergência e não deve ser usado para orientar atendimentos reais.

## O que a simulação demonstra

- Cadastro de chamados com código, local, gravidade e descrição.
- Consulta de um chamado pelo código de triagem.
- Atendimento por prioridade: gravidade 1 é atendida antes de gravidades 2 e 3.
- Desempate por ordem de chegada quando os chamados têm a mesma gravidade.
- Busca de uma rota entre a base e o local do chamado.
- Cancelamento do último despacho e retorno do chamado à fila, sem perder sua ordem original.

## Estruturas utilizadas

| Estrutura | Como aparece no projeto | Custo principal |
| --- | --- | --- |
| Tabela hash com encadeamento separado | Guarda e consulta os chamados pelo código de triagem. | Busca e inserção são, em média, O(1); no pior caso, O(n). O cálculo do hash percorre a chave, portanto custa O(k), em que *k* é seu tamanho. |
| Min-heap binária | Mantém o chamado mais urgente pronto para ser atendido. | Inserção e remoção da raiz: O(log n). |
| Grafo com lista de adjacência | Representa as ligações entre os locais cadastrados. | Armazenamento: O(V + E); a busca em largura (BFS) percorre o grafo em O(V + E). |
| Pilha encadeada | Registra despachos e permite desfazer o mais recente. | Inserção e remoção do topo: O(1). |

Na heap, o número menor representa maior urgência. A ordem de chegada é usada como segundo critério, para que chamados de mesma gravidade mantenham a sequência em que foram recebidos. A BFS encontra o caminho com menos trechos no grafo; como as vias não têm pesos, ela não calcula distância real nem tempo de viagem.

## Como executar

É necessário ter Python 3.10 ou superior. O projeto usa apenas recursos da biblioteca padrão do Python, sem dependências externas.

```bash
python --version
python rescueroute.py
```

O arquivo `simulador_logistica.py` também executa a demonstração. No estado atual, os dois arquivos contêm a mesma implementação; `rescueroute.py` é o nome recomendado para iniciar.

## Cenário da demonstração

A simulação cadastra seis locais conectados por vias e recebe quatro chamados. Um chamado de gravidade 1 é inserido por último para demonstrar que a heap o prioriza. Em seguida, o programa despacha atendimentos, cancela o despacho mais recente e mostra o chamado retornando à fila com sua ordem de chegada preservada.

Ao final, o terminal exibe verificações da prioridade da heap e da reintegração do chamado cancelado.

## Escopo e limitações

O mapa é pequeno e fixo, e todos os trechos têm o mesmo peso. Por isso, a BFS atende ao objetivo didático de encontrar o caminho com menos arestas. O programa não considera trânsito, distância, disponibilidade de equipes, persistência dos dados nem regras clínicas reais.

## Autor

**Thiago da Silva Lopes**
Projeto final da disciplina **Estruturas de Dados e Algoritmos (EDA)**.
