"""Classe Categoria: organiza lançamentos por tipo."""
from models.lancamento import DescricaoInvalidaError


class Categoria:
    """Categoria de movimentações (Alimentacao, Transporte, Lazer...)."""

    def __init__(self, nome):
        self.nome = nome

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, novo):
        if not isinstance(novo, str) or not novo.strip():
            raise DescricaoInvalidaError("O nome da categoria não pode ser vazio.")
        self._nome = novo.strip()

    def __str__(self):
        return self._nome

    def __repr__(self):
        return f"Categoria({self._nome!r})"

    def __eq__(self, outro):
        if isinstance(outro, Categoria):
            return self._nome.lower() == outro._nome.lower()
        return NotImplemented

    def __hash__(self):
        return hash(self._nome.lower())
