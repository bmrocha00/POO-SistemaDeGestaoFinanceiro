"""Classe Receita: lançamento de entrada de dinheiro."""
from models.lancamento import Lancamento


class Receita(Lancamento):
    """Entrada de dinheiro (salário, bolsa, venda...)."""

    @property
    def tipo(self):
        """Nome do tipo, usado na persistência."""
        return "Receita"

    def calcular_impacto(self):
        """Impacto positivo no saldo."""
        return self.valor