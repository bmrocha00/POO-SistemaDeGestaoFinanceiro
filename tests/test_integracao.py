"""Integração: main + GestorFinanceiro + GerenciadorArquivos (TXT real em pasta temporária).

Execute na raiz do projeto:  python -m unittest tests.test_integracao -v
"""
import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import main


def sessao(pasta, entradas):
    """Abre o programa (carrega o TXT), roda as entradas e devolve o texto impresso."""
    saida = io.StringIO()
    with patch("builtins.input", side_effect=entradas), redirect_stdout(saida):
        main.executar(main.criar_gestor(pasta))
    texto = saida.getvalue()
    assert "Erro inesperado" not in texto, texto
    return texto


class TestPersistenciaNoMenu(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def _arquivo(self):
        with open(os.path.join(self.pasta, "lancamentos.txt"), encoding="utf-8") as f:
            return f.read()

    def test_dados_sobrevivem_ao_reiniciar(self):
        sessao(self.pasta, ["1", "Salario", "3000", "2026-11-01", "Trabalho",
                            "2", "Mercado", "250,50", "2026-11-02", "Alimentação", "0"])
        self.assertIn("1;Receita;Salario;3000.00;2026-11-01;Trabalho", self._arquivo())
        saida = sessao(self.pasta, ["3", "1", "6", "0"])
        self.assertIn("Salario", saida)
        self.assertIn("Mercado", saida)
        self.assertIn("R$ 2749.50", saida)

    def test_novo_id_continua_depois_de_reiniciar(self):
        sessao(self.pasta, ["1", "A", "10", "2026-11-01", "X", "0"])
        sessao(self.pasta, ["1", "B", "20", "2026-11-02", "X", "0"])
        ids = [l.split(";")[0] for l in self._arquivo().splitlines()]
        self.assertEqual(ids, ["1", "2"])

    def test_editar_persiste(self):
        sessao(self.pasta, ["1", "Salario", "3000", "2026-11-01", "Trabalho", "0"])
        sessao(self.pasta, ["4", "1", "", "3500", "", "", "0"])
        self.assertIn("1;Receita;Salario;3500.00;2026-11-01;Trabalho", self._arquivo())
        self.assertIn("R$ 3500.00", sessao(self.pasta, ["6", "0"]))

    def test_excluir_persiste(self):
        sessao(self.pasta, ["1", "A", "10", "2026-11-01", "X",
                            "1", "B", "20", "2026-11-02", "X", "0"])
        sessao(self.pasta, ["5", "1", "s", "0"])
        self.assertEqual(len(self._arquivo().splitlines()), 1)
        self.assertIn(";B;", self._arquivo())

    def test_relatorio_depois_de_reiniciar(self):
        sessao(self.pasta, ["1", "Salario", "3000", "2026-11-01", "Trabalho",
                            "2", "Mercado", "250", "2026-11-02", "Casa", "0"])
        saida = sessao(self.pasta, ["7", "2026", "11", "0"])
        self.assertIn("Total receitas: R$ 3000.00", saida)
        self.assertIn("Total despesas: R$ 250.00", saida)

    def test_linha_mal_formatada_nao_derruba_o_programa(self):
        with open(os.path.join(self.pasta, "lancamentos.txt"), "w", encoding="utf-8") as f:
            f.write("1;Receita;Salario;3000.00;2026-11-01;Trabalho\nlixo\n")
        self.assertIn("R$ 3000.00", sessao(self.pasta, ["6", "0"]))


if __name__ == "__main__":
    unittest.main()