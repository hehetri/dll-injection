# Gerador de dungeon.bin

Este repositório contém um script (`generator_dungeon.py`) que transforma arquivos JSON individuais de dungeons em um único arquivo `dungeon.bin`.

## Pré-requisitos
- Python 3.8 ou superior.
- Arquivos JSON de cada dungeon no diretório de entrada (por padrão `files/dungeon` ao lado do script).

## Como usar
1. Crie (ou aponte) um diretório contendo os arquivos JSON com os nomes listados no script.
   - Linhas comentadas iniciando com `//`, `#` e blocos entre `/* ... */` são ignorados automaticamente.
   - Se houver mais de um objeto JSON no arquivo, somente o primeiro será usado e o restante será ignorado com um aviso.
   - Arquivos vazios, apenas com comentários ou sem um valor JSON logo no início geram erro indicando o arquivo problemático para facilitar o ajuste.
- Valores de `clear` podem ser números ou strings numéricas; eles são normalizados para índices inteiros e geram erro se ficarem fora dos limites da lista `spawns`.
- O campo `spawns` precisa ser uma lista (não um objeto/dicionário); índices de `clear` são convertidos explicitamente para inteiro e produzem erro claro se não puderem ser interpretados como tal.
2. Execute o comando abaixo informando o caminho de saída para o `dungeon.bin`.

```bash
python generator_dungeon.py caminho/para/dungeon.bin --input-dir caminho/para/pasta/dungeon_json
```

Se você mantiver a estrutura padrão (`files/dungeon` ao lado do script), basta indicar apenas o arquivo de saída:

```bash
python generator_dungeon.py dungeon.bin
```

O script exibirá o progresso no terminal e criará o arquivo `dungeon.bin` no caminho informado.
