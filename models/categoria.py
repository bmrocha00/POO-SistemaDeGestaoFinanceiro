"""Classe Categoria: organiza lançamentos por tipo."""
from models.lancamento import DescricaoInvalidaError


class Categoria:
    """Categoria de movimentações (Alimentacao, Transporte, Lazer...)."""

    def __init__(self, nome):
        """Cria a categoria validando o nome."""
        self.nome = nome  # nome da categoria (validado pelo setter)

    @property
    def nome(self):
        """Nome da categoria."""
        return self._nome

    @nome.setter
    def nome(self, novo):
        """Define o nome (texto não vazio; espaços das pontas são removidos)."""
        if not isinstance(novo, str) or not novo.strip():
            raise DescricaoInvalidaError("O nome da categoria não pode ser vazio.")
        self._nome = novo.strip()

    def __str__(self):
        """Retorna o nome da categoria."""
        return self._nome

    def __repr__(self):
        """Representação técnica do objeto, útil para depuração."""
        return f"Categoria({self._nome!r})"

    def __eq__(self, outro):
        """Categorias são iguais quando o nome é igual, ignorando maiúsculas e minúsculas."""
        if isinstance(outro, Categoria):
            return self._nome.lower() == outro._nome.lower()
        return NotImplemented

    def __hash__(self):
        """Hash consistente com __eq__ (ignora maiúsculas e minúsculas)."""
        return hash(self._nome.lower())