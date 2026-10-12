# Validação do CanaControle

## Verificação local executada em 11/10/2026

Ambiente de desenvolvimento: Python 3.12.14, Linux.

- 15 testes automatizados passaram: cálculos e unidades, percentual agregado por
  massa, entradas inválidas, datas, duplicatas, separação de origem, JSON, CRUD local,
  persistência e importação sem gravação parcial.
- Os testes do contrato Oracle utilizaram doubles: verificação de binds, commit,
  rollback e número de linhas afetadas. Não houve servidor Oracle nesses testes.
- O programa foi executado pelo terminal em modo `--demo`, com importação dos três
  exemplos, relatório, exportação TXT/JSON e encerramento normal.
- A exportação JSON foi relida e conferida; o TXT correspondeu ao relatório da tabela.
- Uma segunda importação do mesmo exemplo foi rejeitada, preservando os três registros.

Evidências: `testes_locais.txt` e `demonstracao_terminal.txt` nesta pasta.
Todos os dados nessa demonstração são sintéticos.

## Verificação Oracle no computador do aluno — 11/10/2026

Marlon executou o programa no Windows com Oracle AI Database 26ai Free,
versão 23.26.3.0.0, serviço local `localhost:1521/FREEPDB1` e usuário
`CANACONTROLE`. Os resultados abaixo foram conferidos nas capturas do terminal
enviadas durante a validação. O Oracle local do aluno não foi acessado remotamente
pelo ambiente de desenvolvimento.

| Verificação | Resultado verdadeiro |
|---|---|
| Data do teste e versões Python/driver | 11/10/2026; versões Python/driver no Windows não registradas |
| Conectou e exibiu MODO: ORACLE | CONFIRMADO; SQL*Plus também identificou o usuário CANACONTROLE |
| Criou a tabela | CONFIRMADO; opção 9 criou ftc_colheitas |
| Importou e consultou três exemplos sintéticos | CONFIRMADO; CANA-01, CANA-02 e CANA-03 |
| Relatório calculado a partir do Oracle | CONFIRMADO; 116,00 t, 4,61% e R$ 17.400,00 |
| Fechou/reabriu e os registros continuaram no Oracle | CONFIRMADO; os três exemplos reapareceram na opção 2 |
| Cadastrou e consultou uma colheita sintética | CONFIRMADO; TESTE-RM576052, 1 ha e 80 t colhidas |
| Editou e confirmou o valor alterado | CONFIRMADO; TESTE-RM576052 alterado de 80 para 85 t |
| Exportou TXT/JSON a partir do Oracle | Roteiro enviado; confirmação dos arquivos no Windows pendente |
| Excluiu somente o registro de teste | CONFIRMADO; TESTE-RM576052 removido e os três exemplos preservados |
| Consultou ftc_colheitas diretamente no SQL*Plus | PENDENTE; consulta complementar ao teste pelo programa |

Os testes de integração confirmados envolvem dados sintéticos, sem medições de fazenda.
Não foram verificados concorrência, todas as falhas possíveis de conexão ou rollback
em servidor real; commit/rollback em falhas permanecem cobertos pelos doubles locais.
Registre somente testes realmente realizados. Não inclua a senha ou dados privados.

## Template oficial — AINDA PENDENTE

O enunciado exige um template, mas seu link/ZIP não estava no material recebido.
O código está organizado provisoriamente. É necessário obter o modelo oficial e
adaptar o repositório antes de entregar.
