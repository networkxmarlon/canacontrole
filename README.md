# CanaControle — perdas visíveis na colheita de cana

**Autor:** Marlon Gomes Rodrigues — RM576052  
**Modalidade:** trabalho individual  
**Contexto:** atividade de Python aplicada ao agronegócio (capítulos 3, 4, 5 e 6).

## Estado da entrega

O programa e os testes locais estão implementados. A conexão Oracle está no código,
mas **o teste em um banco real ainda precisa ser realizado pelo aluno**, após localizar
os dados de acesso. O **template oficial de repositório mencionado no enunciado ainda
não foi fornecido**: a organização abaixo é provisória e deve ser adaptada antes da entrega.
O modo `--demo` não substitui o requisito Oracle.

## Problema e proposta

Parte da cana pode permanecer no campo após a colheita. Sem registros por talhão,
fica difícil comparar operações e escolher onde investigar perdas primeiro.
O CanaControle registra a massa colhida e a massa remanescente encontrada em amostras
de área conhecida, estima perdas visíveis e organiza um relatório para inspeção.
Seu foco é o **setor de produção**, na operação de colheita de cana-de-açúcar.

O diferencial proposto é priorizar a inspeção pelo valor de cana perdida estimado,
separar os dados sintéticos dos observados e apresentar um cenário hipotético de
redução de perdas. Trata-se de uma proposta para esta atividade, sem alegação de
ineditismo comercial, IA ou comprovação de economia real.

## Funcionalidades

- Cadastrar, listar, editar e excluir colheitas.
- Validar tipos, datas, limites, origem e duplicatas antes da gravação.
- Exibir tabelas e relatórios em português, com unidades e números formatados.
- Exportar relatório TXT e dados JSON; importar JSON validando o lote inteiro.
- Gravar e consultar dados em Oracle com parâmetros vinculados, commit e rollback.
- Executar uma demonstração local em JSON quando escolhida explicitamente.

## Execução rápida da demonstração

Requer Python 3.10 ou mais recente. Na pasta que contém `main.py`:

No Windows, também é possível abrir **INICIAR_DEMO.bat** com dois cliques,
após extrair o ZIP. Ele mantém a janela aberta para que os erros possam ser lidos.
O iniciador **INICIAR_ORACLE.bat** abre o modo Oracle quando a configuração estiver pronta.

```bash
python main.py --demo
```

Selecione **8**, pressione Enter para usar `dados/exemplo_sintetico.json` e confirme
com `SIM`. Selecione **5** para o relatório. As opções **6** e **7** exportam TXT e
JSON para `resultados/`. Os exemplos são inventados e identificados como `sintetico`.

O modo demonstração persiste em `dados/demo_local.json`, gerado na primeira execução
e ignorado pelo Git. Não importe os mesmos exemplos duas vezes: duplicatas são rejeitadas.

## Execução com Oracle — requisito obrigatório

```bash
python -m pip install -r requirements.txt
```

Copie `config/oracle.exemplo.json` para `config/oracle.json` e preencha com os dados
reais do seu banco Oracle, local ou fornecido pela faculdade:

```json
{
  "usuario": "SEU_USUARIO_ORACLE",
  "dsn": "HOST_ORACLE:1521/NOME_DO_SERVICO"
}
```

Esse exemplo contém placeholders: não é um servidor disponível. A senha é solicitada
localmente e não aparece na tela. Também são aceitas as variáveis `CANA_ORACLE_USER`,
`CANA_ORACLE_DSN` e `CANA_ORACLE_PASSWORD`; variáveis de usuário/DSN prevalecem sobre o JSON.
O arquivo de configuração não deve conter senha.

No teste realizado pelo autor no Windows, foi usado Oracle AI Database 26ai Free,
serviço `localhost:1521/FREEPDB1` e usuário `canacontrole`. Para esse ambiente:

```json
{
  "usuario": "canacontrole",
  "dsn": "localhost:1521/FREEPDB1"
}
```

Esse endereço funciona no computador em que o banco foi instalado. Consulte
`PASSO_A_PASSO.md` para preparar o usuário local.

```bash
python main.py
```

Se a tabela não existir, use a opção **9** e confirme. O comando executa
`sql/criar_tabelas.sql` no usuário conectado. Não apaga tabelas existentes.
O usuário precisa de permissão para criar a tabela e de quota de armazenamento.
DDL no Oracle confirma transações implicitamente; a criação é uma operação separada.
Depois use as opções **1**, **2**, **3** e **4** para comprovar o CRUD no banco.

O driver funciona em modo Thin para conexão direta, sem Oracle Instant Client.
Se o banco da faculdade exigir wallet, autenticação especial ou modo Thick, a
configuração precisará ser adaptada às instruções desse ambiente. Não há troca
automática para demonstração quando Oracle falha.

## Dados e regras de entrada

Cada registro representa **uma operação de colheita por talhão e data**. Talhões são
normalizados para maiúsculas. Para este protótipo, operações no mesmo talhão e dia
devem ser consolidadas pelo usuário antes do cadastro.

| Campo | Significado | Validação |
|---|---|---|
| `id` | Identificador UUID | Gerado no cadastro; validado na importação |
| `talhao` | Nome ou código | Obrigatório, até 60 caracteres |
| `data_colheita` | Data da operação | Data válida, sem futuro; ISO ou DD/MM/AAAA |
| `area_ha` | Área efetivamente colhida da operação | Maior que 0, até 100.000 ha |
| `colhida_t` | Massa colhida nessa área | De 0 a 100.000.000 t |
| `amostra_m2` | Soma das áreas amostradas | Maior que 0, até 100.000 m² e até a área colhida |
| `perda_kg` | Soma da cana remanescente nas amostras | De 0 a 1.000.000 kg |
| `preco_t` | Preço de referência informado | De 0 a R$ 1.000.000/t; até 2 casas decimais |
| `origem` | Proveniência declarada | `observado` ou `sintetico` |
| `observacao` | Nota livre em uma linha | Opcional, até 240 caracteres |

Demais números aceitam até 4 casas decimais. Vírgula ou ponto decimal são aceitos,
sem separadores de milhar. Esses tetos são limites técnicos do protótipo, não faixas
recomendadas para uma fazenda. Booleanos, NaN, infinito, datas impossíveis, textos
de controle e campos desconhecidos são rejeitados. Massa colhida e perda não podem
ser ambas zero, pois o percentual não teria denominador.

No formulário de edição, Enter mantém o valor anterior; `-` limpa a observação.
Cadastro, alterações, exclusão e importação pedem confirmação `SIM`.

## Cálculos e exemplo conferível

Amostras devem ser coletadas em diferentes pontos representativos **da área já
colhida**. Some a massa e a área de todas elas antes de cadastrar:

```text
perda_t_ha = (perda_kg / amostra_m2) × 10
perdida_t = perda_t_ha × area_ha
potencial_t = colhida_t + perdida_t
perda_pct = (perdida_t / potencial_t) × 100
valor_estimado = perdida_t × preco_t
```

O fator 10 vem de 10.000 m² por hectare divididos por 1.000 kg por tonelada.
O denominador combina massa colhida e perda estimada, seguindo o conceito descrito
na pesquisa de Rosa et al. (2009). Os cálculos usam `Decimal`; o arredondamento
para duas casas ocorre na apresentação, preservando os valores intermediários.

Exemplo **sintético** CANA-01: área 10 ha, massa colhida 800 t, amostras de 10 m²
com 4 kg de cana remanescente e preço de referência R$ 150/t. Resultado: **4 t/ha**,
**40 t perdidas**, **4,76%** de perda e **R$ 6.000,00** de cana perdida estimada.

Com os três exemplos do JSON: 30 ha em operações, 2.400 t colhidas, 116 t perdidas
estimadas, percentual agregado de aproximadamente **4,61%** e valor **R$ 17.400,00**.
O relatório calcula `soma(perdida_t) / soma(potencial_t) × 100`, e não a média simples
dos percentuais. Totais e rankings são separados por origem dos dados.

### Alerta e cenário

O alerta padrão de 5% é uma **regra didática escolhida para o projeto**. Não é
um limite agronômico universal nem um valor recomendado pela pesquisa. Pode mudar:

```bash
python main.py --demo --limite-perda 7
```

O relatório sinaliza perdas iguais ou superiores ao limite e sugere verificar a
amostragem e inspecionar a operação. Não determina automaticamente velocidade,
rotação de extrator ou regulagem de máquina. O cenário de reduzir pela metade as
perdas é apenas aritmético: não prevê que isso ocorrerá e não considera custos.

## Conteúdos exigidos e onde aparecem

| Conteúdo | Aplicação concreta |
|---|---|
| Função com parâmetros e retorno | `calcular_perdas(registro)`, `resumir(registros)` |
| Procedimento com parâmetros | `mostrar_lista(registros)`, `escrever_texto(caminho, conteudo)` |
| Lista | Registros de colheita e linhas do relatório |
| Tupla | `CAMPOS`, `COLUNAS` e chave composta `(talhao, data_colheita)` |
| Dicionário | Cada colheita, regras de limites e resultados dos cálculos |
| Tabela de memória | Lista de dicionários retornada por `banco.listar()` |
| Arquivo texto | `open(..., encoding='utf-8')` para TXT/SQL e escrita do relatório |
| Arquivo JSON | `json.load`, `json.dumps`, importação e exportação |
| Oracle | `oracledb.connect`, SELECT/INSERT/UPDATE/DELETE e criação da tabela |
| Validação e exceções | Repetição de entrada, `try/except` e rollback em falhas |

## Arquivos

| Caminho | Papel |
|---|---|
| `main.py` | Inicialização e opções de execução |
| `cana/dominio.py` | Validação, estruturas de dados e fórmulas |
| `cana/interface.py` | Menu e entrada do usuário |
| `cana/banco.py` | Conexão Oracle e persistência |
| `cana/arquivos.py` | TXT e JSON |
| `cana/relatorios.py` | Formatação e priorização |
| `sql/criar_tabelas.sql` | Estrutura Oracle e restrições |
| `config/oracle.exemplo.json` | Modelo de configuração sem credenciais reais |
| `dados/exemplo_sintetico.json` | Três colheitas inventadas |
| `tests/test_cana.py` | Testes de cálculos, entradas, persistência e transações com doubles |
| `PASSO_A_PASSO.md` | Instalação e teste no Windows |
| `docs/VALIDACAO.md` | Testes locais e resultados da integração Oracle no Windows |

## Integridade e limitações

Importação valida todas as linhas, duplicatas e capacidade antes de gravar. Oracle
grava lotes em uma transação, com rollback se falhar. JSON usa arquivo temporário
e substituição atômica, preservando a versão anterior em falhas de escrita.
Dados são enviados ao SQL por bind variables; nomes de tabela e comandos são fixos.
O modo JSON é voltado a uma única sessão local, sem suporte a edições concorrentes.
O protótipo limita a tabela a 1.000 registros e a importação a 5 MB.

As estimativas dependem da representatividade das amostras. Não há intervalo de
confiança: o programa recebe a amostragem agregada. Não mede perdas invisíveis,
ATR, impurezas, transporte ou prejuízo líquido. O campo `observado` registra a
declaração do usuário, sem auditar a origem. O programa não comprova redução real
de perdas. Dados do exemplo não foram coletados em fazenda.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes com doubles verificam o uso de binds, commit e rollback, mas **não provam
uma conexão real com Oracle**. A integração real foi conferida separadamente no
Windows do autor: conexão, criação da tabela, importação, relatório, persistência,
cadastro, edição e exclusão. Veja `docs/VALIDACAO.md` para resultados e limites.

## Referências consultadas

- Rosa, E. J.; José, J. V.; Salvestro, A. C.; Gava, R. **Perdas visíveis de cana-de-açúcar
  em colheita mecanizada**. VI EPCC, 2009.
  https://www.unicesumar.edu.br/epcc-2009/wp-content/uploads/sites/77/2016/07/jefferson_vieira_jose3.pdf
  Base para o conceito de massa remanescente em área amostrada e denominador do percentual.
  Resultados experimentais daquele estudo não foram tratados como padrão nacional atual.
- Embrapa. **Agricultura digital: pesquisa, desenvolvimento e inovação nas cadeias produtivas**,
  2020. https://www.alice.cnptia.embrapa.br/handle/doc/1126213
  Registro bibliográfico e descrição consultados para contextualizar agricultura digital.
- Oracle / python-oracledb. Conexões, variáveis vinculadas e transações:
  https://python-oracledb.readthedocs.io/en/stable/user_guide/connection_handling.html
  https://python-oracledb.readthedocs.io/en/stable/user_guide/bind.html
  https://python-oracledb.readthedocs.io/en/stable/user_guide/txn_management.html

## Antes de entregar

1. Adaptar a estrutura ao template oficial fornecido pela FIAP.
2. Conferir os resultados de validação Oracle registrados e completar as evidências de exportação.
3. Substituir os campos exigidos pelo template por nome, RM e demais dados reais.
4. Publicar o código, README e arquivos necessários no repositório próprio da atividade.
5. Conferir a versão entregue e não alterar o código oficial após a data de entrega.

O enunciado enviado não exige vídeo, Wokwi, ESP32 ou análise em R para esta atividade.
