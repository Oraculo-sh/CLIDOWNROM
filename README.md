# CLIDOWNROM

![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)

Uma ferramenta de linha de comando (CLI) poderosa e autônoma para pesquisar e baixar ROMs de jogos utilizando o banco de dados do CrocDB.

## ✨ Funcionalidades

* **Interface Híbrida:** Funciona como um CLI padrão para automação e também como um Shell Interativo amigável para uso guiado.
* **Autoinstalação:** Gerencia suas próprias dependências (Python e Git) de forma automática na primeira execução.
* **Atualizações Automáticas:** Verifica e atualiza o banco de dados do CrocDB para manter as informações das ROMs sempre recentes.
* **Múltiplas Fontes:** Busca ROMs tanto pela API online do CrocDB quanto por um banco de dados local para operações em lote mais rápidas.
* **Teste Inteligente de Mirrors:** Testa a velocidade dos mirrors de download e prioriza o mais rápido para otimizar a velocidade de download.
* **Gerenciador de Downloads Robusto:** Inclui barras de progresso, retentativas automáticas, validação de tamanho do arquivo e organização automática em pastas por plataforma.
* **Logging Detalhado:** Registra todas as operações, sucessos, erros e crashes em arquivos de log para fácil depuração.
* **Suporte a Múltiplos Idiomas:** A interface se adapta ao idioma do sistema (com suporte inicial para pt_br e en_us).

## 🚀 Instalação e Primeira Execução

A ferramenta foi projetada para ser o mais simples possível de instalar e usar.

**Pré-requisitos:**
* [Python 3.8+](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads/)

Com os pré-requisitos instalados, siga os passos:

1.  **Obtenha o projeto:**
    ```bash
    git clone [https://github.com/Oraculo-adm/CLIDOWNROM.git](https://github.com/Oraculo-adm/CLIDOWNROM.git)
    cd CLIDOWNROM
    ```

2.  **Execute o Launcher:**
    Basta executar o script iniciador correspondente ao seu sistema operacional.

    * **No Windows:**
        ```bash
        start.bat
        ```
        (Você também pode dar um duplo-clique no arquivo `start.bat`)

    * **No Linux ou macOS:**
        ```bash
        chmod +x start.sh  # Dá permissão de execução (só precisa na primeira vez)
        ./start.sh
        ```

Na primeira vez que você executar, o script irá automaticamente criar um ambiente virtual, instalar as dependências do Python e baixar os bancos de dados necessários do CrocDB. Nas execuções seguintes, ele iniciará a aplicação instantaneamente.

## ⚙️ Configuração

O comportamento da ferramenta pode ser ajustado através de dois arquivos principais na pasta `Cli-Download-Rom/`:

* **`config.yml`**: O arquivo de configuração principal. Aqui você pode habilitar/desabilitar o teste de mirrors, definir o número de retentativas de download, alterar os diretórios padrão e muito mais.
* **`.env`**: Usado para credenciais. Copie o arquivo `.env.example` para `.env` e adicione seu usuário e senha do Internet Archive se precisar baixar arquivos restritos.

## USAGE

A ferramenta pode ser usada de duas maneiras:

### Modo Shell Interativo (Uso Guiado)

Execute o launcher sem argumentos (`start.bat` ou `./start.sh`) para entrar no modo interativo.

```
Bem-vindo ao Shell Interativo. Digite 'help' para uma lista de comandos ou 'exit' para sair.
Downloader> search "Super Mario World"
Downloader> download-list list/meus_favoritos.json
Downloader> exit
```

### Modo CLI Padrão (Automação e Scripts)

Passe os comandos diretamente para o launcher. A ferramenta executará a tarefa e sairá.

* **Buscar uma ROM usando a API:**
    ```bash
    start.bat search "Sonic The Hedgehog 2"
    ```
* **Baixar uma lista de ROMs:**
    ```bash
    start.bat download-list list/snes_collection.json
    ```

## 🙏 Agradecimentos e Dependências

Esta ferramenta depende fundamentalmente do excelente trabalho da equipe do **CrocDB**. Os seguintes projetos são utilizados como dependências:

* [**crocdb-db**](https://github.com/cavv-dev/crocdb-db) (Licença MIT)
* [**crocdb-api**](https://github.com/cavv-dev/crocdb-api) (Licença MIT)

Agradecemos por fornecerem um recurso tão valioso para a comunidade de preservação de jogos.

## ⚖️ Licença

Este projeto está licenciado sob os termos da Licença Creative Commons Atribuição-NãoComercial-CompartilhaIgual 4.0 Internacional. Veja o arquivo [LICENSE.md](LICENSE.md) para mais detalhes.