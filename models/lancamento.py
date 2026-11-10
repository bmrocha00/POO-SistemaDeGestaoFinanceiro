"""Classe abstrata Lancamento e exceções de validação."""
from abc import ABC, abstractmethod
from datetime import date, datetime


class LancamentoError(ValueError):
    """Erro base para dados inválidos de um lançamento."""


class ValorInvalidoError(LancamentoError):
    """Valor não numérico, zero ou negativo."""


class DataInvalidaError(LancamentoError):
    """Data fora do formato AAAA-MM-DD ou inexistente."""


class DescricaoInvalidaError(LancamentoError):
    """Descrição ou categoria vazia."""


class Lancamento(ABC):
    """Movimentação financeira genérica (abstração).

    Atributos: id, descricao, valor, data e categoria.
    O valor é sempre positivo; o sinal (entrada/saída) é dado por
    calcular_impacto(), implementado em cada subclasse.
    """

    FORMATO_DATA = "%Y-%m-%d"  # formato aceito e gravado para as datas (AAAA-MM-DD)

    def __init__(self, descricao, valor, data, categoria, id=None):
        """Cria o lançamento validando cada campo pelos setters (o id é opcional)."""
        self._id = None              # identificador (definido pelo setter abaixo)
        self.id = id                 # id do lançamento; None até ser cadastrado
        self.descricao = descricao   # texto que descreve a movimentação
        self.valor = valor           # valor positivo; o sinal vem de calcular_impacto()
        self.data = data             # data da movimentação (objeto date)
        self.categoria = categoria   # nome da categoria (ex.: Alimentacao)

    # ---------- id ----------
    @property
    def id(self):
        """Identificador do lançamento (None até ser cadastrado)."""
        return self._id

    @id.setter
    def id(self, novo_id):
        """Define o id (inteiro não negativo ou None)."""
        if novo_id is None:
            self._id = None
            return
        try:
            novo_id = int(novo_id)
        except (TypeError, ValueError):
            raise LancamentoError(f"ID inválido: {novo_id!r}")
        if novo_id < 0:
            raise LancamentoError("O ID não pode ser negativo.")
        self._id = novo_id

    # ---------- descricao ----------
    @property
    def descricao(self):
        """Descrição do lançamento."""
        return self._descricao

    @descricao.setter
    def descricao(self, nova):
        """Define a descrição (texto não vazio)."""
        if not isinstance(nova, str) or not nova.strip():
            raise DescricaoInvalidaError("A descrição não pode ser vazia.")
        self._descricao = nova.strip()

    # ---------- valor ----------
    @property
    def valor(self):
        """Valor do lançamento (sempre positivo, com 2 casas decimais)."""
        return self._valor

    @valor.setter
    def valor(self, novo):
        """Define o valor (aceita vírgula; deve ser maior que zero)."""
        if isinstance(novo, bool):
            raise ValorInvalidoError("Valor inválido.")
        if isinstance(novo, str):
            novo = novo.strip().replace(",", ".")
        try:
            novo = round(float(novo), 2)
        except (TypeError, ValueError):
            raise ValorInvalidoError(f"Valor inválido: {novo!r}")
        if novo != novo or novo in (float("inf"), float("-inf")):
            raise ValorInvalidoError("Valor inválido.")
        if novo <= 0:
            raise ValorInvalidoError("O valor deve ser maior que zero.")
        self._valor = novo

    # ---------- data ----------
    @property
    def data(self):
        """Data do lançamento (objeto date)."""
        return self._data

    @data.setter
    def data(self, nova):
        """Define a data (objeto date ou texto no formato AAAA-MM-DD)."""
        if isinstance(nova, datetime):
            nova = nova.date()
        if isinstance(nova, date):
            self._data = nova
            return
        if not isinstance(nova, str):
            raise DataInvalidaError(f"Data inválida: {nova!r}")
        try:
            self._data = datetime.strptime(nova.strip(), self.FORMATO_DATA).date()
        except ValueError:
            raise DataInvalidaError(
                f"Data inválida: {nova!r}. Use o formato AAAA-MM-DD."
            )

    # ---------- categoria ----------
    @property
    def categoria(self):
        """Nome da categoria do lançamento."""
        return self._categoria

    @categoria.setter
    def categoria(self, nova):
        """Define a categoria (texto ou objeto Categoria; não pode ser vazia)."""
        nova = str(getattr(nova, "nome", nova)).strip()
        if not nova:
            raise DescricaoInvalidaError("A categoria não pode ser vazia.")
        self._categoria = nova

    # ---------- polimorfismo ----------
    @property
    @abstractmethod
    def tipo(self):
        """Nome do tipo ('Receita' ou 'Despesa'), usado na persistência."""

    @abstractmethod
    def calcular_impacto(self):
        """Efeito do lançamento no saldo (positivo ou negativo)."""

    # ---------- utilitários de integração ----------
    def to_dict(self):
        """Dicionário com todos os campos, pronto para o TXT."""
        return {
            "id": self.id,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "valor": self.valor,
            "data": self.data.strftime(self.FORMATO_DATA),
            "categoria": self.categoria,
        }

    def __str__(self):
        """Texto de exibição: [id] data | tipo | descrição (categoria) | valor."""
        return (
            f"[{self.id}] {self.data.strftime('%d/%m/%Y')} | {self.tipo:<7} | "
            f"{self.descricao} ({self.categoria}) | R$ {self.valor:.2f}"
        )

    def __repr__(self):
        """Representação técnica do objeto, útil para depuração."""
        return (
            f"{type(self).__name__}(id={self.id!r}, descricao={self.descricao!r}, "
            f"valor={self.valor!r}, data={self.data.isoformat()!r}, "
            f"categoria={self.categoria!r})"
        )

    def __eq__(self, outro):
        """Dois lançamentos são iguais quando todos os campos (to_dict) são iguais."""
        if not isinstance(outro, Lancamento):
            return NotImplemented
        return self.to_dict() == outro.to_dict()