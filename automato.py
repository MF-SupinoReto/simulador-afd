"""Motor de simulação de um Autômato Finito Determinístico (AFD).

Contrato com main.py:
    simular_afd(afd: dict, sequencia: str) -> (bool, list)

Cada item do histórico é uma tupla:
    (estado_origem, simbolo_lido, estado_destino)

Formato esperado para "transicoes":
    {
        "q0": {"0": "q0", "1": "q1"},
        "q1": {"0": "q0", "1": "q1"}
    }
"""

def simular_afd(afd: dict, sequencia: str) -> tuple[bool, list]:
    """Processa a sequência e retorna (aceita, histórico de transições).

    Levanta ValueError quando a sequência contém um símbolo fora do
    alfabeto ou quando falta uma transição necessária.
    """
    if not isinstance(afd, dict):
        raise ValueError("o autômato precisa ser um dicionário")

    campos = ("estados", "alfabeto", "estado_inicial",
              "estados_finais", "transicoes")
    faltando = [campo for campo in campos if campo not in afd]
    if faltando:
        raise ValueError(
            "autômato sem os campos obrigatórios: " + ", ".join(faltando)
        )

    if not isinstance(sequencia, str):
        raise ValueError("a sequência precisa ser um texto")

    estados = afd["estados"]
    alfabeto = afd["alfabeto"]
    estado_inicial = afd["estado_inicial"]
    estados_finais = afd["estados_finais"]
    transicoes = afd["transicoes"]

    if not isinstance(estados, (list, tuple, set)):
        raise ValueError("'estados' precisa ser uma lista de estados")
    if not isinstance(alfabeto, (list, tuple, set)):
        raise ValueError("'alfabeto' precisa ser uma lista de símbolos")
    if not isinstance(estados_finais, (list, tuple, set)):
        raise ValueError("'estados_finais' precisa ser uma lista de estados")
    if not isinstance(transicoes, dict):
        raise ValueError("'transicoes' precisa ser um dicionário")

    if estado_inicial not in estados:
        raise ValueError("o estado inicial não está na lista de estados")

    for estado_final in estados_finais:
        if estado_final not in estados:
            raise ValueError(
                f"o estado final {estado_final!r} não está na lista de estados"
            )

    estado_atual = estado_inicial
    historico = []

    # A sequência vazia não percorre transições: basta verificar
    # se o estado inicial já é um estado final.
    for simbolo in sequencia:
        if simbolo not in alfabeto:
            raise ValueError(
                f"símbolo inválido {simbolo!r}: não pertence ao alfabeto"
            )

        transicoes_estado = transicoes.get(estado_atual)
        if not isinstance(transicoes_estado, dict):
            raise ValueError(
                f"não há transições definidas para o estado {estado_atual!r}"
            )

        if simbolo not in transicoes_estado:
            raise ValueError(
                f"transição ausente: estado {estado_atual!r} "
                f"com símbolo {simbolo!r}"
            )

        proximo_estado = transicoes_estado[simbolo]
        if proximo_estado not in estados:
            raise ValueError(
                f"a transição de {estado_atual!r} com {simbolo!r} "
                f"leva a um estado inexistente: {proximo_estado!r}"
            )

        historico.append((estado_atual, simbolo, proximo_estado))
        estado_atual = proximo_estado

    aceita = estado_atual in estados_finais
    return aceita, historico
