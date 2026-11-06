"""Pacote de modelos: Lancamento, Receita, Despesa e Categoria."""
from models.lancamento import (
    Lancamento,
    LancamentoError,
    ValorInvalidoError,
    DataInvalidaError,
    DescricaoInvalidaError,
)
from models.receita import Receita
from models.despesa import Despesa
from models.categoria import Categoria

_TIPOS = {"receita": Receita, "despesa": Despesa}


def criar_lancamento(tipo, descricao, valor, data, categoria, id=None):
    """Fábrica usada pela persistência para reconstruir objetos do TXT.

    Exemplo: criar_lancamento("Receita", "Salario", "3000.00",
                              "2026-11-01", "Trabalho", id=1)
    """
    classe = _TIPOS.get(str(tipo).strip().lower())
    if classe is None:
        raise LancamentoError(f"Tipo de lançamento desconhecido: {tipo!r}")
    return classe(descricao, valor, data, categoria, id=id)


__all__ = [
    "Lancamento", "Receita", "Despesa", "Categoria", "criar_lancamento",
    "LancamentoError", "ValorInvalidoError", "DataInvalidaError",
    "DescricaoInvalidaError",
]
