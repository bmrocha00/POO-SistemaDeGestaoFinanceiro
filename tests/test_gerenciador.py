import os
import shutil
import tempfile
import unittest

from database.gerenciador_arquivos import GerenciadorArquivos, ErroPersistencia


def lancamento(id=1, tipo="Receita", descricao="Salario", valor=3000,
               data="2026-11-01", categoria="Trabalho"):
    """Monta um dict de lançamento para os testes."""
    return {"id": id, "tipo": tipo, "descricao": descricao, "valor": valor,
            "data": data, "categoria": categoria}


class TestGerenciadorArquivos(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.g = GerenciadorArquivos(self.pasta)

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    # ---------- inicialização ----------
    def test_cria_pasta_e_arquivos(self):
        shutil.rmtree(self.pasta)
        GerenciadorArquivos(self.pasta)
        self.assertTrue(os.path.exists(os.path.join(self.pasta, "lancamentos.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.pasta, "categorias.txt")))

    def test_nao_apaga_dados_existentes(self):
        self.g.salvar_lancamento(lancamento())
        novo = GerenciadorArquivos(self.pasta)
        self.assertEqual(len(novo.carregar_lancamentos()), 1)

    def test_pasta_invalida_gera_erro_persistencia(self):
        arquivo = os.path.join(self.pasta, "arquivo.txt")
        with open(arquivo, "w") as f:
            f.write("x")
        with self.assertRaises(ErroPersistencia):
            GerenciadorArquivos(os.path.join(arquivo, "sub"))

    def test_setter_pasta_invalida(self):
        for invalido in ("", "   ", None, 123):
            with self.assertRaises(ValueError):
                self.g.pasta_dados = invalido

    def test_setter_pasta_valida(self):
        nova = os.path.join(self.pasta, "outra")
        self.g.pasta_dados = nova
        self.assertEqual(self.g.pasta_dados, nova)
        self.assertTrue(os.path.exists(os.path.join(nova, "lancamentos.txt")))

    # ---------- salvar e carregar ----------
    def test_salvar_e_carregar_mantem_dados_e_tipos(self):
        original = lancamento()
        self.g.salvar_lancamento(original)
        carregados = self.g.carregar_lancamentos()
        self.assertEqual(carregados, [{**original, "valor": 3000.0}])
        self.assertIsInstance(carregados[0]["id"], int)
        self.assertIsInstance(carregados[0]["valor"], float)

    def test_descricao_com_ponto_e_virgula(self):
        self.g.salvar_lancamento(lancamento(descricao="pao; leite"))
        self.assertEqual(self.g.carregar_lancamentos()[0]["descricao"], "pao; leite")

    def test_acentos(self):
        self.g.salvar_lancamento(lancamento(descricao="Açaí", categoria="Alimentação"))
        r = self.g.carregar_lancamentos()[0]
        self.assertEqual((r["descricao"], r["categoria"]), ("Açaí", "Alimentação"))

    def test_salvar_varios_preserva_ordem(self):
        for i in (1, 2, 3):
            self.g.salvar_lancamento(lancamento(id=i))
        self.assertEqual([r["id"] for r in self.g.carregar_lancamentos()], [1, 2, 3])

    def test_salvar_campo_faltando(self):
        dado = lancamento()
        del dado["categoria"]
        with self.assertRaises(ValueError):
            self.g.salvar_lancamento(dado)
        self.assertEqual(self.g.carregar_lancamentos(), [])   # nada foi gravado

    def test_salvar_valor_invalido(self):
        with self.assertRaises(ValueError):
            self.g.salvar_lancamento(lancamento(valor="abc"))

    def test_salvar_nao_dict(self):
        with self.assertRaises(ValueError):
            self.g.salvar_lancamento("texto")

    def test_carregar_arquivo_vazio(self):
        self.assertEqual(self.g.carregar_lancamentos(), [])

    def test_carregar_arquivo_apagado_recria(self):
        os.remove(self.g.caminho_lancamentos)
        self.assertEqual(self.g.carregar_lancamentos(), [])
        self.assertTrue(os.path.exists(self.g.caminho_lancamentos))

    # ---------- linhas mal formatadas ----------
    def test_linhas_corrompidas_sao_ignoradas_com_aviso(self):
        self.g.salvar_lancamento(lancamento(id=1))
        with open(self.g.caminho_lancamentos, "a", encoding="utf-8") as f:
            f.write("2;Despesa;so;tres\n")                       # colunas erradas
            f.write("x;Despesa;Mercado;10.00;2026-11-02;A\n")    # id inválido
            f.write("4;Despesa;Mercado;abc;2026-11-02;A\n")      # valor inválido
            f.write("\n")                                        # linha em branco
        self.g.salvar_lancamento(lancamento(id=5))
        carregados = self.g.carregar_lancamentos()
        self.assertEqual([r["id"] for r in carregados], [1, 5])
        self.assertEqual(len(self.g.avisos), 3)

    def test_avisos_sao_resetados_a_cada_leitura(self):
        with open(self.g.caminho_lancamentos, "w", encoding="utf-8") as f:
            f.write("lixo\n")
        self.g.carregar_lancamentos()
        self.assertEqual(len(self.g.avisos), 1)
        self.g.carregar_lancamentos()
        self.assertEqual(len(self.g.avisos), 1)   # não acumula

    def test_avisos_devolve_copia(self):
        self.g.avisos.append("x")
        self.assertEqual(self.g.avisos, [])

    # ---------- atualizar ----------
    def test_atualizar_muda_so_o_registro_certo(self):
        self.g.salvar_lancamento(lancamento(id=1))
        self.g.salvar_lancamento(lancamento(id=2, descricao="Mercado"))
        self.assertTrue(self.g.atualizar_lancamento(2, {"valor": 99.9, "descricao": "Feira"}))
        r1, r2 = self.g.carregar_lancamentos()
        self.assertEqual(r1["descricao"], "Salario")
        self.assertEqual((r2["descricao"], r2["valor"]), ("Feira", 99.9))

    def test_atualizar_id_inexistente(self):
        self.g.salvar_lancamento(lancamento())
        self.assertFalse(self.g.atualizar_lancamento(99, {"valor": 1}))

    def test_atualizar_nao_altera_id(self):
        self.g.salvar_lancamento(lancamento(id=3))
        self.g.atualizar_lancamento(3, {"id": 50, "valor": 10})
        self.assertEqual([r["id"] for r in self.g.carregar_lancamentos()], [3])

    def test_atualizar_valor_invalido_nao_corrompe(self):
        self.g.salvar_lancamento(lancamento(valor=100))
        with self.assertRaises(ValueError):
            self.g.atualizar_lancamento(1, {"valor": "abc"})
        self.assertEqual(self.g.carregar_lancamentos()[0]["valor"], 100.0)

    def test_atualizar_dados_nao_dict(self):
        with self.assertRaises(ValueError):
            self.g.atualizar_lancamento(1, "texto")

    # ---------- excluir ----------
    def test_excluir_remove_so_o_registro_certo(self):
        for i in (1, 2, 3):
            self.g.salvar_lancamento(lancamento(id=i))
        self.assertTrue(self.g.excluir_lancamento(2))
        self.assertEqual([r["id"] for r in self.g.carregar_lancamentos()], [1, 3])

    def test_excluir_id_inexistente(self):
        self.g.salvar_lancamento(lancamento())
        self.assertFalse(self.g.excluir_lancamento(99))
        self.assertEqual(len(self.g.carregar_lancamentos()), 1)

    def test_excluir_ultimo_deixa_arquivo_vazio(self):
        self.g.salvar_lancamento(lancamento())
        self.assertTrue(self.g.excluir_lancamento(1))
        self.assertEqual(self.g.carregar_lancamentos(), [])

    def test_nao_deixa_arquivo_temporario(self):
        self.g.salvar_lancamento(lancamento())
        self.g.excluir_lancamento(1)
        self.assertFalse(os.path.exists(self.g.caminho_lancamentos + ".tmp"))

    # ---------- próximo id ----------
    def test_proximo_id_arquivo_vazio(self):
        self.assertEqual(self.g.gerar_proximo_id(), 1)

    def test_proximo_id_usa_maior_id(self):
        for i in (1, 7, 3):
            self.g.salvar_lancamento(lancamento(id=i))
        self.assertEqual(self.g.gerar_proximo_id(), 8)

    # ---------- categorias ----------
    def test_categorias_vazio(self):
        self.assertEqual(self.g.carregar_categorias(), [])

    def test_salvar_e_carregar_categorias(self):
        self.assertTrue(self.g.salvar_categoria("Alimentacao"))
        self.assertTrue(self.g.salvar_categoria("Transporte"))
        self.assertEqual(self.g.carregar_categorias(), ["Alimentacao", "Transporte"])

    def test_categoria_duplicada_ignora_maiusculas(self):
        self.g.salvar_categoria("Alimentacao")
        self.assertFalse(self.g.salvar_categoria("alimentacao"))
        self.assertFalse(self.g.salvar_categoria("  ALIMENTACAO  "))
        self.assertEqual(self.g.carregar_categorias(), ["Alimentacao"])

    def test_categoria_invalida(self):
        for invalida in ("", "   ", None, 5):
            with self.assertRaises(ValueError):
                self.g.salvar_categoria(invalida)

    def test_categoria_com_acento(self):
        self.g.salvar_categoria("Alimentação")
        self.assertEqual(self.g.carregar_categorias(), ["Alimentação"])
