"""Testes automáticos do Simulador de AFD — Grupo 6 (responsável: Matheus).

Executar na pasta do projeto:
    python -m unittest              (resumo)
    python -m unittest -v           (lista cada teste)

Organização:
    TestMotor           -> automato.simular_afd (Kauê)
    TestOraculo         -> compara o AFD com a definição da linguagem em
                           TODAS as sequências até um tamanho (casos difíceis)
    TestLeitor          -> leitor.carregar_afd / validar_afd (Yruan)
    TestExemplos        -> arquivos da pasta exemplos/ (válidos e inválidos)
    TestIntegracao      -> leitor + motor juntos, como o main.py usa
    TestInterface       -> main.py simulado com entradas digitadas (Enzo)
    TestPendencias      -> falhas encontradas na rodada 1, já corrigidas;
                           ficam aqui para não voltarem (RELATORIO_TESTES.md)
"""

import copy
import io
import itertools
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import main
from automato import simular_afd
from leitor import ErroAFD, carregar_afd, validar_afd


PASTA = Path(__file__).resolve().parent
EXEMPLOS = PASTA / "exemplos"
INVALIDOS = EXEMPLOS / "invalidos"


def afd_termina_em_1():
    """AFD do guia: aceita binários terminados em 1 (q0 inicial, q1 final)."""
    return {
        "estados": ["q0", "q1"],
        "alfabeto": ["0", "1"],
        "estado_inicial": "q0",
        "estados_finais": ["q1"],
        "transicoes": {
            "q0": {"0": "q0", "1": "q1"},
            "q1": {"0": "q0", "1": "q1"},
        },
    }


class ArquivosTemporarios(unittest.TestCase):
    """Base para testes que precisam criar arquivos JSON de verdade."""

    def setUp(self):
        self.pasta_tmp = Path(tempfile.mkdtemp(prefix="afd_testes_"))

    def tearDown(self):
        shutil.rmtree(self.pasta_tmp, ignore_errors=True)

    def criar(self, nome, conteudo, encoding="utf-8"):
        caminho = self.pasta_tmp / nome
        if isinstance(conteudo, dict):
            conteudo = json.dumps(conteudo, ensure_ascii=False, indent=2)
        caminho.write_text(conteudo, encoding=encoding)
        return caminho


# ==========================================================================
# 1. Motor de simulação (automato.py)
# ==========================================================================

class TestMotor(unittest.TestCase):

    def setUp(self):
        self.afd = afd_termina_em_1()

    # --- casos mínimos do guia -------------------------------------------
    def test_101_aceita(self):
        aceita, _ = simular_afd(self.afd, "101")
        self.assertTrue(aceita)

    def test_100_rejeita(self):
        aceita, _ = simular_afd(self.afd, "100")
        self.assertFalse(aceita)

    def test_102_erro_de_simbolo(self):
        with self.assertRaises(ValueError) as ctx:
            simular_afd(self.afd, "102")
        self.assertIn("'2'", str(ctx.exception))

    def test_historico_do_guia(self):
        _, historico = simular_afd(self.afd, "101")
        self.assertEqual(
            historico,
            [("q0", "1", "q1"), ("q1", "0", "q0"), ("q0", "1", "q1")],
        )

    # --- sentença vazia ---------------------------------------------------
    def test_vazia_rejeita_quando_inicial_nao_e_final(self):
        self.assertEqual(simular_afd(self.afd, ""), (False, []))

    def test_vazia_aceita_quando_inicial_e_final(self):
        self.afd["estados_finais"] = ["q0", "q1"]
        self.assertEqual(simular_afd(self.afd, ""), (True, []))

    # --- símbolos inválidos em posições diferentes -----------------------
    def test_simbolo_invalido_no_inicio_meio_e_fim(self):
        # A mensagem informa a posição do símbolo (contando a partir de 1).
        casos = {"201": 1, "2101": 1, "1021": 3, "1012": 4}
        for sequencia, posicao in casos.items():
            with self.subTest(sequencia=sequencia):
                with self.assertRaises(ValueError) as ctx:
                    simular_afd(self.afd, sequencia)
                self.assertIn(f"'2' na posição {posicao}", str(ctx.exception))

    def test_posicao_aponta_o_primeiro_simbolo_invalido(self):
        with self.assertRaises(ValueError) as ctx:
            simular_afd(self.afd, "1x0y")
        self.assertIn("'x' na posição 2", str(ctx.exception))

    def test_espaco_na_sequencia_e_simbolo_invalido(self):
        with self.assertRaises(ValueError):
            simular_afd(self.afd, "1 0 1")

    def test_letra_parecida_com_digito(self):
        # 'O' maiúsculo e 'l' minúsculo parecem 0 e 1, mas não são.
        for sequencia in ("1O1", "l01"):
            with self.subTest(sequencia=sequencia):
                with self.assertRaises(ValueError):
                    simular_afd(self.afd, sequencia)

    def test_digito_unicode_nao_e_aceito(self):
        # '１' (dígito de largura total) não é o símbolo '1'.
        with self.assertRaises(ValueError):
            simular_afd(self.afd, "1１")

    # --- histórico --------------------------------------------------------
    def test_historico_encadeado_e_do_tamanho_da_sequencia(self):
        sequencia = "1100101110"
        aceita, historico = simular_afd(self.afd, sequencia)
        self.assertEqual(len(historico), len(sequencia))
        self.assertEqual(historico[0][0], self.afd["estado_inicial"])
        for (origem, simbolo, destino), lido in zip(historico, sequencia):
            self.assertEqual(simbolo, lido)
            self.assertEqual(destino, self.afd["transicoes"][origem][simbolo])
        for anterior, proximo in zip(historico, historico[1:]):
            self.assertEqual(anterior[2], proximo[0], "o destino deve ser a próxima origem")
        self.assertEqual(aceita, historico[-1][2] in self.afd["estados_finais"])

    def test_retorno_respeita_contrato(self):
        saida = simular_afd(self.afd, "10")
        self.assertIsInstance(saida, tuple)
        self.assertEqual(len(saida), 2)
        self.assertIsInstance(saida[0], bool)
        self.assertIsInstance(saida[1], list)
        for passo in saida[1]:
            self.assertIsInstance(passo, tuple)
            self.assertEqual(len(passo), 3)

    def test_nao_altera_o_automato(self):
        original = copy.deepcopy(self.afd)
        simular_afd(self.afd, "110101")
        self.assertEqual(self.afd, original)

    def test_chamadas_seguidas_sao_independentes(self):
        self.assertTrue(simular_afd(self.afd, "1")[0])
        self.assertEqual(simular_afd(self.afd, ""), (False, []))

    # --- autômatos diferentes ---------------------------------------------
    def test_sem_estados_finais_sempre_rejeita(self):
        self.afd["estados_finais"] = []
        for sequencia in ("", "1", "0", "111"):
            with self.subTest(sequencia=sequencia):
                self.assertFalse(simular_afd(self.afd, sequencia)[0])

    def test_todos_finais_sempre_aceita(self):
        self.afd["estados_finais"] = ["q0", "q1"]
        for sequencia in ("", "0", "000", "1010"):
            with self.subTest(sequencia=sequencia):
                self.assertTrue(simular_afd(self.afd, sequencia)[0])

    def test_estado_sumidouro(self):
        # Aceita somente sequências que começam com 'a'; ao ler 'b' primeiro
        # o autômato cai em um estado "morto" e nunca mais sai.
        afd = {
            "estados": ["inicio", "ok", "morto"],
            "alfabeto": ["a", "b"],
            "estado_inicial": "inicio",
            "estados_finais": ["ok"],
            "transicoes": {
                "inicio": {"a": "ok", "b": "morto"},
                "ok": {"a": "ok", "b": "ok"},
                "morto": {"a": "morto", "b": "morto"},
            },
        }
        self.assertTrue(simular_afd(afd, "abba")[0])
        aceita, historico = simular_afd(afd, "baaa")
        self.assertFalse(aceita)
        self.assertTrue(all(destino == "morto" for _, _, destino in historico))

    def test_nomes_de_estado_com_acento_e_espaco(self):
        afd = {
            "estados": ["Estado Ímpar", "Estado Par"],
            "alfabeto": ["x"],
            "estado_inicial": "Estado Par",
            "estados_finais": ["Estado Par"],
            "transicoes": {
                "Estado Par": {"x": "Estado Ímpar"},
                "Estado Ímpar": {"x": "Estado Par"},
            },
        }
        self.assertTrue(simular_afd(afd, "xx")[0])
        self.assertFalse(simular_afd(afd, "xxx")[0])

    def test_alfabeto_com_simbolos_unicode(self):
        afd = {
            "estados": ["s"],
            "alfabeto": ["α", "β"],
            "estado_inicial": "s",
            "estados_finais": ["s"],
            "transicoes": {"s": {"α": "s", "β": "s"}},
        }
        self.assertTrue(simular_afd(afd, "αββα")[0])
        with self.assertRaises(ValueError):
            simular_afd(afd, "αa")

    def test_sequencia_longa(self):
        sequencia = "10" * 50_000 + "1"
        aceita, historico = simular_afd(self.afd, sequencia)
        self.assertTrue(aceita)
        self.assertEqual(len(historico), 100_001)

    # --- autômato mal formado entregue direto ao motor --------------------
    def test_motor_recusa_entradas_que_nao_sao_afd(self):
        with self.assertRaises(ValueError):
            simular_afd(["não", "é", "dict"], "1")
        with self.assertRaises(ValueError):
            simular_afd(self.afd, 101)

    def test_motor_recusa_afd_sem_campo(self):
        del self.afd["transicoes"]
        with self.assertRaises(ValueError) as ctx:
            simular_afd(self.afd, "1")
        self.assertIn("transicoes", str(ctx.exception))

    def test_motor_detecta_transicao_ausente(self):
        del self.afd["transicoes"]["q1"]["0"]
        with self.assertRaises(ValueError) as ctx:
            simular_afd(self.afd, "10")
        self.assertIn("ausente", str(ctx.exception))

    def test_motor_detecta_destino_inexistente(self):
        self.afd["transicoes"]["q0"]["1"] = "q9"
        with self.assertRaises(ValueError):
            simular_afd(self.afd, "1")


# ==========================================================================
# 2. Oráculo: compara cada AFD de exemplo com a definição da linguagem
# ==========================================================================

class TestOraculo(unittest.TestCase):
    """Testa exaustivamente todas as sequências até TAMANHO_MAX símbolos.

    Se o AFD e a definição em Python discordarem em qualquer sequência, o
    teste mostra qual foi. Para alfabeto {0,1} e tamanho 10 são 2047 casos.
    """

    TAMANHO_MAX = 10

    CASOS = {
        "termina_em_1.json": lambda s: s.endswith("1"),
        "zeros_pares.json": lambda s: s.count("0") % 2 == 0,
        "contem_ab.json": lambda s: "ab" in s,
    }

    def test_exemplos_reconhecem_a_linguagem_descrita(self):
        for arquivo, linguagem in self.CASOS.items():
            afd = carregar_afd(EXEMPLOS / arquivo)
            for tamanho in range(self.TAMANHO_MAX + 1):
                for simbolos in itertools.product(afd["alfabeto"], repeat=tamanho):
                    sequencia = "".join(simbolos)
                    aceita, _ = simular_afd(afd, sequencia)
                    if aceita != linguagem(sequencia):
                        self.fail(
                            f"{arquivo}: sequência {sequencia!r} deveria ser "
                            f"{'aceita' if linguagem(sequencia) else 'rejeitada'}"
                        )


# ==========================================================================
# 3. Leitor e validação (leitor.py)
# ==========================================================================

class TestLeitor(ArquivosTemporarios):

    def assertInvalido(self, dados, *trechos):
        """Confere que validar_afd recusa os dados e cita cada trecho."""
        with self.assertRaises(ErroAFD) as ctx:
            validar_afd(dados)
        mensagem = str(ctx.exception)
        for trecho in trechos:
            self.assertIn(trecho, mensagem)
        return mensagem

    def test_erroafd_e_valueerror(self):
        # O main.py captura ValueError; isso garante que o erro aparece na tela.
        self.assertTrue(issubclass(ErroAFD, ValueError))

    def test_afd_valido_retorna_dict_completo(self):
        afd = validar_afd(afd_termina_em_1())
        self.assertEqual(afd, afd_termina_em_1())

    def test_retorno_e_copia_independente(self):
        dados = afd_termina_em_1()
        afd = validar_afd(dados)
        afd["transicoes"]["q0"]["1"] = "q0"
        self.assertEqual(dados["transicoes"]["q0"]["1"], "q1")

    def test_campos_opcionais_sao_mantidos(self):
        dados = afd_termina_em_1()
        dados["nome"] = "Termina em 1"
        dados["descricao"] = "teste"
        self.assertEqual(validar_afd(dados)["nome"], "Termina em 1")

    def test_estados_finais_vazio_e_permitido(self):
        dados = afd_termina_em_1()
        dados["estados_finais"] = []
        self.assertEqual(validar_afd(dados)["estados_finais"], [])

    # --- JSON incompleto / estrutura errada --------------------------------
    def test_json_que_nao_e_objeto(self):
        for dados in ([], "texto", 42, None):
            with self.subTest(dados=dados):
                with self.assertRaises(ErroAFD):
                    validar_afd(dados)

    def test_cada_campo_obrigatorio_faltando(self):
        for campo in ("estados", "alfabeto", "estado_inicial", "estados_finais", "transicoes"):
            with self.subTest(campo=campo):
                dados = afd_termina_em_1()
                del dados[campo]
                self.assertInvalido(dados, "ausente", campo)

    def test_campo_com_erro_de_digitacao(self):
        dados = afd_termina_em_1()
        dados["estado_final"] = dados.pop("estados_finais")
        self.assertInvalido(dados, "estado_final", "desconhecido")

    def test_tipos_errados(self):
        casos = {
            "estados": "q0,q1",
            "alfabeto": "01",
            "estado_inicial": ["q0"],
            "estados_finais": "q1",
            "transicoes": [["q0", "0", "q0"]],
        }
        for campo, valor in casos.items():
            with self.subTest(campo=campo):
                dados = afd_termina_em_1()
                dados[campo] = valor
                self.assertInvalido(dados, campo)

    def test_estado_inicial_numero(self):
        dados = afd_termina_em_1()
        dados["estado_inicial"] = 0
        self.assertInvalido(dados, "estado_inicial")

    def test_listas_vazias(self):
        for campo in ("estados", "alfabeto"):
            with self.subTest(campo=campo):
                dados = afd_termina_em_1()
                dados[campo] = []
                self.assertInvalido(dados, campo, "vazia")

    # --- estados ----------------------------------------------------------
    def test_estado_repetido(self):
        dados = afd_termina_em_1()
        dados["estados"] = ["q0", "q1", "q1"]
        self.assertInvalido(dados, "repetido", "q1")

    def test_estado_com_nome_vazio(self):
        dados = afd_termina_em_1()
        dados["estados"].append("  ")
        self.assertInvalido(dados, "vazio")

    def test_estado_inicial_inexistente(self):
        dados = afd_termina_em_1()
        dados["estado_inicial"] = "q9"
        self.assertInvalido(dados, "q9", "estado_inicial")

    def test_estado_final_inexistente(self):
        dados = afd_termina_em_1()
        dados["estados_finais"] = ["q1", "qf"]
        self.assertInvalido(dados, "qf")

    def test_nome_de_estado_diferencia_maiusculas(self):
        dados = afd_termina_em_1()
        dados["estado_inicial"] = "Q0"
        self.assertInvalido(dados, "Q0")

    # --- alfabeto ---------------------------------------------------------
    def test_simbolo_com_mais_de_um_caractere(self):
        dados = afd_termina_em_1()
        dados["alfabeto"] = ["0", "10"]
        self.assertInvalido(dados, "'10'")

    def test_simbolo_espaco(self):
        dados = afd_termina_em_1()
        dados["alfabeto"].append(" ")
        self.assertInvalido(dados, "espaço")

    def test_simbolo_numerico_sem_aspas(self):
        dados = afd_termina_em_1()
        dados["alfabeto"] = [0, 1]
        self.assertInvalido(dados, "alfabeto")

    def test_simbolo_repetido(self):
        dados = afd_termina_em_1()
        dados["alfabeto"] = ["0", "1", "0"]
        self.assertInvalido(dados, "repetido")

    # --- transições (exatamente uma por símbolo) ---------------------------
    def test_transicao_faltando(self):
        dados = afd_termina_em_1()
        del dados["transicoes"]["q1"]["1"]
        self.assertInvalido(dados, "q1", "'1'")

    def test_estado_sem_nenhuma_transicao(self):
        dados = afd_termina_em_1()
        del dados["transicoes"]["q1"]
        self.assertInvalido(dados, "q1", "não tem transições")

    def test_transicoes_de_estado_desconhecido(self):
        dados = afd_termina_em_1()
        dados["transicoes"]["q7"] = {"0": "q0", "1": "q0"}
        self.assertInvalido(dados, "q7")

    def test_transicao_com_simbolo_fora_do_alfabeto(self):
        dados = afd_termina_em_1()
        dados["transicoes"]["q0"]["2"] = "q0"
        self.assertInvalido(dados, "'2'", "alfabeto")

    def test_destino_inexistente(self):
        dados = afd_termina_em_1()
        dados["transicoes"]["q0"]["0"] = "q5"
        self.assertInvalido(dados, "q5")

    def test_dois_destinos_nao_deterministico(self):
        dados = afd_termina_em_1()
        dados["transicoes"]["q0"]["1"] = ["q0", "q1"]
        self.assertInvalido(dados, "mais de um destino")

    def test_destino_vazio_ou_nulo(self):
        for destino in ("", None):
            with self.subTest(destino=destino):
                dados = afd_termina_em_1()
                dados["transicoes"]["q0"]["1"] = destino
                self.assertInvalido(dados, "('q0', '1')")

    def test_transicoes_de_um_estado_nao_sao_objeto(self):
        dados = afd_termina_em_1()
        dados["transicoes"]["q0"] = ["q0", "q1"]
        self.assertInvalido(dados, "q0")

    def test_varios_erros_listados_juntos(self):
        dados = afd_termina_em_1()
        dados["estado_inicial"] = "q9"
        dados["transicoes"]["q1"]["1"] = "q5"
        mensagem = self.assertInvalido(dados, "q9", "q5")
        self.assertIn("2 problemas", mensagem)

    # --- leitura de arquivos ----------------------------------------------
    def test_carregar_arquivo_valido(self):
        caminho = self.criar("ok.json", afd_termina_em_1())
        self.assertEqual(carregar_afd(str(caminho)), afd_termina_em_1())

    def test_aceita_path_e_str(self):
        caminho = self.criar("ok.json", afd_termina_em_1())
        self.assertEqual(carregar_afd(caminho), carregar_afd(str(caminho)))

    def test_arquivo_inexistente(self):
        with self.assertRaises(ErroAFD) as ctx:
            carregar_afd(self.pasta_tmp / "nao_existe.json")
        self.assertIn("não encontrado", str(ctx.exception))

    def test_caminho_e_pasta(self):
        with self.assertRaises(ErroAFD):
            carregar_afd(self.pasta_tmp)

    def test_arquivo_vazio(self):
        with self.assertRaises(ErroAFD) as ctx:
            carregar_afd(self.criar("vazio.json", ""))
        self.assertIn("JSON malformado", str(ctx.exception))

    def test_virgula_sobrando_no_final(self):
        texto = '{"estados": ["q0"], }'
        with self.assertRaises(ErroAFD) as ctx:
            carregar_afd(self.criar("virgula.json", texto))
        self.assertIn("linha 1", str(ctx.exception))

    def test_aspas_simples_nao_sao_json(self):
        texto = json.dumps(afd_termina_em_1()).replace('"', "'")
        with self.assertRaises(ErroAFD):
            carregar_afd(self.criar("aspas.json", texto))

    def test_arquivo_que_nao_e_utf8(self):
        caminho = self.pasta_tmp / "latin1.json"
        dados = afd_termina_em_1()
        dados["nome"] = "Autômato"
        caminho.write_bytes(json.dumps(dados, ensure_ascii=False).encode("latin-1"))
        with self.assertRaises(ErroAFD) as ctx:
            carregar_afd(caminho)
        self.assertIn("UTF-8", str(ctx.exception))

    def test_chave_duplicada_no_json(self):
        texto = (
            '{"estados": ["q0"], "alfabeto": ["a"], "estado_inicial": "q0",'
            ' "estados_finais": [], "transicoes": {"q0": {"a": "q0", "a": "q0"}}}'
        )
        with self.assertRaises(ErroAFD) as ctx:
            carregar_afd(self.criar("dup.json", texto))
        self.assertIn("mais de uma vez", str(ctx.exception))

    def test_arquivo_com_acentos_em_utf8(self):
        dados = {
            "nome": "Ímpar de 'á'",
            "estados": ["ímpar", "par"],
            "alfabeto": ["á"],
            "estado_inicial": "par",
            "estados_finais": ["ímpar"],
            "transicoes": {"par": {"á": "ímpar"}, "ímpar": {"á": "par"}},
        }
        afd = carregar_afd(self.criar("acentos.json", dados))
        self.assertTrue(simular_afd(afd, "ááá")[0])


# ==========================================================================
# 4. Arquivos de exemplo do repositório
# ==========================================================================

class TestExemplos(unittest.TestCase):

    def test_todos_os_exemplos_validos_carregam(self):
        arquivos = sorted(EXEMPLOS.glob("*.json"))
        self.assertGreaterEqual(len(arquivos), 3)
        for arquivo in arquivos:
            with self.subTest(arquivo=arquivo.name):
                afd = carregar_afd(arquivo)
                self.assertIsInstance(afd, dict)

    def test_todos_os_exemplos_invalidos_sao_recusados(self):
        esperado = {
            "campo_faltando.json": "estado_inicial",
            "destino_inexistente.json": "q5",
            "estado_final_inexistente.json": "q2",
            "estado_inicial_invalido.json": "q9",
            "json_malformado.json": "JSON malformado",
            "nao_deterministico.json": "mais de um destino",
            "simbolo_fora_do_alfabeto.json": "'2'",
            "transicao_duplicada.json": "mais de uma vez",
            "transicao_faltando.json": "não tem transição",
            "varios_erros.json": "5 problemas",
        }
        encontrados = {arquivo.name for arquivo in INVALIDOS.glob("*.json")}
        self.assertEqual(encontrados, set(esperado), "há exemplo inválido sem teste")
        for nome, trecho in esperado.items():
            with self.subTest(arquivo=nome):
                with self.assertRaises(ErroAFD) as ctx:
                    carregar_afd(INVALIDOS / nome)
                self.assertIn(trecho, str(ctx.exception))


# ==========================================================================
# 5. Integração leitor + motor (o mesmo caminho que o main.py percorre)
# ==========================================================================

class TestIntegracao(unittest.TestCase):

    def test_tabela_de_casos(self):
        casos = [
            ("termina_em_1.json", "101", True),
            ("termina_em_1.json", "100", False),
            ("termina_em_1.json", "", False),
            ("termina_em_1.json", "1", True),
            ("zeros_pares.json", "", True),
            ("zeros_pares.json", "1001", True),
            ("zeros_pares.json", "10", False),
            ("contem_ab.json", "bbab", True),
            ("contem_ab.json", "bbba", False),
            ("contem_ab.json", "", False),
        ]
        for arquivo, sequencia, esperado in casos:
            with self.subTest(arquivo=arquivo, sequencia=sequencia):
                afd = carregar_afd(EXEMPLOS / arquivo)
                self.assertEqual(simular_afd(afd, sequencia)[0], esperado)

    def test_simbolo_de_outro_alfabeto(self):
        afd = carregar_afd(EXEMPLOS / "contem_ab.json")
        with self.assertRaises(ValueError):
            simular_afd(afd, "a1b")


# ==========================================================================
# 6. Interface (main.py) com entradas simuladas
# ==========================================================================

class TestInterface(unittest.TestCase):

    def executar(self, *entradas):
        """Roda main.main() digitando as entradas e devolve o que foi impresso."""
        saida = io.StringIO()
        with mock.patch("builtins.input", side_effect=list(entradas)), redirect_stdout(saida):
            main.main()
        return saida.getvalue()

    def test_fluxo_aceita(self):
        texto = self.executar("1", "exemplos/termina_em_1.json", "2", "101", "0")
        self.assertIn("carregado com sucesso", texto)
        self.assertIn("q0 -> q1", texto)
        self.assertIn("q1 -> q0", texto)
        self.assertIn("Resultado: ACEITA", texto)

    def test_fluxo_rejeita(self):
        texto = self.executar("1", "exemplos/termina_em_1.json", "2", "100", "0")
        self.assertIn("Resultado: REJEITA", texto)

    def test_simbolo_invalido_nao_encerra_o_programa(self):
        texto = self.executar(
            "1", "exemplos/termina_em_1.json", "2", "102", "2", "1", "0"
        )
        self.assertIn("Não foi possível simular", texto)
        self.assertIn("'2' na posição 3", texto)
        self.assertIn("Resultado: ACEITA", texto)  # continuou funcionando depois

    def test_sequencia_vazia(self):
        texto = self.executar("1", "exemplos/zeros_pares.json", "2", "", "0")
        self.assertIn("sequência é vazia", texto)
        self.assertIn("Resultado: ACEITA", texto)

    def test_json_quebrado_mostra_erro_e_continua(self):
        texto = self.executar("1", "exemplos/invalidos/json_malformado.json", "3", "0")
        self.assertIn("Não foi possível carregar", texto)
        self.assertIn("JSON malformado", texto)
        self.assertIn("Nenhum autômato carregado", texto)

    def test_arquivo_inexistente(self):
        texto = self.executar("1", "exemplos/nao_existe.json", "0")
        self.assertIn("não encontrado", texto)

    def test_caminho_em_branco(self):
        texto = self.executar("1", "   ", "0")
        self.assertIn("Informe o caminho", texto)

    def test_arquivo_invalido_mantem_o_anterior(self):
        texto = self.executar(
            "1", "exemplos/termina_em_1.json",
            "1", "exemplos/invalidos/transicao_faltando.json",
            "2", "1", "0",
        )
        self.assertIn("Não foi possível carregar", texto)
        self.assertIn("Resultado: ACEITA", texto)

    def test_testar_antes_de_carregar(self):
        texto = self.executar("2", "0")
        self.assertIn("Carregue um autômato", texto)

    def test_opcao_invalida(self):
        texto = self.executar("9", "abc", "", "0")
        self.assertEqual(texto.count("Opção inválida"), 3)

    def test_ctrl_d_ou_fim_da_entrada_encerra_sem_traceback(self):
        # input() lança EOFError quando a entrada acaba (Ctrl+D / Ctrl+Z).
        texto = self.executar("1", "exemplos/termina_em_1.json", EOFError)
        self.assertIn("Encerrando", texto)

    def test_ctrl_c_encerra_sem_traceback(self):
        saida = io.StringIO()
        with mock.patch("builtins.input", side_effect=KeyboardInterrupt), redirect_stdout(saida):
            main.main()
        self.assertIn("Encerrando", saida.getvalue())

    def test_caminho_absoluto(self):
        caminho = str(EXEMPLOS / "contem_ab.json")
        texto = self.executar("1", caminho, "2", "ab", "0")
        self.assertIn("Resultado: ACEITA", texto)


# ==========================================================================
# 7. Pendências: casos que FALHAM hoje (ver RELATORIO_TESTES.md)
# ==========================================================================

class TestPendencias(ArquivosTemporarios):
    """Falhas encontradas na rodada 1 e corrigidas na rodada 2.

    Ficam na suíte para garantir que os problemas não voltem.
    """

    def test_P1_leitor_aceita_json_utf8_com_bom(self):
        # Bloco de Notas ("UTF-8 com BOM") e o PowerShell 5.1
        # (Out-File / Set-Content -Encoding utf8) salvam com BOM.
        caminho = self.criar("bom.json", afd_termina_em_1(), encoding="utf-8-sig")
        self.assertEqual(carregar_afd(caminho), afd_termina_em_1())

    def test_P2_interface_aceita_caminho_entre_aspas(self):
        # "Copiar como caminho" do Explorador do Windows coloca aspas.
        caminho = f'"{EXEMPLOS / "termina_em_1.json"}"'
        saida = io.StringIO()
        entradas = ["1", caminho, "2", "101", "0"]
        with mock.patch("builtins.input", side_effect=entradas), redirect_stdout(saida):
            main.main()
        self.assertIn("Resultado: ACEITA", saida.getvalue())


if __name__ == "__main__":
    unittest.main()
