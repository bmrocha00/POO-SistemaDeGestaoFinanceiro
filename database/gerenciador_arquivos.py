"""Classe GerenciadorArquivos: Manipula o banco de dados (TXT)"""

import os
import csv

# Ordem das colunas em lancamentos.txt (igual ao to_dict() do Lancamento)
CAMPOS_LANCAMENTO = ["id", "tipo", "descricao", "valor", "data", "categoria"]

class ErroPersistencia(Exception):
    """Erro para quando a leitura ou escrita dos arquivos falha"""

class GerenciadorArquivos():
    """Responsável pela persistência dos dados do sistema.

    Lê e grava os lançamentos em arquivo TXT (delimitado por ';'),
    trabalhando com dicionários.
    """
    def __init__(self, pasta_dados = "data"):
        """Guarda a pasta e o nome dos arquivos.

        :param pasta_dados: pasta onde o TXT é guardado (criada se não existir).
        """
        self.__pasta_dados = pasta_dados                    # pasta onde fica o arquivo TXT
        self.__arquivo_lancamentos = "lancamentos.txt"      # nome do arquivo dos lançamentos
        self.__avisos = []                                  # linhas ignoradas na última leitura
        self.__garantir_arquivos()

    @property
    def pasta_dados(self):
        """Retorna o nome da pasta que os arquivos estão armazenados"""
        return self.__pasta_dados
    
    @pasta_dados.setter
    def pasta_dados(self, pasta):
        """Permite a mudança de pasta em que os arquivos vão ser armazenados (Str não vazia)"""
        if not isinstance(pasta, str) or not pasta.strip():
            raise ValueError("Nome da pasta deve ser uma string nao vazia")
        self.__pasta_dados = pasta.strip()
        self.__garantir_arquivos()

    @property
    def caminho_lancamentos(self):
        """Retorna o caminho completo de lancamentos.txt"""
        return os.path.join(self.__pasta_dados, self.__arquivo_lancamentos)

    def __garantir_arquivos(self):
        """Cria a pasta e o arquivo TXT dos lançamentos caso não existam"""
        try:
            os.makedirs(self.__pasta_dados, exist_ok=True)
            if not os.path.exists(self.caminho_lancamentos):
                with open(self.caminho_lancamentos, "w", encoding="utf-8"):
                    pass
        except OSError as erro:
            raise ErroPersistencia(f"Nao foi possivel preparar os arquivos: {erro}")

    def __dict_to_linha(self, lancamento):
        """Converte um dict em lista, ordem das colunas"""
        if not isinstance(lancamento, dict):
            raise ValueError("O lancamento tem que ser um dicionario")
        faltando = [c for c in CAMPOS_LANCAMENTO if c not in lancamento]
        if faltando:
            raise ValueError(f"Campos faltando no lancamento: {faltando}")
        try:
            valor = f"{float(lancamento['valor']):.2f}"
        except (TypeError, ValueError):
            raise ValueError(f"Valor invalido: {lancamento['valor']!r}")
        return [lancamento["id"], lancamento["tipo"], lancamento["descricao"], valor, lancamento["data"], lancamento["categoria"],]

    def salvar_lancamento(self, lancamento):
        """Adiciona o lançamento no lancamentos.txt"""
        linha = self.__dict_to_linha(lancamento)
        try:
            with open(self.caminho_lancamentos, "a", newline="", encoding="utf-8") as arquivo:
                csv.writer(arquivo, delimiter=";").writerow(linha)
        except OSError as erro:
            raise ErroPersistencia(f"Nao foi possivel salvar o lancamento: {erro}")

    @property
    def avisos(self):
        """Mensagens sobre linhas ignoradas na última leitura"""
        return list(self.__avisos)

    def carregar_lancamentos(self):
        """Lê lancamentos.txt e devolve uma lista de dicts"""
        lancamentos = []
        self.__avisos = []
        try: 
            with open(self.caminho_lancamentos, "r", newline="", encoding="utf-8") as arquivo:
                leitor = csv.reader(arquivo, delimiter=";")
                for numero, linha in enumerate(leitor, start=1):
                    if not linha:           #linha em branco
                        continue
                    if len(linha) != len(CAMPOS_LANCAMENTO):
                        self.__avisos.append(f"Linha {numero} ignorada: colunas incorretas")
                        continue
                    registro = dict(zip(CAMPOS_LANCAMENTO, linha))
                    try:
                        registro["id"] = int(registro["id"])
                        registro["valor"] = float(registro["valor"])
                    except ValueError:
                        self.__avisos.append(f"Linha {numero} ignorada: id ou valor inválido.")
                        continue
                    lancamentos.append(registro)
        except FileNotFoundError:
            self.__garantir_arquivos()              
        except OSError as erro:
            raise ErroPersistencia(f"Não foi possível ler os lançamentos: {erro}")
        return lancamentos

    def __reescrever_lancamentos(self, lista):
        """Substitui todo o conteúdo de lancamentos.txt pela lista recebida."""
        linhas = [self.__dict_to_linha(registro) for registro in lista]

        caminho = self.caminho_lancamentos
        temporario = caminho + ".tmp"
        try:
            with open(temporario, "w", newline="", encoding="utf-8") as arquivo:
                csv.writer(arquivo, delimiter=";").writerows(linhas)
            os.replace(temporario, caminho)
        except OSError as erro:
            raise ErroPersistencia(f"Não foi possível atualizar os lançamentos: {erro}")

    def atualizar_lancamento(self, id_lancamento, novos_dados):
        """Altera campos de um lançamento. Retorna True se achou, False se não."""
        if not isinstance(novos_dados, dict):
            raise ValueError("Os novos dados devem ser um dicionário.")

        lista = self.carregar_lancamentos()
        for registro in lista:
            if registro["id"] == id_lancamento:
                novos_dados = {c: v for c, v in novos_dados.items() if c != "id"}
                registro.update(novos_dados)
                self.__reescrever_lancamentos(lista)
                return True
        return False

    def excluir_lancamento(self, id_lancamento):
        """Remove um lançamento pelo id. Retorna True se removeu, False se não achou."""
        lista = self.carregar_lancamentos()
        restantes = [r for r in lista if r["id"] != id_lancamento]

        if len(restantes) == len(lista):      
            return False
        self.__reescrever_lancamentos(restantes)
        return True