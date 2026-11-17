# Roteiro da apresentação — Grupo 6

**Simulador de Autômato Finito Determinístico (AFD) em Python**

Duração planejada: **cerca de 13 min** + perguntas. O mínimo é 10 min,
então há folga de 3 min se algo atrasar.

| Bloco | Quem | Slides | Tempo |
|---|---|---|---|
| Abertura e objetivo | Enzo | 1–3 | 2 min |
| Lógica do AFD | Kauê | 4–6 | 3 min |
| JSON e validação | Yruan | 7–8 | 2 min 30 |
| Demonstração ao vivo | Enzo (digita) + todos | 9 | 3 min |
| Testes, documentação e conclusão | Matheus | 10–13 | 2 min 40 |
| **Total** | | **13 slides** | **≈ 13 min** |

---

## Orientações para montar os slides

- **Uma ideia por slide**, no máximo 5 linhas de texto. O detalhe vai na fala, não no slide.
- **Código e terminal em fonte monoespaçada** (Consolas, JetBrains Mono), fundo escuro, letra grande (≥ 20 pt).
- **Cores fixas por integrante**, iguais às do guia: Enzo azul, Kauê verde-azulado, Yruan roxo, Matheus laranja.
  Coloque a cor de quem fala numa faixa no canto do slide.
- **Diagrama do AFD** (slide 4): desenhe uma vez e reutilize. Ferramentas grátis:
  [draw.io](https://app.diagrams.net) ou [FSM Simulator](https://ivanzuzak.info/noam/webapps/fsm_simulator/).
  Estado final = círculo duplo; estado inicial = seta entrando.
- **Prints do terminal**: tire da execução real (o README tem a saída), não redigite.
- Slide de **título e de conclusão** com o nome dos quatro.

---

## Slide a slide

### Slide 1 — Título · Enzo · 20 s

**No slide:** "Simulador de Autômato Finito Determinístico em Python", Grupo 6,
nomes dos 4 integrantes, disciplina e data.

**Fala:** "Boa noite. Nós somos o Grupo 6 e vamos apresentar um simulador de
AFD feito em Python, que roda no terminal."

### Slide 2 — O problema · Enzo · 50 s

**No slide:**
- Um AFD é uma "máquina de regras" que lê uma sequência símbolo por símbolo
- No fim, ela diz: **aceita** ou **rejeita**
- Nosso objetivo: configurar o AFD por arquivo e ver o caminho passo a passo

**Visual:** três cartões como no guia: `101 → ACEITA`, `100 → REJEITA`, `102 → ERRO`.

**Fala:** "Um autômato finito determinístico é um modelo de computação com
memória finita: ele só sabe em qual estado está. A cada símbolo lido, ele
segue exatamente uma regra e muda de estado. Quando a entrada acaba, se ele
parou num estado final, a sequência é aceita. Nosso programa recebe essas
regras num arquivo JSON, então dá para testar qualquer AFD sem mudar o código."

### Slide 3 — Como o programa é dividido · Enzo · 50 s

**No slide:** o fluxo do guia em 4 caixas:
`main.py (entrada) → leitor.py (carrega e valida) → automato.py (simula) → main.py (mostra)`,
com o nome do responsável embaixo de cada uma.

**Fala:** "Dividimos o programa em módulos, um por integrante. O `main.py`
é o menu: pede o arquivo e a sequência. Ele chama o leitor do Yruan, que
abre e confere o JSON, e o motor do Kauê, que faz a simulação. No fim o
`main.py` mostra o resultado. Antes de programar, combinamos o formato do
JSON e o que cada função recebe e devolve, por isso as partes se encaixaram
sem reescrever nada. E erro nenhum fecha o programa: a mensagem aparece e o
menu volta."

### Slide 4 — Definição formal · Kauê · 1 min

**No slide:**
- M = (Q, Σ, δ, q₀, F)
- Diagrama do AFD "termina em 1": q0 (inicial) e q1 (final, círculo duplo);
  q0 –0→ q0, q0 –1→ q1, q1 –1→ q1, q1 –0→ q0
- Tabela de transição δ ao lado

| δ | 0 | 1 |
|---|---|---|
| →q0 | q0 | q1 |
| *q1 | q0 | q1 |

**Fala:** "Formalmente, um AFD é uma quíntupla: Q são os estados, Σ é o
alfabeto, δ é a função de transição, q₀ é o estado inicial e F são os
estados finais. Determinístico quer dizer que, para cada estado e cada
símbolo, existe exatamente um próximo estado. Nunca zero, nunca dois. No
nosso exemplo, q1 significa 'o último símbolo lido foi 1'."

### Slide 5 — O algoritmo · Kauê · 1 min

**No slide:** pseudocódigo curto

```
estado = inicial
para cada símbolo da sequência:
    se símbolo não está no alfabeto: ERRO
    próximo = δ(estado, símbolo)
    guardar (estado, símbolo, próximo) no histórico
    estado = próximo
aceita = estado está em F
```

**Fala:** "A função `simular_afd` recebe o autômato e a sequência e devolve
duas coisas: se aceitou, e o histórico de transições. Cada passo do
histórico é uma tupla com origem, símbolo e destino: é isso que permite
mostrar o caminho na tela. O algoritmo lê cada símbolo uma vez, então o
tempo é proporcional ao tamanho da entrada, O(n)."

### Slide 6 — Casos especiais · Kauê · 1 min

**No slide:**
- **Sequência vazia (ε):** nenhuma transição; aceita se o inicial for final
- **Símbolo fora do alfabeto:** erro com o símbolo e a **posição**, sem travar
- **Rastreamento** de `101`: q0 → q1 → q0 → q1 ✔

**Fala:** "Dois casos pedem cuidado. Na sequência vazia, o autômato não
anda: a resposta depende só de o estado inicial ser final. No exemplo
'termina em 1' a vazia é rejeitada, e no 'quantidade par de zeros' ela é
aceita, porque zero é par. E se aparece um símbolo que não está no
alfabeto, como o 2 em 102, o motor avisa a interface em vez de inventar uma
transição, e diz a posição: 'símbolo inválido 2 na posição 3'."

### Slide 7 — O arquivo JSON · Yruan · 1 min 15

**No slide:** o JSON de `termina_em_1.json`, com uma seta ligando cada campo
ao símbolo da quíntupla (`estados` → Q, `alfabeto` → Σ, `transicoes` → δ,
`estado_inicial` → q₀, `estados_finais` → F).

**Fala:** "O autômato vem de um arquivo JSON, e cada campo corresponde a uma
parte da definição formal. As transições ficam num dicionário de
dicionários: o estado aponta para os símbolos, e cada símbolo para o
destino. Assim o motor acha o próximo estado direto, com
`transicoes[estado][símbolo]`. Os símbolos têm um caractere só, porque a
sequência é lida caractere por caractere."

### Slide 8 — Validação · Yruan · 1 min 15

**No slide:** lista curta + print do `varios_erros.json`

- JSON malformado → linha e coluna
- Campo faltando ou com nome errado
- Estado inicial/final que não existe
- Transição faltando, duplicada, ou com 2 destinos (não determinística)
- **Todos os erros listados de uma vez**

**Fala:** "Antes de simular, o leitor confere se o arquivo é mesmo um AFD.
O ponto mais importante é a regra 'exatamente uma transição por estado e
símbolo'. Se faltar, o AFD está incompleto; se houver duas, não é
determinístico. Um detalhe: o Python, por padrão, aceita uma chave repetida
no JSON e fica com a última, escondendo o erro. Por isso o leitor detecta
chave duplicada. E, em vez de parar no primeiro problema, ele lista todos,
para corrigir tudo de uma vez."

### Slide 9 — Demonstração ao vivo · Enzo digita, cada um comenta a sua parte · 3 min

**No slide:** só o título "Demonstração" (troque para o terminal).

Siga o **roteiro da demo** na próxima seção.

### Slide 10 — Como testamos · Matheus · 50 s

**No slide:**
- **84 testes automáticos** com `unittest`: `python -m unittest`
- Motor · Leitor · Exemplos · Integração · Interface
- Print do terminal: `Ran 84 tests ... OK`

**Fala:** "Para garantir que tudo funciona junto, criei 84 testes
automáticos com o `unittest`, que já vem com o Python. Eles cobrem os casos
mínimos do guia (101 aceita, 100 rejeita, 102 dá erro, sentença vazia,
JSON quebrado, transição faltando) e também testam o menu do `main.py`,
simulando o que o usuário digita, para conferir que nenhum erro fecha o
programa."

### Slide 11 — Casos difíceis · Matheus · 50 s

**No slide:**
- **Teste exaustivo:** todas as sequências de até 10 símbolos (2047 por AFD)
  comparadas com a definição da linguagem
- Estado "morto", nenhum estado final, todos finais
- Nomes com acento, alfabeto grego (α, β), 100 mil símbolos
- Arquivo vazio, não UTF-8, aspas simples, `"1"` repetido

**Fala:** "Além dos casos comuns, procurei casos difíceis. O principal é um
teste exaustivo: para cada AFD de exemplo, geramos todas as sequências de
até 10 símbolos e comparamos com a definição em Python. Por exemplo, o
'termina em 1' tem que concordar com `sequencia.endswith('1')` nas 2047
sequências. Se discordar em uma, o teste mostra qual foi."

### Slide 12 — O que os testes encontraram · Matheus · 30 s

**No slide:** antes/depois

- JSON salvo "UTF-8 com BOM" (Bloco de Notas/PowerShell) era recusado → corrigido
- Caminho colado com aspas ("Copiar como caminho") não era encontrado → corrigido
- Rodada 1: 81/83 → depois das correções: **84/84**
- Relatório em `RELATORIO_TESTES.md`

**Fala:** "Os testes encontraram dois problemas reais, os dois comuns no
Windows. Eu registrei no relatório com a correção sugerida, cada autor
corrigiu a sua parte, e rodamos os testes de novo até passar tudo."

### Slide 13 — Conclusão · Matheus · 30 s

**No slide:**
- AFD configurável por arquivo ✔ · passo a passo ✔ · aceita/rejeita ✔ · erros tratados ✔ · manual ✔
- Possíveis extensões: AFN, minimização de AFD, desenho do autômato
- "Obrigado! Perguntas?" + nomes do grupo

**Fala:** "Atendemos todos os requisitos da proposta: autômato configurado
por arquivo, processamento passo a passo, aceitação e rejeição, tratamento
de erros e manual de uso no README. Como próximos passos, daria para
simular autômatos não determinísticos ou minimizar o AFD. Obrigado, e
ficamos à disposição para perguntas."

---

## Roteiro da demonstração (slide 9, ~3 min)

Abra o terminal **na pasta do projeto antes de começar** e deixe a fonte grande (Ctrl + `+`).

| # | Digitar | O que aparece | Quem comenta |
|---|---|---|---|
| 1 | `python main.py` | Menu | Enzo: "Esse é o menu." |
| 2 | `1` → `exemplos/termina_em_1.json` | Resumo do AFD + "carregado com sucesso" | Yruan: "O leitor validou o arquivo." |
| 3 | `2` → `101` | Passo a passo q0→q1→q0→q1, `Resultado: ACEITA (terminou em q1)` | Kauê explica o caminho |
| 4 | `2` → `100` | `Resultado: REJEITA (terminou em q0)` | Kauê |
| 5 | `2` → `102` | `símbolo inválido '2' na posição 3`; o menu volta | Enzo: "Não travou." Kauê: "E ele diz onde está o erro." |
| 6 | `1` → `exemplos/zeros_pares.json`, depois `2` → *Enter* | Sequência vazia: `Resultado: ACEITA (terminou em par)` | Kauê: "Zero zeros é par." |
| 7 | `1` → `exemplos/invalidos/varios_erros.json` | Lista de 5 problemas | Yruan |
| 8 | `0` | Encerra | — |
| 9 | `python -m unittest` | `Ran 84 tests ... OK` | Matheus (liga com o slide 10) |

Isso cobre o que o guia exige: **uma aceita, uma rejeitada e um caso inválido** (aqui são três).

**Plano B:** se o computador falhar, tenha prints de cada passo acima nos
slides ocultos, logo depois do slide 9.

---

## Perguntas prováveis

| Pergunta | Quem responde | Resposta curta |
|---|---|---|
| Por que AFD e não AFN? | Kauê | No AFD cada passo tem um único próximo estado, então a simulação é direta e O(n). Todo AFN pode ser convertido em AFD (construção de subconjuntos). |
| O que acontece com uma transição faltando? | Yruan | O leitor recusa o arquivo antes de simular. O motor também confere, por segurança. |
| E se o alfabeto tiver símbolos de 2 caracteres, tipo "10"? | Yruan | Não é permitido: a sequência é lida caractere por caractere, e "10" ficaria ambíguo. |
| Como vocês sabem que está certo? | Matheus | 84 testes automáticos, incluindo o teste exaustivo com todas as sequências até 10 símbolos. |
| Qual a complexidade? | Kauê | O(n) no tamanho da sequência; cada símbolo é uma consulta num dicionário. |
| Dá para usar outro AFD? | Enzo | Sim: basta criar outro JSON no mesmo formato e carregar pela opção 1. |

---

## Checklist do ensaio

- [x] Correções P1 e P2 do relatório feitas e `python -m unittest` dando **OK**
- [ ] Python ≥ 3.9 no computador da apresentação (`python --version`)
- [ ] Ensaio completo cronometrado: entre 11 e 14 min
- [ ] Cada um sabe a sua fala e quem passa a vez para quem
- [ ] Prints de reserva da demo nos slides ocultos
- [ ] Terminal aberto na pasta certa e com a fonte grande
