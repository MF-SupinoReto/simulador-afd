# Simulador de Autômato Finito Determinístico (AFD)

Trabalho de Computabilidade — Grupo 6.

Programa de terminal em Python que lê um AFD de um arquivo JSON, recebe uma
sequência de símbolos, mostra cada transição percorrida e informa se a
sequência foi **aceita** ou **rejeitada**.

| Integrante | Responsabilidade | Arquivo |
|---|---|---|
| Enzo | Interface e integração | `main.py` |
| Kauê | Motor de simulação | `automato.py` |
| Yruan | Leitura e validação do JSON | `leitor.py`, `exemplos/` |
| Matheus | Testes e documentação | `test_automato.py`, `README.md` |

## Requisitos

- Python **3.9 ou mais novo** (testado no 3.11). Não precisa instalar nenhuma biblioteca.

Para conferir a versão:

```
python --version
```

## Como executar

Abra o terminal **na pasta do projeto** e rode:

```
python main.py
```

O menu aparece:

```
==============================================
       SIMULADOR DE AFD — GRUPO 6
==============================================
1 - Carregar autômato (arquivo JSON)
2 - Testar uma sequência
3 - Ver autômato carregado
0 - Sair
==============================================
```

1. Escolha **1** e informe o arquivo, por exemplo `exemplos/termina_em_1.json`
   (caminhos relativos partem da pasta do projeto; caminhos absolutos também funcionam).
2. Escolha **2** e digite a sequência, por exemplo `101`.
   Para testar a **sequência vazia**, só aperte Enter.
3. Repita a opção 2 quantas vezes quiser. Use **0** (ou Ctrl+C) para sair.

### Exemplo de execução

```
Escolha uma opção: 2
Sequência: 101

--- PASSO A PASSO ---
Estado inicial: q0
1. Lendo '1': q0 -> q1
2. Lendo '0': q1 -> q0
3. Lendo '1': q0 -> q1

Resultado: ACEITA (terminou em q1)
```

| Entrada (`termina_em_1.json`) | Resultado |
|---|---|
| `101` | Resultado: ACEITA (terminou em q1) |
| `100` | Resultado: REJEITA (terminou em q0) |
| `102` | Erro: símbolo inválido `'2'` na posição 3: não pertence ao alfabeto |
| *(vazia)* | Resultado: REJEITA (terminou em q0, que não é final) |

Erros não fecham o programa: a mensagem aparece e o menu volta.

### Conferir só um arquivo JSON

```
python leitor.py exemplos/termina_em_1.json exemplos/invalidos/varios_erros.json
```

Mostra `[VÁLIDO]` ou `[INVÁLIDO]` com o motivo de cada arquivo.

## Formato do arquivo JSON

```json
{
    "nome": "Termina em 1",
    "descricao": "Aceita apenas sequências binárias terminadas em 1.",
    "estados": ["q0", "q1"],
    "alfabeto": ["0", "1"],
    "estado_inicial": "q0",
    "estados_finais": ["q1"],
    "transicoes": {
        "q0": {"0": "q0", "1": "q1"},
        "q1": {"0": "q0", "1": "q1"}
    }
}
```

| Campo | Obrigatório | Regra |
|---|---|---|
| `nome`, `descricao` | não | texto |
| `estados` | sim | lista não vazia de nomes, sem repetição |
| `alfabeto` | sim | lista não vazia de símbolos de **1 caractere**, sem espaços nem repetição |
| `estado_inicial` | sim | um dos `estados` |
| `estados_finais` | sim | lista (pode ser vazia) de `estados` |
| `transicoes` | sim | para **cada** estado, **exatamente um** destino para **cada** símbolo |

Isto é a definição formal M = (Q, Σ, δ, q₀, F): `estados` = Q, `alfabeto` = Σ,
`transicoes` = δ, `estado_inicial` = q₀, `estados_finais` = F.

Salve o arquivo em **UTF-8**. Todos os números e símbolos vão **entre aspas**
(`"0"`, e não `0`).

### Exemplos incluídos

| Arquivo | Linguagem aceita |
|---|---|
| `exemplos/termina_em_1.json` | binários terminados em 1 |
| `exemplos/zeros_pares.json` | binários com quantidade par de zeros (aceita a vazia) |
| `exemplos/contem_ab.json` | sequências sobre {a, b} que contêm `ab` |
| `exemplos/invalidos/*.json` | 10 arquivos com erros, um tipo de erro em cada (e um com vários) |

### Erros detectados ao carregar

JSON malformado (com linha e coluna), arquivo vazio, inexistente ou que não
está em UTF-8, campo faltando ou com nome errado, tipos errados, estados ou
símbolos repetidos, estado inicial/final inexistente, transição faltando,
transição duplicada, símbolo fora do alfabeto, destino inexistente e
transição com mais de um destino (não determinística). Quando há vários
problemas, todos são listados de uma vez.

## Testes automáticos

Na pasta do projeto:

```
python -m unittest          # resumo
python -m unittest -v       # nome de cada teste
```

São 84 testes em `test_automato.py`, divididos em:

| Grupo | O que cobre |
|---|---|
| `TestMotor` | aceitação, rejeição, sentença vazia, símbolo inválido em qualquer posição, histórico encadeado, estado sumidouro, nomes com acento, alfabeto Unicode, sequência de 100 mil símbolos |
| `TestOraculo` | compara os 3 AFDs de exemplo com a definição da linguagem em **todas** as sequências de até 10 símbolos (2047 por AFD binário) |
| `TestLeitor` | cada regra de validação, JSON malformado, arquivo vazio, não UTF-8, chave duplicada |
| `TestExemplos` | todos os arquivos de `exemplos/` e `exemplos/invalidos/` |
| `TestIntegracao` | leitor + motor juntos |
| `TestInterface` | `main.py` com entradas simuladas: fluxo completo, erros sem encerrar, Ctrl+C, fim da entrada |
| `TestPendencias` | falhas encontradas pelos testes e já corrigidas: JSON com BOM e caminho entre aspas (ver `RELATORIO_TESTES.md`) |

## Estrutura do projeto

```
main.py               interface de terminal (menu)
leitor.py             carregar_afd(caminho) -> dict  |  validar_afd(dados) -> dict
automato.py           simular_afd(afd, sequencia) -> (aceita, historico)
test_automato.py      testes automáticos (unittest)
exemplos/             AFDs válidos
exemplos/invalidos/   AFDs com erros, para demonstração e testes
RELATORIO_TESTES.md   falhas encontradas nos testes
ROTEIRO_APRESENTACAO.md  roteiro da apresentação e dos slides
```

Fluxo: `main.py` pede o arquivo → `leitor.carregar_afd` valida e devolve o AFD
→ `main.py` pede a sequência → `automato.simular_afd` devolve
`(aceita, [(origem, símbolo, destino), ...])` → `main.py` mostra o passo a
passo e o resultado.
