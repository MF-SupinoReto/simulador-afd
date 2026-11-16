"""Leitura e validação do arquivo JSON do AFD — Grupo 6 (responsável: Yruan).

Contrato com os outros módulos:
    carregar_afd(caminho: str) -> dict
        Abre o arquivo, valida tudo e devolve o AFD pronto para uso.
    validar_afd(dados: dict) -> dict
        Valida um AFD que já está em memória (útil nos testes).

Em caso de problema, as duas funções lançam ErroAFD, que é uma subclasse de
ValueError. Assim o main.py (que já captura ValueError) mostra a mensagem sem
encerrar o programa.

Formato combinado do JSON
-------------------------
{
    "nome": "Termina em 1",                (opcional)
    "descricao": "Aceita binários ...",    (opcional)
    "estados": ["q0", "q1"],
    "alfabeto": ["0", "1"],
    "estado_inicial": "q0",
    "estados_finais": ["q1"],
    "transicoes": {
        "q0": {"0": "q0", "1": "q1"},
        "q1": {"0": "q0", "1": "q1"}
    }
}

Regras verificadas:
    - O arquivo existe, está em UTF-8 e é um JSON bem formado.
    - Todos os campos obrigatórios existem e não há campos desconhecidos.
    - "estados": lista não vazia de nomes (texto), sem repetição.
    - "alfabeto": lista não vazia de símbolos com exatamente 1 caractere
      (a sequência é lida caractere por caractere), sem repetição.
    - "estado_inicial": um dos estados declarados.
    - "estados_finais": lista (pode ser vazia) de estados declarados, sem repetição.
    - "transicoes": cada estado possui exatamente uma transição para cada
      símbolo do alfabeto, e todo destino é um estado declarado.

Para acessar uma transição no motor (automato.py):
    proximo = afd["transicoes"][estado_atual][simbolo]
"""

import json
import sys
from pathlib import Path


CAMPOS_OBRIGATORIOS = ("estados", "alfabeto", "estado_inicial", "estados_finais", "transicoes")
CAMPOS_OPCIONAIS = ("nome", "descricao")


class ErroAFD(ValueError):
    """Erro de leitura ou de configuração do AFD, com mensagem amigável."""


# --------------------------------------------------------------------------
# Leitura do arquivo
# --------------------------------------------------------------------------

def _rejeitar_chaves_duplicadas(pares):
    """Usado pelo json.load para detectar chaves repetidas.

    Por padrão o Python fica silenciosamente com a última chave repetida, o
    que esconderia uma transição duplicada como {"0": "q0", "0": "q1"}.
    """
    objeto = {}
    for chave, valor in pares:
        if chave in objeto:
            raise ErroAFD(
                f"a chave {chave!r} aparece mais de uma vez no mesmo bloco do JSON "
                "(cada estado deve ter exatamente uma transição por símbolo)"
            )
        objeto[chave] = valor
    return objeto


def carregar_afd(caminho):
    """Abre o arquivo JSON, valida o autômato e devolve o dicionário do AFD."""
    arquivo = Path(caminho)

    try:
        with arquivo.open(encoding="utf-8") as f:
            dados = json.load(f, object_pairs_hook=_rejeitar_chaves_duplicadas)
    except FileNotFoundError:
        raise ErroAFD(f"arquivo não encontrado: {arquivo}") from None
    except IsADirectoryError:
        raise ErroAFD(f"o caminho informado é uma pasta, não um arquivo: {arquivo}") from None
    except PermissionError:
        raise ErroAFD(f"sem permissão para ler o arquivo: {arquivo}") from None
    except UnicodeDecodeError:
        raise ErroAFD(f"o arquivo {arquivo.name} não está em UTF-8") from None
    except json.JSONDecodeError as erro:
        raise ErroAFD(
            f"JSON malformado em {arquivo.name} (linha {erro.lineno}, "
            f"coluna {erro.colno}): {_traduzir_erro_json(erro.msg)}"
        ) from None
    except OSError as erro:
        raise ErroAFD(f"não foi possível ler {arquivo}: {erro.strerror or erro}") from None

    return validar_afd(dados)


def _traduzir_erro_json(mensagem):
    """Traduz as mensagens mais comuns do módulo json."""
    traducoes = {
        "Expecting value": "valor esperado (talvez falte algo ou sobre uma vírgula)",
        "Expecting ',' delimiter": "falta uma vírgula entre os itens",
        "Expecting ':' delimiter": "falta ':' entre a chave e o valor",
        "Expecting property name enclosed in double quotes":
            "nome de campo esperado entre aspas duplas (talvez sobre uma vírgula no final)",
        "Unterminated string starting at": "texto aberto com aspas e não fechado",
        "Extra data": "há conteúdo depois do fim do JSON",
        "Invalid control character at": "caractere inválido dentro de um texto",
    }
    for original, traducao in traducoes.items():
        if mensagem.startswith(original):
            return traducao
    return mensagem


# --------------------------------------------------------------------------
# Validação
# --------------------------------------------------------------------------

def validar_afd(dados):
    """Confere se o AFD está completo e consistente.

    Junta todos os problemas encontrados e lança um único ErroAFD com a
    lista, para o usuário corrigir tudo de uma vez.
    """
    if not isinstance(dados, dict):
        raise ErroAFD("o JSON deve ser um objeto { ... } com os campos do autômato")

    erros = []

    faltando = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in dados]
    if faltando:
        erros.append("campo(s) obrigatório(s) ausente(s): " + ", ".join(faltando))

    desconhecidos = [
        campo for campo in dados
        if campo not in CAMPOS_OBRIGATORIOS and campo not in CAMPOS_OPCIONAIS
    ]
    if desconhecidos:
        erros.append(
            "campo(s) desconhecido(s): " + ", ".join(map(repr, desconhecidos))
            + " (confira a grafia; os aceitos são: "
            + ", ".join(CAMPOS_OBRIGATORIOS + CAMPOS_OPCIONAIS) + ")"
        )

    estados = _validar_estados(dados.get("estados"), erros) if "estados" in dados else None
    alfabeto = _validar_alfabeto(dados.get("alfabeto"), erros) if "alfabeto" in dados else None

    if "estado_inicial" in dados:
        _validar_estado_inicial(dados["estado_inicial"], estados, erros)
    if "estados_finais" in dados:
        _validar_estados_finais(dados["estados_finais"], estados, erros)
    if "transicoes" in dados:
        _validar_transicoes(dados["transicoes"], estados, alfabeto, erros)

    for campo in CAMPOS_OPCIONAIS:
        if campo in dados and not isinstance(dados[campo], str):
            erros.append(f'"{campo}" deve ser um texto')

    if erros:
        if len(erros) == 1:
            raise ErroAFD("autômato inválido: " + erros[0])
        lista = "\n".join(f"  - {erro}" for erro in erros)
        raise ErroAFD(f"autômato inválido ({len(erros)} problemas):\n{lista}")

    afd = {
        "estados": list(dados["estados"]),
        "alfabeto": list(dados["alfabeto"]),
        "estado_inicial": dados["estado_inicial"],
        "estados_finais": list(dados["estados_finais"]),
        "transicoes": {
            estado: dict(dados["transicoes"][estado]) for estado in dados["estados"]
        },
    }
    for campo in CAMPOS_OPCIONAIS:
        if campo in dados:
            afd[campo] = dados[campo]
    return afd


def _repetidos(itens):
    vistos, repetidos = set(), []
    for item in itens:
        if item in vistos and item not in repetidos:
            repetidos.append(item)
        vistos.add(item)
    return repetidos


def _lista_de_textos(valor, campo, erros, pode_ser_vazia=False):
    """Confere se o valor é uma lista de textos. Devolve a lista ou None."""
    if not isinstance(valor, list):
        erros.append(f'"{campo}" deve ser uma lista, por exemplo ["a", "b"]')
        return None
    if not valor and not pode_ser_vazia:
        erros.append(f'"{campo}" não pode ser uma lista vazia')
        return None
    nao_textos = [item for item in valor if not isinstance(item, str)]
    if nao_textos:
        erros.append(
            f'"{campo}" deve conter apenas textos entre aspas; inválido(s): '
            + ", ".join(map(repr, nao_textos))
        )
        return None
    repetidos = _repetidos(valor)
    if repetidos:
        erros.append(f'"{campo}" tem item(ns) repetido(s): ' + ", ".join(map(repr, repetidos)))
    return valor


def _validar_estados(valor, erros):
    estados = _lista_de_textos(valor, "estados", erros)
    if estados is None:
        return None
    vazios = [e for e in estados if not e.strip()]
    if vazios:
        erros.append('"estados" não pode ter nomes vazios')
    return set(estados)


def _validar_alfabeto(valor, erros):
    alfabeto = _lista_de_textos(valor, "alfabeto", erros)
    if alfabeto is None:
        return None
    tamanho_errado = [s for s in alfabeto if len(s) != 1]
    if tamanho_errado:
        erros.append(
            '"alfabeto" deve ter símbolos de exatamente 1 caractere; inválido(s): '
            + ", ".join(map(repr, tamanho_errado))
        )
    espacos = [s for s in alfabeto if len(s) == 1 and s.isspace()]
    if espacos:
        erros.append('"alfabeto" não pode conter espaços ou quebras de linha como símbolo')
    # Só os símbolos válidos seguem para a checagem das transições, para não
    # repetir o mesmo problema em cada estado.
    return {s for s in alfabeto if len(s) == 1 and not s.isspace()}


def _validar_estado_inicial(valor, estados, erros):
    if not isinstance(valor, str):
        erros.append('"estado_inicial" deve ser o nome de um estado, entre aspas (ex.: "q0")')
    elif estados is not None and valor not in estados:
        erros.append(f'"estado_inicial" {valor!r} não está na lista de "estados"')


def _validar_estados_finais(valor, estados, erros):
    finais = _lista_de_textos(valor, "estados_finais", erros, pode_ser_vazia=True)
    if finais is None or estados is None:
        return
    inexistentes = [e for e in finais if e not in estados]
    if inexistentes:
        erros.append(
            '"estados_finais" contém estado(s) que não está(ão) em "estados": '
            + ", ".join(map(repr, inexistentes))
        )


def _validar_transicoes(valor, estados, alfabeto, erros):
    if not isinstance(valor, dict):
        erros.append(
            '"transicoes" deve ser um objeto no formato '
            '{"estado": {"simbolo": "destino", ...}, ...}'
        )
        return
    if estados is None or alfabeto is None:
        # Sem estados/alfabeto válidos não há como conferir as transições.
        return

    for origem in valor:
        if origem not in estados:
            erros.append(f'"transicoes" usa o estado {origem!r}, que não está em "estados"')

    for origem in sorted(estados):
        if origem not in valor:
            erros.append(f"o estado {origem!r} não tem transições definidas")
            continue

        regras = valor[origem]
        if not isinstance(regras, dict):
            erros.append(
                f"as transições de {origem!r} devem ser um objeto "
                '{"simbolo": "destino"}'
            )
            continue

        faltando = [s for s in sorted(alfabeto) if s not in regras]
        if faltando:
            erros.append(
                f"o estado {origem!r} não tem transição para o(s) símbolo(s): "
                + ", ".join(map(repr, faltando))
            )

        for simbolo, destino in regras.items():
            if simbolo not in alfabeto:
                erros.append(
                    f"transição de {origem!r} usa o símbolo {simbolo!r}, "
                    'que não está no "alfabeto"'
                )
            if not isinstance(destino, str):
                erros.append(
                    f"a transição ({origem!r}, {simbolo!r}) deve apontar para um único "
                    f"estado entre aspas, mas recebeu {destino!r}"
                    + (" (um AFD não pode ter mais de um destino)" if isinstance(destino, list) else "")
                )
            elif destino not in estados:
                erros.append(
                    f"a transição ({origem!r}, {simbolo!r}) vai para {destino!r}, "
                    'que não está em "estados"'
                )


# --------------------------------------------------------------------------
# Execução direta: python leitor.py exemplos/termina_em_1.json
# --------------------------------------------------------------------------

def _main(argumentos):
    if not argumentos:
        print("Uso: python leitor.py <arquivo.json> [outro.json ...]")
        return 2

    codigo = 0
    for caminho in argumentos:
        try:
            afd = carregar_afd(caminho)
        except ErroAFD as erro:
            print(f"[INVÁLIDO] {caminho}\n  {erro}\n")
            codigo = 1
        else:
            print(f"[VÁLIDO]   {caminho}")
            print(f"  {len(afd['estados'])} estado(s), alfabeto {afd['alfabeto']}, "
                  f"inicial {afd['estado_inicial']!r}, finais {afd['estados_finais']}\n")
    return codigo


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
