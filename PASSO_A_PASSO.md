# CanaControle — execução no Windows

## 1. Extrair o projeto

Extraia o ZIP para `E:\Fiap\CanaControle_Projeto`. Entre na pasta `CanaControle`
que contém `main.py`. Abra o Prompt de Comando nessa pasta. Exemplo:

```bat
cd /d E:\Fiap\CanaControle_Projeto\CanaControle
python --version
```

Adapte o caminho ao local real da extração. Se `python` não for reconhecido e o
lançador Python estiver instalado, use `py` em lugar de `python` nos comandos.

## 2. Testar a demonstração enquanto localiza o Oracle

Para abrir com dois cliques, use **INICIAR_DEMO.bat**, dentro da pasta extraída
que contém `main.py`. Esse iniciador mantém a janela aberta mesmo se ocorrer um erro.
Não execute diretamente dentro do ZIP. Para o banco real, use `INICIAR_ORACLE.bat`
depois de instalar o driver e preencher a configuração da seção 4.

Também é possível executar pelo Prompt de Comando:

```bat
python main.py --demo
```

1. Digite `8` e Enter.
2. Pressione Enter para escolher o JSON sintético incluído.
3. Digite `SIM` e Enter.
4. Digite `5`: o relatório mostra os três exemplos e aproximadamente 4,61% de perda agregada.
5. Digite `6` para exportar TXT e `7` para exportar JSON.
6. Digite `0` para sair.

Os arquivos exportados ficam em `resultados`. O programa continua guardando dados
da demonstração em `dados/demo_local.json` ao ser fechado. A importação não substitui
essa base: adiciona novos registros e rejeita repetidos.

## 3. Preparar o Oracle

### Oracle local no Windows — ambiente usado pelo autor

Com Oracle AI Database 26ai Free instalado, abra o Prompt de Comando do usuário
que realizou a instalação e execute:

```bat
sqlplus / as sysdba
```

No prompt `SQL>`, execute `SHOW PDBS;` e confira se `FREEPDB1` está `READ WRITE`.
Para criar o usuário do projeto pela primeira vez, execute:

```sql
ALTER SESSION SET CONTAINER = FREEPDB1;
CREATE USER canacontrole NO AUTHENTICATION
DEFAULT TABLESPACE USERS QUOTA 20M ON USERS;
GRANT CREATE SESSION, CREATE TABLE TO canacontrole;
PASSWORD canacontrole
```

O comando `PASSWORD` pede a nova senha duas vezes, sem exibi-la. Não cole os comandos
seguintes enquanto ele estiver aguardando a senha. Depois execute uma linha por vez:

```sql
CONNECT canacontrole@"localhost:1521/FREEPDB1"
```

Informe a senha criada; após aparecer `Conectado`, execute:

```sql
SELECT USER FROM dual;
```

O resultado deve ser `CANACONTROLE`. Nessa versão do SQL*Plus, o endereço entre aspas
permite que a conexão solicite a senha separadamente. Não recrie um usuário existente.

### Oracle fornecido pela faculdade

Procure no portal da FIAP, no material do capítulo de conexão com banco de dados,
as instruções de acesso Oracle. Precisamos de **usuário, host, porta e nome do serviço**.
O nome do serviço é usado após a barra no DSN `host:porta/servico`.
Não invente um host a partir de um exemplo de aula. Se só houver SID ou wallet,
confira com o material/tutor qual formato de conexão esse ambiente utiliza.

Você pode enviar uma captura das instruções, ocultando a senha, para receber ajuda
com o preenchimento. Digite a senha apenas no seu computador.

## 4. Configurar e conectar

Instale o driver:

```bat
python -m pip install -r requirements.txt
```

Copie `config\oracle.exemplo.json` para `config\oracle.json`. Abra a cópia no
Bloco de Notas e substitua os placeholders pelos valores oficiais do seu ambiente.
O exemplo não contém um servidor funcional. Mantenha apenas `usuario` e `dsn`.

Se você instalou o Oracle local conforme a seção 3, use este conteúdo em `oracle.json`:

```json
{
  "usuario": "canacontrole",
  "dsn": "localhost:1521/FREEPDB1"
}
```

```bat
python main.py
```

Digite a senha quando solicitada. É normal não aparecerem caracteres. Se conectar,
o programa exibe `MODO: ORACLE`. Use `9` e confirme com `SIM` para criar a tabela
se ainda não existir. Se o acesso não permitir CREATE TABLE, solicite orientação
à faculdade ou execute o SQL com o usuário autorizado.

## 5. Demonstrar os conteúdos obrigatórios no Oracle

1. Use `8` para importar o exemplo sintético no Oracle (opcional, em tabela sem esses registros).
2. Use `1` para cadastrar uma colheita sintética com talhão `TESTE-RM576052`.
3. Use `2` para listar e verificar o cadastro.
4. Feche com `0`, abra novamente `python main.py` e use `2`: o cadastro deve persistir no Oracle.
5. Use `3` para editar o registro e confira novamente.
6. Use `6` e `7` para gerar TXT/JSON a partir do Oracle.
7. Use `4` para excluir SOMENTE o registro de teste, confirmando `SIM`.
8. Em SQL Developer ou ferramenta Oracle da disciplina, execute:

```sql
SELECT talhao, data_colheita, area_ha, colhida_t, origem
FROM ftc_colheitas
ORDER BY data_colheita, talhao;
```

O registro de teste removido não deve aparecer; os outros registros devem permanecer.
Registre o resultado em `docs/VALIDACAO.md` sem incluir a senha. Não descreva um teste
em demonstração como se fosse um teste de Oracle.

## 6. Testar validações

Tente digitar uma letra no campo de área, valor negativo, data impossível e opção
de menu inválida. O programa deve explicar o problema e permitir corrigir a entrada.
Em seguida execute:

```bat
python -m unittest discover -s tests -v
```

## 7. Preparar a entrega

O template oficial citado no enunciado não veio no material anexado. Localize o
link/ZIP e adapte a organização do repositório ao modelo pedido. Publique os arquivos
do projeto, incluindo README, módulos Python, SQL, requirements e JSON de exemplo.
Não publique a configuração real, bases locais, caches ou `.venv`.

Se usar upload pelo navegador, selecione explicitamente os arquivos desejados:
o navegador não aplica automaticamente as exclusões do `.gitignore`.
Este trabalho deve ter seu próprio repositório/template. Preserve a versão já
entregue da atividade anterior de irrigação.
