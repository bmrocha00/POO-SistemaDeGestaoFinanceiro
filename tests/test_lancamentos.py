"""Testes das classes de modelagem (Integrante 1).

Execute na raiz do projeto:  python -m unittest tests.test_lancamentos -v
"""
import unittest
from datetime import date

from models import (
    Lancamento, Receita, Despesa, Categoria, criar_lancamento,
    LancamentoError, ValorInvalidoError, DataInvalidaError,
    DescricaoInvalidaError,
)


class TestAbstracao(unittest.TestCase):
    def test_lancamento_nao_pode_ser_instanciado(self):
        with self.assertRaises(TypeError):
            Lancamento("x", 10, "2026-11-01", "Teste")


class TestPolimorfismo(unittest.TestCase):
    def test_receita_tem_impacto_positivo(self):
        r = Receita("Salario", 3000, "2026-11-01", "Trabalho")
        self.assertEqual(r.calcular_impacto(), 3000.0)

    def test_despesa_tem_impacto_negativo(self):
        d = Despesa("Mercado", 250, "2026-11-02", "Alimentacao")
        self.assertEqual(d.calcular_impacto(), -250.0)

    def test_soma_de_impactos_sem_checar_tipo(self):
        lancs = [
            Receita("Salario", 3000, "2026-11-01", "Trabalho"),
            Despesa("Mercado", 250, "2026-11-02", "Alimentacao"),
            Despesa("Onibus", 50.50, "2026-11-03", "Transporte"),
        ]
        self.assertEqual(round(sum(l.calcular_impacto() for l in lancs), 2), 2699.5)

    def test_tipo(self):
        self.assertEqual(Receita("a", 1, "2026-01-01", "c").tipo, "Receita")
        self.assertEqual(Despesa("a", 1, "2026-01-01", "c").tipo, "Despesa")


class TestEncapsulamento(unittest.TestCase):
    def setUp(self):
        self.r = Receita("Salario", 3000, "2026-11-01", "Trabalho", id=1)

    def test_getters(self):
        self.assertEqual(self.r.id, 1)
        self.assertEqual(self.r.descricao, "Salario")
        self.assertEqual(self.r.valor, 3000.0)
        self.assertEqual(self.r.data, date(2026, 11, 1))
        self.assertEqual(self.r.categoria, "Trabalho")

    def test_setters_validos(self):
        self.r.valor = "1500,75"
        self.r.data = "2026-12-25"
        self.r.descricao = "  13o  "
        self.assertEqual(self.r.valor, 1500.75)
        self.assertEqual(self.r.data, date(2026, 12, 25))
        self.assertEqual(self.r.descricao, "13o")

    def test_setter_invalido_preserva_valor_antigo(self):
        with self.assertRaises(ValorInvalidoError):
            self.r.valor = -5
        self.assertEqual(self.r.valor, 3000.0)


class TestValidacao(unittest.TestCase):
    def test_valores_invalidos(self):
        for v in (0, -10, "abc", None, "", True, float("nan"), float("inf")):
            with self.subTest(valor=v):
                with self.assertRaises(ValorInvalidoError):
                    Despesa("x", v, "2026-11-01", "c")

    def test_datas_invalidas(self):
        for d in ("2026-13-01", "2026-02-30", "01/11/2026", "", "abc", None, 20261101):
            with self.subTest(data=d):
                with self.assertRaises(DataInvalidaError):
                    Receita("x", 10, d, "c")

    def test_data_aceita_objeto_date(self):
        r = Receita("x", 10, date(2026, 11, 1), "c")
        self.assertEqual(r.data, date(2026, 11, 1))

    def test_descricao_e_categoria_vazias(self):
        with self.assertRaises(DescricaoInvalidaError):
            Receita("   ", 10, "2026-11-01", "c")
        with self.assertRaises(DescricaoInvalidaError):
            Receita("x", 10, "2026-11-01", "")

    def test_id_invalido(self):
        with self.assertRaises(LancamentoError):
            Receita("x", 10, "2026-11-01", "c", id="abc")
        with self.assertRaises(LancamentoError):
            Receita("x", 10, "2026-11-01", "c", id=-1)

    def test_erros_sao_value_error(self):
        with self.assertRaises(ValueError):
            Receita("x", -1, "2026-11-01", "c")


class TestIntegracao(unittest.TestCase):
    def test_to_dict(self):
        d = Despesa("Mercado", 250, "2026-11-02", "Alimentacao", id=2).to_dict()
        self.assertEqual(d, {
            "id": 2, "tipo": "Despesa", "descricao": "Mercado",
            "valor": 250.0, "data": "2026-11-02", "categoria": "Alimentacao",
        })

    def test_criar_lancamento_a_partir_de_texto(self):
        # linha do TXT: 1;Receita;Salario;3000.00;2026-11-01;Trabalho
        campos = "1;Receita;Salario;3000.00;2026-11-01;Trabalho".split(";")
        l = criar_lancamento(campos[1], campos[2], campos[3], campos[4],
                             campos[5], id=campos[0])
        self.assertIsInstance(l, Receita)
        self.assertEqual(l.id, 1)
        self.assertEqual(l.valor, 3000.0)

    def test_criar_lancamento_tipo_desconhecido(self):
        with self.assertRaises(LancamentoError):
            criar_lancamento("Outro", "x", 1, "2026-01-01", "c")

    def test_ida_e_volta(self):
        original = Despesa("Mercado", 250.5, "2026-11-02", "Alimentacao", id=2)
        d = original.to_dict()
        copia = criar_lancamento(d["tipo"], d["descricao"], d["valor"],
                                 d["data"], d["categoria"], id=d["id"])
        self.assertEqual(original, copia)

    def test_aceita_objeto_categoria(self):
        l = Receita("x", 10, "2026-11-01", Categoria("Trabalho"))
        self.assertEqual(l.categoria, "Trabalho")

    def test_str(self):
        l = Receita("Salario", 3000, "2026-11-01", "Trabalho", id=1)
        self.assertIn("01/11/2026", str(l))
        self.assertIn("R$ 3000.00", str(l))


class TestCategoria(unittest.TestCase):
    def test_nome_valido_e_igualdade(self):
        self.assertEqual(Categoria(" Lazer "), Categoria("lazer"))
        self.assertEqual(str(Categoria("Lazer")), "Lazer")

    def test_nome_vazio(self):
        with self.assertRaises(DescricaoInvalidaError):
            Categoria("  ")


if __name__ == "__main__":
    unittest.main()
