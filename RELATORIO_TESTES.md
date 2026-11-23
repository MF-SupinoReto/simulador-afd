# Relatório de testes — Grupo 6

Responsável: Matheus · `python -m unittest` com Python 3.11.9

| Rodada | Resultado |
|---|---|
| 1 | 83 testes: 81 passam, 2 falham (pendências P1 e P2) |
| 2 | P1 e P2 corrigidas com o ok de Yruan e Enzo: **83 de 83 passam** |
| 3 | Sugestões S1 e S3 aplicadas (+1 teste da posição do erro): **84 de 84 passam** |
| 4 | Exemplos reduzidos a `termina_em_1` e `contem_ab` (saem `zeros_pares` e `invalidos/`; os testes de interface passam a criar JSONs inválidos temporários): **83 de 83 passam** |

## Conferência do que foi pedido no guia

| Requisito do guia | Situação |
|---|---|
| `101` → aceita, `100` → rejeita | OK |
| `102` → erro de símbolo, sem fechar o programa | OK |
| Sentença vazia conforme o estado inicial | OK (`termina_em_1` e `contem_ab` rejeitam, pois o inicial não é final) |
| JSON incompleto / malformado → erro claro | OK (mostra linha e coluna) |
| Transições faltantes → erro claro | OK |
| Exatamente uma transição por símbolo | OK (inclusive chave duplicada no JSON) |
| Histórico de estados exibido corretamente | OK |
| Contrato `carregar_afd` / `simular_afd` / histórico em tuplas | OK, os três módulos combinam |
| Os 3 AFDs de exemplo reconhecem a linguagem descrita | OK, conferido em todas as sequências de até 10 símbolos |

## Pendências encontradas na rodada 1 (corrigidas na rodada 2)

### P1 — Yruan (`leitor.py`): JSON salvo "UTF-8 com BOM" era recusado · ✅ corrigido

- **Como reproduzir:** salvar um AFD válido no Bloco de Notas como "UTF-8 com BOM",
  ou criar com `Out-File`/`Set-Content -Encoding utf8` no PowerShell 5.1.
- **O que acontece:** `JSON malformado ... (linha 1, coluna 1): Unexpected UTF-8 BOM (decode using utf-8-sig)`,
  mensagem em inglês para um arquivo que está correto.
- **Correção sugerida** (linha 82):
  ```python
  with arquivo.open(encoding="utf-8-sig") as f:
  ```
  `utf-8-sig` lê UTF-8 normal e também ignora o BOM se ele existir.
- **Teste:** `TestPendencias.test_P1_leitor_aceita_json_utf8_com_bom`

### P2 — Enzo (`main.py`): caminho entre aspas não era encontrado · ✅ corrigido

- **Como reproduzir:** no Explorador do Windows, clicar com o botão direito no
  JSON → "Copiar como caminho" e colar na opção 1. O caminho vem com aspas.
- **O que acontece:** `Arquivo não encontrado: ...\"C:\...\termina_em_1.json"`.
  Pode acontecer na hora da demonstração.
- **Correção sugerida** (linha 67):
  ```python
  entrada = input("\nCaminho do JSON (ex.: exemplos/termina_em_1.json): ").strip().strip("\"'")
  ```
  Essa linha também troca o exemplo da mensagem: `exemplos/exemplo.json` não existe.
- **Teste:** `TestPendencias.test_P2_interface_aceita_caminho_entre_aspas`

## Sugestões (nenhum teste falha por elas)

| # | Quem | Observação |
|---|---|---|
| S1 | Enzo | ✅ Aplicada: o resultado agora sai como no guia, `Resultado: ACEITA (terminou em q1)` / `Resultado: REJEITA (terminou em q0)`. |
| S2 | Enzo | `mostrar_automato` não mostra `nome` e `descricao` do JSON. Mostrar a descrição ajuda a plateia a entender o que o AFD aceita. |
| S3 | Kauê | ✅ Aplicada: o erro mostra a posição, ex.: `102` → `símbolo inválido '2' na posição 3`. |
| S4 | Yruan | Chave duplicada fora das transições (ex.: `"estados"` duas vezes) gera uma mensagem que fala de "transição por símbolo". Dá para citar só a chave repetida. |
| S5 | Todos | `automato.py` usa `tuple[bool, list]`, que exige Python 3.9+. Já está no README; confiram a versão no computador da apresentação. |

## Como repetir os testes

```
python -m unittest -v
```

Os testes de `TestPendencias` continuam na suíte para garantir que P1 e P2
não voltem.
