"""Classe GerenciadorArquivos: Manipula o banco de dados (TXT)"""

import os
import csv

# Ordem das colunas em lancamentos.txt (igual ao to_dict() do Lancamento)
CAMPOS_LANCAMENTO = ["id", "tipo", "descricao", "valor", "data", "categoria"]

class ErroPersistencia(Exception):
    """Erro para quando a leitura ou escrita dos arquivos falha"""

class GerenciadorArquivos():
    """Responsável pela persistência dos dados do sistema.

    Lê e grava lançamentos e categorias em arquivos TXT (delimitados por ';'),
    trabalhando com dicionários.
    """
    def __init__(self, pasta_dados = "data"):
        """Guarda a pasta e o nome dos arquivos.

        :param pasta_dados: pasta onde os TXT são guardados (criada se não existir).
        """
        self.__pasta_dados = pasta_dados                    # pasta onde ficam os arquivos TXT
        self.__arquivo_lancamentos = "lancamentos.txt"      # nome do arquivo dos lançamentos
        self.__arquivo_categorias = "categorias.txt"        # nome do arquivo das categorias
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

    @property
    def caminho_categorias(self):
        """Retorna o caminho completo de categorias.txt"""
        return os.path.join(self.__pasta_dados, self.__arquivo_categorias)

    def __garantir_arquivos(self):
        """Cria a pasta e os arquivos TXT caso não existam"""
        try:
            os.makedirs(self.__pasta_dados, exist_ok=True)
            for caminho in (self.caminho_lancamentos, self.caminho_categorias):
                if not os.path.exists(caminho):
                    with open(caminho, "w", encoding="utf-8"):
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

    def gerar_proximo_id(self):
        """Retorna o próximo id livre: maior id existente + 1 (ou 1 se não há registros)."""
        lancamentos = self.carregar_lancamentos()
        if not lancamentos:
            return 1
        return max(r["id"] for r in lancamentos) + 1

    def carregar_categorias(self):
        """Lê categorias.txt e devolve a lista de categorias (uma por linha)."""
        try:
            with open(self.caminho_categorias, "r", encoding="utf-8") as arquivo:
                return [linha.strip() for linha in arquivo if linha.strip()]
        except FileNotFoundError:
            self.__garantir_arquivos()              # recria vazio
            return []
        except OSError as erro:
            raise ErroPersistencia(f"Nao foi possivel ler as categorias: {erro}")

    def salvar_categoria(self, nome):
        """Grava uma nova categoria. Retorna True se gravou, False se já existia
        (a comparação ignora maiúsculas e minúsculas)."""
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("A categoria deve ser um texto nao vazio.")
        nome = " ".join(nome.split())               # tira espaços/quebras sobrando

        existentes = [c.lower() for c in self.carregar_categorias()]
        if nome.lower() in existentes:
            return False
        try:
            with open(self.caminho_categorias, "a", encoding="utf-8") as arquivo:
                arquivo.write(nome + "\n")
        except OSError as erro:
            raise ErroPersistencia(f"Nao foi possivel salvar a categoria: {erro}")
        return True