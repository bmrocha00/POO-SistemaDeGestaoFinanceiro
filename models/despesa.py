"""Classe Despesa: lançamento de saída de dinheiro."""
from models.lancamento import Lancamento


class Despesa(Lancamento):
    """Saída de dinheiro (compras, contas, transporte...)."""

    @property
    def tipo(self):
        return "Despesa"

    def calcular_impacto(self):
        """Impacto negativo no saldo."""
        return -self.valor
