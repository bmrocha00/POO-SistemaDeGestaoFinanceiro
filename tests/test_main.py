"""Testes da interface (main.py) usando o GestorFinanceiro real.

Execute na raiz do projeto:  python -m unittest tests.test_main -v
"""
import io
import unittest
from contextlib import redirect_stdout
from datetime import date
from unittest.mock import patch

import main
from models import Receita, Despesa
from services.gestor_financeiro import GestorFinanceiro


def rodar(gestor, entradas):
    """Executa o menu com as entradas simuladas e devolve o texto impresso."""
    saida = io.StringIO()
    with patch("builtins.input", side_effect=entradas), redirect_stdout(saida):
        main.executar(gestor)
    texto = saida.getvalue()
    assert "Erro inesperado" not in texto, texto  # qualquer bug interno vira falha
    return texto


class TestMenu(unittest.TestCase):
    def setUp(self):
        self.g = GestorFinanceiro()

    def _preencher(self):
        self.g.cadastrar_lancamento(Receita("Salario", 3000, "2026-11-01", "Trabalho"))
        self.g.cadastrar_lancamento(Despesa("Mercado", 250, "2026-11-02", "Alimentacao"))

    def test_sair(self):
        self.assertIn("Até logo", rodar(self.g, ["0"]))

    def test_opcao_invalida_nao_derruba(self):
        saida = rodar(self.g, ["9", "abc", "0"])
        self.assertEqual(saida.count("Opção inválida"), 2)

    def test_cadastrar_receita_com_data_padrao(self):
        rodar(self.g, ["1", "Salario", "3000", "", "Trabalho", "0"])
        self.assertEqual(len(self.g.listar_lancamentos()), 1)
        r = self.g.listar_lancamentos()[0]
        self.assertIsInstance(r, Receita)
        self.assertEqual(r.data, date.today())

    def test_mensagens_de_sucesso(self):
        saida = rodar(self.g, ["1", "Salario", "3000", "", "Trabalho",
                               "4", "1", "", "3500", "", "", "5", "1", "s", "0"])
        self.assertIn("Receita cadastrada com sucesso", saida)
        self.assertIn("Movimentação atualizada", saida)
        self.assertIn("Movimentação excluída", saida)

    def test_cadastrar_despesa(self):
        rodar(self.g, ["2", "Mercado", "250,50", "2026-11-02", "Alimentacao", "0"])
        d = self.g.listar_lancamentos()[0]
        self.assertIsInstance(d, Despesa)
        self.assertEqual(d.valor, 250.5)

    def test_entradas_invalidas_sao_repetidas(self):
        saida = rodar(self.g, ["2", "Mercado", "abc", "-5", "100",
                               "31/12/2026", "2026-12-31", "Casa", "0"])
        self.assertEqual(saida.count("Entrada inválida"), 3)
        self.assertEqual(len(self.g.listar_lancamentos()), 1)
        self.assertEqual(self.g.listar_lancamentos()[0].valor, 100.0)

    def test_listar_todas_e_filtrar(self):
        self._preencher()
        saida = rodar(self.g, ["3", "1", "3", "2", "trabalho", "0"])
        self.assertIn("Mercado", saida)
        self.assertIn("2 movimentação(ões)", saida)
        self.assertIn("1 movimentação(ões)", saida)

    def test_listar_vazio(self):
        self.assertIn("Nenhuma movimentação", rodar(self.g, ["3", "1", "0"]))

    def test_editar_so_o_valor(self):
        self._preencher()
        rodar(self.g, ["4", "1", "", "500", "", "", "0"])
        r = self.g.listar_lancamentos()[0]
        self.assertEqual(r.valor, 500.0)
        self.assertEqual(r.descricao, "Salario")

    def test_editar_id_inexistente(self):
        self.assertIn("Nenhuma movimentação com ID 99", rodar(self.g, ["4", "99", "0"]))

    def test_excluir_confirmado(self):
        self._preencher()
        rodar(self.g, ["5", "1", "s", "0"])
        self.assertEqual([l.id for l in self.g.listar_lancamentos()], [2])

    def test_excluir_cancelado(self):
        self._preencher()
        rodar(self.g, ["5", "1", "n", "0"])
        self.assertEqual(len(self.g.listar_lancamentos()), 2)

    def test_saldo(self):
        self._preencher()
        self.assertIn("R$ 2750.00", rodar(self.g, ["6", "0"]))

    def test_relatorio_mensal(self):
        self._preencher()
        saida = rodar(self.g, ["7", "2026", "13", "11", "0"])
        self.assertIn("máximo é 12", saida)
        self.assertIn("11/2026", saida)
        self.assertIn("Total receitas: R$ 3000.00", saida)
        self.assertIn("Total despesas: R$ 250.00", saida)
        self.assertIn("Saldo: R$ 2750.00", saida)

    def test_erro_de_arquivo_nao_derruba_o_menu(self):
        def falha(_):
            raise OSError("disco cheio")
        self.g.cadastrar_lancamento = falha
        saida = rodar(self.g, ["1", "x", "10", "", "c", "0"])
        self.assertIn("Erro de arquivo: disco cheio", saida)
        self.assertIn("Até logo", saida)

    def test_id_inexistente_na_exclusao_e_edicao_nao_quebra(self):
        saida = rodar(self.g, ["5", "42", "4", "42", "0"])
        self.assertEqual(saida.count("Nenhuma movimentação com ID 42"), 2)

    def test_filtro_categoria_vazia_mostra_erro(self):
        saida = rodar(self.g, ["3", "2", "", "0"])
        self.assertIn("Categoria inválida", saida)
        self.assertIn("Até logo", saida)

    def test_ctrl_c_encerra_com_elegancia(self):
        saida = rodar(self.g, [KeyboardInterrupt()])
        self.assertIn("Encerrando", saida)


if __name__ == "__main__":
    unittest.main()