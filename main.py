"""Interface de terminal do Simulador de AFD — Grupo 6.

Contrato acordado com os outros módulos:
    leitor.py: carregar_afd(caminho: str) -> dict
    automato.py: simular_afd(afd: dict, sequencia: str) -> (bool, list)

Cada item da lista de histórico deve ser uma tupla:
    (estado_origem, simbolo_lido, estado_destino)

A entrada de AFD segue o JSON combinado: estados, alfabeto,
estado_inicial, estados_finais e transicoes.
"""

from pathlib import Path


PASTA_PROJETO = Path(__file__).resolve().parent


def obter_funcoes():
    """Carrega as funções implementadas pelos colegas quando disponíveis."""
    try:
        from leitor import carregar_afd
        from automato import simular_afd
    except ImportError as erro:
        print("\nNão foi possível acessar os módulos do grupo.")
        print("Confira se 'leitor.py' (Yruan) e 'automato.py' (Kauê) estão na mesma pasta de 'main.py'.")
        print(f"Detalhes: {erro}\n")
        return None

    return carregar_afd, simular_afd


def mostrar_menu():
    """Mostra o menu principal do simulador."""
    print("\n" + "=" * 46)
    print("       SIMULADOR DE AFD — GRUPO 6")
    print("=" * 46)
    print("1 - Carregar autômato (arquivo JSON)")
    print("2 - Testar uma sequência")
    print("3 - Ver autômato carregado")
    print("0 - Sair")
    print("=" * 46)


def resolver_caminho(entrada):
    """Aceita caminhos absolutos ou relativos à pasta do projeto."""
    caminho = Path(entrada).expanduser()
    if not caminho.is_absolute():
        caminho = PASTA_PROJETO / caminho
    return caminho


def mostrar_automato(afd, arquivo=None):
    """Apresenta um resumo amigável do autômato carregado."""
    print("\n--- AUTÔMATO CARREGADO ---")
    if arquivo is not None:
        print(f"Arquivo: {arquivo.name}")
    print("Estados:", ", ".join(map(str, afd["estados"])))
    print("Alfabeto:", ", ".join(map(str, afd["alfabeto"])))
    print("Estado inicial:", afd["estado_inicial"])
    print("Estados finais:", ", ".join(map(str, afd["estados_finais"])) or "(nenhum)")


def carregar_interativo(carregar_afd):
    """Solicita o arquivo, chama o leitor do Yruan e informa o resultado."""
    # strip("\"'") remove as aspas do "Copiar como caminho" do Windows.
    entrada = input("\nCaminho do JSON (ex.: exemplos/termina_em_1.json): ").strip().strip("\"'")
    if not entrada:
        print("Informe o caminho de um arquivo JSON.")
        return None, None

    caminho = resolver_caminho(entrada)
    if not caminho.is_file():
        print(f"Arquivo não encontrado: {caminho}")
        return None, None

    try:
        afd = carregar_afd(str(caminho))
        if not isinstance(afd, dict):
            raise ValueError("o leitor deve retornar um dicionário com o AFD")
        mostrar_automato(afd, caminho)
        print("Autômato carregado com sucesso!")
        return afd, caminho
    except (OSError, ValueError, KeyError, TypeError) as erro:
        print(f"Não foi possível carregar o autômato: {erro}")
        return None, None


def mostrar_historico(afd, historico):
    """Exibe as transições que o motor do Kauê retornou."""
    print("\n--- PASSO A PASSO ---")
    print("Estado inicial:", afd["estado_inicial"])

    if not historico:
        print("Nenhuma transição: a sequência é vazia.")
        return afd["estado_inicial"]

    estado_final = None
    for numero, passo in enumerate(historico, start=1):
        if not isinstance(passo, (tuple, list)) or len(passo) != 3:
            raise ValueError(
                "histórico inválido: cada passo precisa conter "
                "(estado_origem, simbolo, estado_destino)"
            )
        origem, simbolo, destino = passo
        print(f"{numero}. Lendo {simbolo!r}: {origem} -> {destino}")
        estado_final = destino

    return estado_final


def testar_sequencia(afd, simular_afd):
    """Solicita uma sequência e mostra o processamento e o resultado."""
    print("\nDigite uma sequência usando os símbolos do alfabeto.")
    print("Para testar a sequência vazia, apenas pressione Enter.")
    sequencia = input("Sequência: ")

    try:
        saida = simular_afd(afd, sequencia)
        if not isinstance(saida, (tuple, list)) or len(saida) != 2:
            raise ValueError("o motor deve retornar (aceita: bool, historico: list)")
        aceita, historico = saida
        if not isinstance(aceita, bool):
            raise ValueError("o resultado do motor deve ser True ou False")
        if not isinstance(historico, (tuple, list)):
            raise ValueError("o histórico do motor deve ser uma lista de transições")

        estado_final = mostrar_historico(afd, historico)
        decisao = "ACEITA" if aceita else "REJEITA"
        print(f"\nResultado: {decisao} (terminou em {estado_final})")
    except (ValueError, KeyError, TypeError) as erro:
        print(f"Não foi possível simular a sequência: {erro}")


def main():
    """Mantém o programa em funcionamento até o usuário decidir sair."""
    afd = None
    arquivo = None
    funcoes = None

    while True:
        mostrar_menu()
        try:
            opcao = input("Escolha uma opção: ").strip()

            if opcao == "0":
                print("Encerrando o simulador. Até mais!")
                break

            if opcao == "1":
                if funcoes is None:
                    funcoes = obter_funcoes()
                if funcoes is None:
                    continue
                novo_afd, novo_arquivo = carregar_interativo(funcoes[0])
                if novo_afd is not None:
                    afd, arquivo = novo_afd, novo_arquivo

            elif opcao == "2":
                if afd is None:
                    print("Carregue um autômato antes de testar uma sequência (opção 1).")
                    continue
                testar_sequencia(afd, funcoes[1])

            elif opcao == "3":
                if afd is None:
                    print("Nenhum autômato carregado. Use a opção 1 primeiro.")
                else:
                    mostrar_automato(afd, arquivo)

            else:
                print("Opção inválida. Escolha 0, 1, 2 ou 3.")

        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando o simulador. Até mais!")
            break


if __name__ == "__main__":
    main()
