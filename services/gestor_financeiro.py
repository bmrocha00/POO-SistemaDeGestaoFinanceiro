"""Classe GestorFinanceiro: regras de negócio (cadastro, saldo, filtros e relatórios)."""
from models import Lancamento, criar_lancamento
from datetime import date, datetime


class GestorFinanceiro:
    """Gerencia as movimentações financeiras."""
    def __init__(self, gerenciador=None):
        """Inicializa o gestor e carrega os lançamentos salvos."""

        self._lancamentos = []             # lançamentos em memória (objetos Receita/Despesa)
        self._proximo_id = 1               # próximo id livre para novos lançamentos
        self._gerenciador = gerenciador    # GerenciadorArquivos usado para salvar no TXT (opcional)

        if self._gerenciador is not None:
            registros = self._gerenciador.carregar_lancamentos()

            for registro in registros:
                lancamento = criar_lancamento(
                    registro["tipo"],
                    registro["descricao"],
                    registro["valor"],
                    registro["data"],
                    registro["categoria"],
                    id=registro["id"]
                )

                self._lancamentos.append(lancamento)

            self._proximo_id = max(
                (l.id for l in self._lancamentos),
                default=0
            ) + 1

    def cadastrar_lancamento(self, lancamento):
        """Cadastra e salva uma movimentação."""

        if not isinstance(lancamento, Lancamento):
            raise TypeError("O objeto deve ser um lançamento.")

        id_anterior = lancamento.id

        if lancamento.id is None:
            lancamento.id = self._proximo_id

        if any(l.id == lancamento.id for l in self._lancamentos):
            raise ValueError("Já existe um lançamento com esse ID.")

        try:
            if self._gerenciador is not None:
                self._gerenciador.salvar_lancamento(
                    lancamento.to_dict()
                )
        except Exception:
            lancamento.id = id_anterior
            raise

        self._lancamentos.append(lancamento)

        self._proximo_id = max(
            self._proximo_id, lancamento.id + 1
        )

        return lancamento

    def listar_lancamentos(self):
        """Retorna os lançamentos cadastrados."""
        return self._lancamentos.copy()
    
    def calcular_saldo(self):
        """Calcula o saldo total das movimentações."""

        saldo = 0

        for lancamento in self._lancamentos:
            saldo += lancamento.calcular_impacto()

        return round(saldo, 2)
    
    def remover_lancamento(self, id_lancamento):
        """Remove um lançamento da memória e do TXT."""

        for lancamento in self._lancamentos:

            if lancamento.id == id_lancamento:

                if self._gerenciador is not None:
                    removido = self._gerenciador.excluir_lancamento(
                        id_lancamento
                    )

                    if not removido:
                        raise ValueError(
                            "Lançamento não encontrado no TXT."
                        )

                self._lancamentos.remove(lancamento)
                return lancamento

        raise ValueError("Lançamento não encontrado.")
    
    def editar_lancamento(self, id_lancamento, **alteracoes):
        """Edita um lançamento na memória e no TXT."""

        campos_permitidos = {
            "descricao", "valor", "data", "categoria"
        }

        if not alteracoes:
            raise ValueError("Nenhuma alteração informada.")

        if not set(alteracoes).issubset(campos_permitidos):
            raise ValueError("Campo de edição inválido.")

        for lancamento in self._lancamentos:

            if lancamento.id == id_lancamento:

                antigos = {
                    campo: getattr(lancamento, campo)
                    for campo in alteracoes
                }

                try:
                    for campo, novo_valor in alteracoes.items():
                        setattr(lancamento, campo, novo_valor)

                    if self._gerenciador is not None:

                        dados = lancamento.to_dict()

                        novos_dados = {
                            campo: dados[campo]
                            for campo in alteracoes
                        }

                        atualizado = self._gerenciador.atualizar_lancamento(
                            id_lancamento,
                            novos_dados
                        )

                        if not atualizado:
                            raise ValueError(
                                "Lançamento não encontrado no TXT."
                            )

                except Exception:
                    for campo, valor_antigo in antigos.items():
                        setattr(lancamento, campo, valor_antigo)
                    raise

                return lancamento

        raise ValueError("Lançamento não encontrado.")
    
    def filtrar_por_categoria(self, categoria):
        """Retorna os lançamentos de uma categoria."""

        if not isinstance(categoria, str) or not categoria.strip():
            raise ValueError("Categoria inválida.")

        return [
            lancamento
            for lancamento in self._lancamentos
            if lancamento.categoria.lower() == categoria.strip().lower()
        ]

    def filtrar_por_data(self, data_inicial=None, data_final=None):
        """Retorna os lançamentos dentro de um período."""

        def converter_data(valor):
            """Converte None, date, datetime ou texto AAAA-MM-DD em date (ValueError se inválida)."""
            if valor is None:
                return None

            if isinstance(valor, datetime):
                return valor.date()

            if isinstance(valor, date):
                return valor

            if isinstance(valor, str):
                try:
                    return datetime.strptime(
                        valor, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    pass

            raise ValueError("Data inválida. Use AAAA-MM-DD.")

        inicio = converter_data(data_inicial)
        fim = converter_data(data_final)

        if inicio is not None and fim is not None and inicio > fim:
            raise ValueError("Data inicial maior que a final.")

        return [
            lancamento
            for lancamento in self._lancamentos
            if (inicio is None or lancamento.data >= inicio)
            and (fim is None or lancamento.data <= fim)
        ]
    
    def gerar_relatorio_mensal(self, ano, mes):
        """Gera um relatório financeiro de um mês específico."""

        if (type(ano) is not int or type(mes) is not int
                or ano < 1 or ano > 9999 or mes < 1 or mes > 12):
            raise ValueError("Ano ou mês inválido.")

        total_receitas = 0
        total_despesas = 0
        quantidade = 0

        for lancamento in self._lancamentos:

            if lancamento.data.year == ano and lancamento.data.month == mes:

                impacto = lancamento.calcular_impacto()

                if impacto > 0:
                    total_receitas += impacto
                else:
                    total_despesas += abs(impacto)

                quantidade += 1

        saldo = total_receitas - total_despesas

        return {
            "ano": ano,
            "mes": mes,
            "total_receitas": round(total_receitas, 2),
            "total_despesas": round(total_despesas, 2),
            "saldo": round(saldo, 2),
            "quantidade_lancamentos": quantidade
        }