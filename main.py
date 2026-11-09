"""Sistema de Gestão Financeira - interface de terminal (Integrante 4).

Execute na raiz do projeto:  python main.py

Usa o GestorFinanceiro (Integrante 3):
    cadastrar_lancamento(lancamento)      remover_lancamento(id)
    editar_lancamento(id, **campos)       calcular_saldo()
    listar_lancamentos()                  filtrar_por_categoria(nome)
    gerar_relatorio_mensal(ano, mes)      -> dict
"""
import os
import sys
from datetime import date

from database.gerenciador_arquivos import GerenciadorArquivos, ErroPersistencia
from models import Receita, Despesa, LancamentoError, criar_lancamento

PASTA_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

MENU = """
========== GESTÃO FINANCEIRA ==========
1 - Cadastrar receita
2 - Cadastrar despesa
3 - Listar movimentações
4 - Editar movimentação
5 - Excluir movimentação
6 - Consultar saldo
7 - Relatórios financeiros
0 - Sair
======================================="""


# ---------------------------------------------------------------------------
# Integração: gestor (Integrante 3) + persistência TXT (Integrante 2).
# O GestorFinanceiro guarda tudo em memória; o GestorPersistente carrega os
# dados do TXT ao iniciar e grava cada alteração depois que o gestor a valida.
# ---------------------------------------------------------------------------
class GestorPersistente:
    """Envolve o GestorFinanceiro e espelha cada alteração nos arquivos TXT."""

    def __init__(self, gestor, arquivos):
        self._gestor = gestor
        self._arquivos = arquivos
        self.avisos = []
        self._carregar()

    def _carregar(self):
        for reg in self._arquivos.carregar_lancamentos():
            try:
                lanc = criar_lancamento(reg["tipo"], reg["descricao"], reg["valor"],
                                        reg["data"], reg["categoria"], id=reg["id"])
                self._gestor.cadastrar_lancamento(lanc)
            except ValueError as erro:
                self.avisos.append(f"Registro {reg['id']} ignorado: {erro}")
        self.avisos = list(self._arquivos.avisos) + self.avisos

    def cadastrar_lancamento(self, lanc):
        self._gestor.cadastrar_lancamento(lanc)
        try:
            self._arquivos.salvar_lancamento(lanc.to_dict())
            self._arquivos.salvar_categoria(lanc.categoria)
        except Exception:
            self._gestor.remover_lancamento(lanc.id)  # memória e arquivo não divergem
            raise
        return lanc

    def editar_lancamento(self, id_, **alteracoes):
        lanc = self._gestor.editar_lancamento(id_, **alteracoes)
        dados = lanc.to_dict()
        dados.pop("id")
        self._arquivos.atualizar_lancamento(id_, dados)
        if "categoria" in alteracoes:
            self._arquivos.salvar_categoria(lanc.categoria)
        return lanc

    def remover_lancamento(self, id_):
        lanc = self._gestor.remover_lancamento(id_)
        self._arquivos.excluir_lancamento(id_)
        return lanc

    def __getattr__(self, nome):  # listar, saldo, filtros e relatório vão direto
        return getattr(self._gestor, nome)


def criar_gestor(pasta=PASTA_DADOS):
    from services.gestor_financeiro import GestorFinanceiro

    return GestorPersistente(GestorFinanceiro(), GerenciadorArquivos(pasta))


# ---------------------------------------------------------------------------
# Leitura e validação de entradas
# ---------------------------------------------------------------------------
def _validar(campo, valor):
    """Valida e normaliza um campo usando os setters do modelo (Integrante 1)."""
    molde = Receita("x", 1, date.today(), "x")
    setattr(molde, campo, valor)
    return getattr(molde, campo)


def ler_campo(mensagem, campo, opcional=False, padrao=None):
    """Pergunta até receber um valor válido para o campo do lançamento.

    opcional=True: Enter devolve None (usado na edição para manter o valor).
    padrao: texto usado quando o usuário só aperta Enter.
    """
    while True:
        texto = input(mensagem).strip()
        if texto == "":
            if opcional:
                return None
            if padrao is not None:
                texto = padrao
        try:
            return _validar(campo, texto)
        except LancamentoError as erro:
            print(f"  Entrada inválida: {erro}")


def ler_inteiro(mensagem, minimo=None, maximo=None):
    while True:
        texto = input(mensagem).strip()
        try:
            numero = int(texto)
        except ValueError:
            print("  Digite um número inteiro.")
            continue
        if minimo is not None and numero < minimo:
            print(f"  O valor mínimo é {minimo}.")
        elif maximo is not None and numero > maximo:
            print(f"  O valor máximo é {maximo}.")
        else:
            return numero


def _moeda(valor):
    return f"R$ {valor:.2f}"


def _buscar(gestor, id_):
    for lanc in gestor.listar_lancamentos():
        if lanc.id == id_:
            return lanc
    return None


# ---------------------------------------------------------------------------
# Ações do menu
# ---------------------------------------------------------------------------
def cadastrar(gestor, classe):
    print(f"\n--- Cadastrar {classe.__name__.lower()} ---")
    descricao = ler_campo("Descrição: ", "descricao")
    valor = ler_campo("Valor (ex.: 150,50): ", "valor")
    data = ler_campo("Data AAAA-MM-DD [Enter = hoje]: ", "data",
                     padrao=date.today().isoformat())
    categoria = ler_campo("Categoria: ", "categoria")
    gestor.cadastrar_lancamento(classe(descricao, valor, data, categoria))
    salvar(gestor)
    print(f"{classe.__name__} cadastrada com sucesso!")


def mostrar(lancamentos):
    if not lancamentos:
        print("Nenhuma movimentação encontrada.")
        return
    for lanc in lancamentos:
        print(lanc)
    total = sum(l.calcular_impacto() for l in lancamentos)
    print(f"\n{len(lancamentos)} movimentação(ões) | impacto total: {_moeda(total)}")


def listar(gestor):
    print("\n--- Listar movimentações ---")
    print("1 - Todas\n2 - Filtrar por categoria")
    if ler_inteiro("Opção: ", 1, 2) == 2:
        nome = input("Categoria: ").strip()
        mostrar(gestor.filtrar_por_categoria(nome))
    else:
        mostrar(gestor.listar_lancamentos())


def editar(gestor):
    print("\n--- Editar movimentação ---")
    id_ = ler_inteiro("ID da movimentação: ", 0)
    atual = _buscar(gestor, id_)
    if atual is None:
        print(f"Nenhuma movimentação com ID {id_}.")
        return
    print(atual)
    print("Pressione Enter para manter o valor atual.")
    campos = [
        ("descricao", "Descrição", atual.descricao),
        ("valor", "Valor", f"{atual.valor:.2f}"),
        ("data", "Data AAAA-MM-DD", atual.data.isoformat()),
        ("categoria", "Categoria", atual.categoria),
    ]
    novos = {}
    for campo, rotulo, atual_txt in campos:
        novo = ler_campo(f"{rotulo} [{atual_txt}]: ", campo, opcional=True)
        if novo is not None:
            novos[campo] = novo
    if not novos:
        print("Nada foi alterado.")
        return
    gestor.editar_lancamento(id_, **novos)
    salvar(gestor)
    print("Movimentação atualizada!")


def excluir(gestor):
    print("\n--- Excluir movimentação ---")
    id_ = ler_inteiro("ID da movimentação: ", 0)
    atual = _buscar(gestor, id_)
    if atual is None:
        print(f"Nenhuma movimentação com ID {id_}.")
        return
    print(atual)
    if input("Confirmar exclusão? (s/n): ").strip().lower() != "s":
        print("Exclusão cancelada.")
        return
    gestor.remover_lancamento(id_)
    salvar(gestor)
    print("Movimentação excluída!")


def consultar_saldo(gestor):
    print(f"\nSaldo atual: {_moeda(gestor.calcular_saldo())}")


def relatorio(gestor):
    print("\n--- Relatório mensal ---")
    ano = ler_inteiro("Ano (ex.: 2026): ", 1, 9999)
    mes = ler_inteiro("Mês (1-12): ", 1, 12)
    resultado = gestor.gerar_relatorio_mensal(ano, mes)
    print(f"\nRelatório de {mes:02d}/{ano}")
    if isinstance(resultado, dict):
        for chave, valor in resultado.items():
            if chave.startswith(("total", "saldo")):
                valor = _moeda(valor)
            print(f"  {chave.replace('_', ' ').capitalize()}: {valor}")
    else:
        print(resultado)


ACOES = {
    "1": lambda g: cadastrar(g, Receita),
    "2": lambda g: cadastrar(g, Despesa),
    "3": listar,
    "4": editar,
    "5": excluir,
    "6": consultar_saldo,
    "7": relatorio,
}


# ---------------------------------------------------------------------------
# Laço principal
# ---------------------------------------------------------------------------
def executar(gestor):
    while True:
        print(MENU)
        try:
            opcao = input("Escolha uma opção: ").strip()
            if opcao == "0":
                print("Até logo!")
                return
            acao = ACOES.get(opcao)
            if acao is None:
                print("Opção inválida. Digite um número de 0 a 7.")
                continue
            acao(gestor)
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando o programa.")
            return
        except ValueError as erro:  # inclui LancamentoError
            print(f"Erro: {erro}")
        except (OSError, ErroPersistencia) as erro:
            print(f"Erro de arquivo: {erro}")
        except Exception as erro:  # rede de segurança: o menu não pode cair
            print(f"Erro inesperado ({type(erro).__name__}): {erro}")


def main():
    try:
        gestor = criar_gestor()
    except Exception as erro:
        print(f"Não foi possível iniciar o sistema: {erro}")
        sys.exit(1)
    for aviso in gestor.avisos:
        print(f"Aviso: {aviso}")
    print("Sistema iniciado.")
    executar(gestor)


if __name__ == "__main__":
    main()