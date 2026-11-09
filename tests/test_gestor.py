
import unittest

from models import Receita, Despesa
from services.gestor_financeiro import GestorFinanceiro


class TestGestorFinanceiro(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorFinanceiro()

    def test_cadastrar_e_listar(self):
        receita = Receita("Salário", 3000, "2026-11-01", "Trabalho")

        self.gestor.cadastrar_lancamento(receita)

        self.assertEqual(len(self.gestor.listar_lancamentos()), 1)

    def test_calcular_saldo(self):
        receita = Receita("Salário", 3000, "2026-11-01", "Trabalho")
        despesa = Despesa("Mercado", 250, "2026-11-02", "Alimentação")

        self.gestor.cadastrar_lancamento(receita)
        self.gestor.cadastrar_lancamento(despesa)

        self.assertEqual(self.gestor.calcular_saldo(), 2750.0)

    def test_remover_lancamento(self):
        receita = Receita("Salário", 3000, "2026-11-01", "Trabalho")

        self.gestor.cadastrar_lancamento(receita)
        self.gestor.remover_lancamento(receita.id)

        self.assertEqual(len(self.gestor.listar_lancamentos()), 0)

    def test_remover_lancamento_inexistente(self):
        with self.assertRaises(ValueError):
            self.gestor.remover_lancamento(999)
    
    def test_editar_lancamento(self):
        receita = Receita("Salário", 3000, "2026-11-01", "Trabalho")

        self.gestor.cadastrar_lancamento(receita)

        self.gestor.editar_lancamento(
            receita.id,
            descricao="Bolsa",
            valor=3500
        )

        self.assertEqual(receita.descricao, "Bolsa")
        self.assertEqual(receita.valor, 3500)
        self.assertEqual(self.gestor.calcular_saldo(), 3500)

    def test_editar_valor_invalido(self):
        receita = Receita("Salário", 3000, "2026-11-01", "Trabalho")

        self.gestor.cadastrar_lancamento(receita)

        with self.assertRaises(ValueError):
            self.gestor.editar_lancamento(
                receita.id,
                descricao="Bolsa",
                valor=-100
            )

        self.assertEqual(receita.descricao, "Salário")
        self.assertEqual(receita.valor, 3000)
    
    def test_filtrar_por_categoria(self):
        receita = Receita("Salário", 3000, "2026-11-01", "Trabalho")
        despesa = Despesa("Mercado", 250, "2026-11-05", "Alimentação")

        self.gestor.cadastrar_lancamento(receita)
        self.gestor.cadastrar_lancamento(despesa)

        resultado = self.gestor.filtrar_por_categoria("alimentação")

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0].descricao, "Mercado")

    def test_filtrar_por_data(self):
        receita = Receita("Salário", 3000, "2026-11-01", "Trabalho")
        despesa = Despesa("Mercado", 250, "2026-11-15", "Alimentação")

        self.gestor.cadastrar_lancamento(receita)
        self.gestor.cadastrar_lancamento(despesa)

        resultado = self.gestor.filtrar_por_data(
            "2026-11-01", "2026-11-10"
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0].descricao, "Salário")
    
    def test_gerar_relatorio_mensal(self):
        receita = Receita("Salário", 3000, "2026-11-01", "Trabalho")
        despesa1 = Despesa("Mercado", 250, "2026-11-05", "Alimentação")
        despesa2 = Despesa("Transporte", 100, "2026-11-10", "Transporte")

        self.gestor.cadastrar_lancamento(receita)
        self.gestor.cadastrar_lancamento(despesa1)
        self.gestor.cadastrar_lancamento(despesa2)

        relatorio = self.gestor.gerar_relatorio_mensal(2026, 11)

        self.assertEqual(relatorio["total_receitas"], 3000)
        self.assertEqual(relatorio["total_despesas"], 350)
        self.assertEqual(relatorio["saldo"], 2650)
        self.assertEqual(relatorio["quantidade_lancamentos"], 3)

    def test_relatorio_mes_diferente(self):
        receita = Receita("Salário", 3000, "2026-10-01", "Trabalho")

        self.gestor.cadastrar_lancamento(receita)

        relatorio = self.gestor.gerar_relatorio_mensal(2026, 11)

        self.assertEqual(relatorio["saldo"], 0)
        self.assertEqual(relatorio["quantidade_lancamentos"], 0)

    def test_relatorio_mes_invalido(self):
        with self.assertRaises(ValueError):
            self.gestor.gerar_relatorio_mensal(2026, 13)






if __name__ == "__main__":
    unittest.main()
