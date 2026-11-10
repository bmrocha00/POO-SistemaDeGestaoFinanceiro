# Sistema de Gestão Financeira

Sistema de gestão financeira pessoal desenvolvido em Python para a disciplina de Programação Orientada a Objetos (Profa. Luiza Bernardes Real).

O programa permite registrar receitas e despesas, organizá-las por categoria, consultar, editar e excluir lançamentos, acompanhar o saldo e gerar o relatório de um mês. Os dados são gravados em um arquivo TXT e recarregados sempre que o programa é iniciado, de modo que nada se perde ao fechá-lo.

A interface é feita no terminal. A prioridade do projeto foi a qualidade da modelagem e a aplicação correta dos conceitos de POO, e não a complexidade visual.

## Execução

É necessário ter o Python 3 instalado. O projeto usa apenas a biblioteca padrão, portanto não há dependências a instalar.

Na pasta raiz do projeto (a que contém o `main.py`):

```
python main.py
```

O menu principal oferece as seguintes opções:

```
1 - Cadastrar receita
2 - Cadastrar despesa
3 - Listar movimentações
4 - Editar movimentação
5 - Excluir movimentação
6 - Consultar saldo
7 - Relatórios financeiros
0 - Sair
```

Observações sobre o uso:

- Na data, pressionar Enter usa o dia atual. O formato aceito é `AAAA-MM-DD`.
- O valor pode ser informado com vírgula ou ponto (`150,50` ou `150.50`).
- Na edição, pressionar Enter em um campo mantém o valor atual.
- A exclusão exige confirmação.
- Entradas inválidas (valor negativo ou zero, data inexistente, campo vazio, opção fora do menu) são recusadas com uma mensagem explicativa, e o programa continua em execução.

## Testes

Para executar todos os testes automatizados:

```
python -m unittest discover tests
```

Para executar apenas um módulo, como o da persistência:

```
python -m unittest tests.test_gerenciador -v
```

Os testes que envolvem gravação usam pastas temporárias e, por isso, não alteram os dados reais em `data/`.

## Estrutura do projeto

```
main.py                        menu no terminal e integração dos módulos
models/
    lancamento.py              classe abstrata Lancamento e exceções de validação
    receita.py                 Receita
    despesa.py                 Despesa
    categoria.py               Categoria
services/
    gestor_financeiro.py       GestorFinanceiro: saldo, filtros e relatórios
database/
    gerenciador_arquivos.py    GerenciadorArquivos: leitura e gravação do TXT
data/
    lancamentos.txt            base de dados
tests/                         testes automatizados
```

O `main.py` interage com o `GestorFinanceiro`, que mantém a lista de lançamentos (`Receita` e `Despesa`) e utiliza o `GerenciadorArquivos` para carregar e gravar os dados em `data/lancamentos.txt`.

Cada camada tem uma responsabilidade bem definida. Os modelos não conhecem arquivos. O gerenciador de arquivos não conhece receitas nem despesas, pois trabalha apenas com dicionários. A conversão entre dicionários e objetos é feita pelo gestor.

## Conceitos de POO aplicados

**Abstração e classe abstrata.** `Lancamento` não pode ser instanciada diretamente. Ela define o que todo lançamento deve oferecer (`tipo` e `calcular_impacto()`), e cada subclasse completa essa definição.

**Herança.** `Receita` e `Despesa` herdam de `Lancamento`, reaproveitando seus atributos e validações. As exceções do projeto também seguem uma hierarquia: `ValorInvalidoError`, `DataInvalidaError` e `DescricaoInvalidaError` herdam de `LancamentoError`.

**Polimorfismo.** `calcular_impacto()` retorna o valor positivo em `Receita` e o negativo em `Despesa`. O gestor calcula o saldo somando os impactos de todos os lançamentos, sem verificar o tipo de cada um.

**Encapsulamento, getters e setters.** Os atributos são protegidos ou privados e só são acessados por meio de `@property` e `@setter`, que validam o dado antes de aceitá-lo. Assim, um lançamento nunca existe com valor zero ou data inválida.

**Composição.** O `GestorFinanceiro` contém a lista de lançamentos e uma instância de `GerenciadorArquivos`.

**Fábrica.** `criar_lancamento()` identifica, a partir do tipo gravado no arquivo ("Receita" ou "Despesa"), qual classe deve ser instanciada ao carregar os dados.

**Tratamento de erros.** Além das exceções de validação dos modelos, a persistência define `ErroPersistencia` para falhas de leitura e escrita. O menu captura esses erros e informa o usuário sem encerrar o programa.

## Persistência dos dados

Cada lançamento ocupa uma linha de `data/lancamentos.txt`, com os campos separados por ponto e vírgula:

```
1;Receita;Salario;3000.00;2026-11-01;Trabalho
2;Despesa;Mercado;250.50;2026-11-02;Alimentacao
```

Os campos, na ordem, são: id, tipo, descrição, valor, data e categoria. A leitura e a escrita usam o módulo `csv`, que trata corretamente textos contendo o próprio delimitador.

Decisões adotadas na persistência:

- Ao editar ou excluir, o arquivo é reescrito primeiro em um arquivo temporário, que depois substitui o original (`os.replace`). Se ocorrer uma falha durante a gravação, os dados anteriores permanecem íntegros.
- Linhas malformadas (número de colunas incorreto, `id` ou `valor` não numéricos) são ignoradas na leitura, em vez de interromper o programa. O motivo de cada descarte fica registrado em `GerenciadorArquivos.avisos`.
- Falhas ao abrir ou gravar o arquivo são lançadas como `ErroPersistencia`.

## Equipe

| Integrante | Responsabilidade |
|---|---|
| [Andrei Marques] | Modelagem: `Lancamento`, `Receita`, `Despesa` e `Categoria` |
| [Bernardo Mendes] | Persistência: `GerenciadorArquivos` e arquivo TXT |
| [Bruno Rios] | Regras de negócio: `GestorFinanceiro` e relatórios |
| [Vitor Emanuel] | Interface (`main.py`), integração e testes |
