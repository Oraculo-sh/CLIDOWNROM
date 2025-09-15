# Roadmap

## Backend

*Estrutura*
*Diretórios do Projeto*
- source/                                # Diretório principal do código fonte
  - core/                                # Módulos de funcionalidade principal
    - __init__.py                        # Inicialização do módulo principal
    - config_manager.py                  # Gerenciador de configurações do sistema
    - crocdb_client.py                   # Interface de cliente da API CrocDB
    - directory_manager.py               # Gerenciador de diretórios do sistema
    - cache_manager.py                   # Sistema de cache para otimização de requisições
    - download_manager.py                # Gerenciador de downloads de ROMs
    - helpers.py                         # Funções auxiliares diversas
    - locale_manager.py                  # Sistema de internacionalização
    - logger_system.py                   # Sistema de registro de logs
    - search_engine.py                   # Motor de busca de ROMs
    - utils.py                           # Utilitários gerais
    - version.py                         # Controle de versão do sistema
  - interfaces/                          # Módulos de interface do usuário
    - cli/                               # Implementação da Interface de Linha de Comando
    - shell/                             # Implementação da Interface Shell Interativa
    - tui/                               # Implementação da Interface de Usuário Terminal
    - gui/                               # Implementação da Interface Gráfica
  - locales/                             # Arquivos de internacionalização
    - en_us.yml                          # Strings do idioma padrão
  - config.yml                           # Arquivo principal de configuração
  - main.py                              # Ponto de entrada da aplicação


### Fase 1 - Sistemas

#### Task 1 - Cache
[ ] *Sistema de cache 'temp\cache'*
- [ ] Sistema de cache de resultados de pesquisas de ROMs para evitar requisições repetidas ao servidor.
- [ ] Sistema de cache de informações de ROMs para evitar requisições repetidas ao servidor.
- [ ] Sistema de cache de thumbnails com a boxart para previa viasualizção das capas nos resultados de pesquisas, armazene numa pasta 'temp\cache\thumbnails'.
- [ ] Sistema de cache de informações de plataformas e regiões para evitar requisições repetidas ao servidor.
- [ ] Sistema de armazenamento de historico de download temporario no diretorio temp\history\download_history.csv armazenando todas as informações da rom, hora e data do download, tempo decorrido, onde foi armazenado, se houve algum erro e quantas tentativas ate o sucesso.
- [ ] Gestão de Validade (TTL) para os arquivos de cache, garantindo que os dados não fiquem obsoletos, valor editavel no config.yml

#### Task 2 - Internacionalização
[ ] *Sistema de locales*
- [ ] Sistema de locales para suporte a vários idiomas em 'source\locales'.
- [ ] Idioma padrão 'en_us' para todas os textos.
  * [ ] Estruturar o 'en_us.yml' para definir o modelo padrão dos demais arquivos a serem seguidos.
- [ ] Sistema de escaneamento do diretorio 'source\locales' para buscar arquivos yml de idiomas, assim qualquer um pode criar seu proprio locale e colocar no diretorio, necessario serguir o padrão de de locale code. 
  * [ ] O locale code é o nome do arquivo sem a extensão '.yml', por exemplo: 'en_us', 'pt_br', 'es_es', 'ru_ru', etc.
  * [ ] O locale code é case insensitive, ou seja, 'en_us' é o mesmo que 'EN_US'.
- [ ] Configuração do idioma preferido no arquivo de configuração.
  * [ ] Se parte das traduções do idioma preferido não estiver disponivel, carregar o arquivo de locale padrão 'en_us'.
- [ ] Sistema que reconhece o idioma do sistema operacional e carrega o locale correspondente se disponivel
  * [ ] Opção 'auto' como locale preferido no config.yml para reconhecimento automatico do idioma do sistema.
- [ ] Gerar locales traduzidos
  * [ ] pt_br.yml
  * [ ] ru_ru.yml
  * [ ] es_es.yml

#### Task 3 - Sistema de configuração

[ ] *Configuração*
- [ ] Renomear source\core\config.py para 'source\core\config_manager.py'
- [ ] Migrar o source\config\config.yml para 'source\config.yml'
- [ ] Armazenar valores padroes de opções em 'source\core\config_manager.py'
- [ ] Configurar o 'source\core\directory_manager.py' para gerar o 'source\config.yml' com as opções padroes caso o arquivo não exista.

#### Task 4 - Sistema de diretorios 
[ ] *Sistema de diretorios*
- [ ] Configurar o 'source\core\directory_manager.py' para verificar durante a primeira execução se os diretorios existem, caso não exista, criá-los conforme o 'source\config.yml'.
  * [ ] Diretorio ROMs
  * [ ] Diretorio ROMs\boxart
  * [ ] Diretorio logs
  * [ ] Diretorio temp
  * [ ] Diretorio temp\download
  * [ ] Diretorio temp\cache
  * [ ] Diretorio temp\cache\thumbnails
  * [ ] Diretorio temp\test
  * [ ] Diretorio history
  * [ ] Arquivo source\config.yml (Conforme Fase 1 - Task 3)


---
### Fase 2 - Comandos e Flags

#### Task 1 - Comandos
[ ] *Comandos*
- [ ] Comando *search* <query> [options] - Search for ROMs
- [ ] Comando *download* <index> - Baixa a rom do index da ultima execução do 'search', caso nao tenha index, exiba "Por favor, realize uma busca antes de usar o download por índice."
- [ ] Comando *boxart* <index> - Exporta a boxart da rom expecificada
- [ ] Comando *random* [options] - Get random ROMs
- [ ] Comando *info* <index> - Show ROM information
- [ ] Comando *config* <action> [args] - Manage configuration
  * [ ] set <key> <value> - Set a configuration value
  * [ ] get <key> - Get a configuration value
  * [ ] list - List all configuration values
  * [ ] reset <key|all> - Reset a configuration value or all values for defalt options
- [ ] Comando *platforms* - List available platforms
- [ ] Comando *regions* - List available regions
- [ ] Comando *history* - List download history
- [ ] Comando *cache-clear* - crear cache files
- [ ] Comando *clear* - Clear screen
- [ ] Comando *help* - Show help
- [ ] Comando *exit*, *quit* - Exit the program
- [ ] Comando *shell* - Abre um shell interativo
- [ ] Comando *gui* - Abre a interface grafica
- [ ] Comando *tui* - Abre a interface textual

#### Task 2 - Flags
[ ] *Flags*
- [ ] Flag "--platform, -p <code> - Filter by platform code" para os comandos
  * [ ] Implantado ao comando 'search'
  * [ ] Implantado ao comando 'download'
  * [ ] Implantado ao comando 'boxart'
  * [ ] Implantado ao comando 'random'
- [ ] Flag "--region, -r <code> - Filter by region code" para os comandos
  * [ ] Implantado ao comando 'search'
  * [ ] Implantado ao comando 'download'
  * [ ] Implantado ao comando 'boxart'
  * [ ] Implantado ao comando 'random'
- [ ] Flag "--max-results, -m <num> - Maximum number of results per page (default: 100, max: 100)" para o comando "search"
- [ ] Flag "--page <num> - Page number for pagination (default: 1)" para o comando "search"
- [ ] Flag "--romid <id> - specific ROM ID"
  * [ ] Implantado ao comando 'download'
  * [ ] Implantado ao comando 'boxart'
  * [ ] Implantado ao comando 'info'
- [ ] Flag "--slug <slug> - specific ROM Slug
  * [ ] Implantado ao comando 'download'
  * [ ] Implantado ao comando 'boxart'
- [ ] Flag "--no-boxart - Baixa sem boxart" para o comando "download"
- [ ] Flag "--count, -n <num> - Number of ROMs to return (default: 1)" para o comando "random"
- [ ] Flag "--export, -e <txt|json|csv> <path> - Export results to a file" para o comando "search", sendo quando selecionado o formato json, exportar o json retornado pela api. 
  * [ ] Implantado ao comando 'search'
  * [ ] Implantado ao comando 'history'
- [ ] Flag "--search, -s <query> - Specify search query to automatically find and download the first matching ROM" for the "download" command
- [ ] Flag "--failed" - filtra por falhas no comando "history"

#### Task 3
[ ] *Global Flags*
- [ ] Flag "--help, -h - Detalha ajuda sobre o comando e suas flags disponível."
- [ ] Flag "--force, -f - Executar o comando de forma forçada, sem confirmação
- [ ] Flag "--silence - Executar o comando de forma silenciosa, oculta no prompt, sem retornar resultado no terminal"


---
### Fase 3 - Testes
#### Task 1 - Teste manual
[ ] *Testar comandos e suas flags*
  * [ ] Testar comando search 
    > [ ] python -m source.main search mario 64 (exibiu com sucesso o resultado "Super Mario 64")
    > [ ] python -m source.main search "Super Mario Bros" -r us (exibiu com sucesso somente resultados da região us)
    > [ ] python -m source.main search "Super Mario Bros" -p wii (exibiu com sucesso somente resultados da plataforma wii)
    > [ ] python -m source.main search "Super Mario Bros" --max-results 2 (exibiu com sucesso somente 2 resultados)
    > [ ] python -m source.main search --help (exibiu com sucesso a ajuda do comando search)
    > [ ] python -m source.main search "Super Mario Bros" -p wii -r us (exibiu com sucesso somente resultados da plataforma wii e região us)
    > [ ] python -m source.main search "Super Mario Bros" -p wii -r us -m 2 (exibiu com sucesso somente 2 resultados da plataforma wii e região us)
    > [ ] python -m source.main search "Super Mario Bros" --export txt 'C:\Github\CLIDOWNROM\' (exportou com sucesso os resultados em uma lista txt no diretorio expecificado)
    > [ ] python -m source.main search "Super Mario Bros" --export json 'C:\Github\CLIDOWNROM\' (exportou com sucesso os resultados em uma lista json no diretorio expecificado)
    > [ ] python -m source.main search "Super Mario Bros" --export csv 'C:\Github\CLIDOWNROM\' (exportou com sucesso os resultados em uma lista csv no diretorio expecificado)
  * [ ] Testar comando download
    > [ ] python -m source.main download 1 (baixou com sucesso o resultado com index 1 da ultima pesquisa)
    > [ ] python -m source.main download -s Super Mario Bros (baixou com sucesso o primeiro resultado para Super Mario Bros)
    > [ ] python -m source.main download -s Super Mario Bros -p wii (baixou com sucesso o primeiro resultado para Super Mario Bros na plataforma wii)
    > [ ] python -m source.main download -s Super Mario Bros -r us (baixou com sucesso o primeiro resultado para Super Mario Bros na região us)
    > [ ] python -m source.main download --romid Y7WE (baixou com sucesso '7 Wonders of the Ancient World', plataforma 'nds' e regiao 'us')
    > [ ] python -m source.main download --romid AWRE --force (baixou com sucesso 'Advance Wars - Dual Strike (USA, Australia), plataforma 'nds' e regiao 'us' sem confirmação)
  * [ ] Testar comando boxart
    > [ ] python -m source.main boxart 1 (exportou com sucesso a boxart do item de index 1 da última pesquisa)
    > [ ] python -m source.main boxart --romid Y7WE (exportou com sucesso a boxart de '7 Wonders of the Ancient World')
    > [ ] python -m source.main boxart --help (exibiu com sucesso a ajuda do comando boxart)
  * [ ] Testar comando random
    > [ ] python -m source.main random (exibiu com sucesso 1 ROM aleatória)
    > [ ] python -m source.main random -n 5 (exibiu com sucesso 5 ROMs aleatórias)
    > [ ] python -m source.main random -p nes (exibiu com sucesso 1 ROM aleatória da plataforma NES)
    > [ ] python -m source.main random -r jp (exibiu com sucesso 1 ROM aleatória da região JP)
    > [ ] python -m source.main random -p snes -r eu -n 3 (exibiu com sucesso 3 ROMs aleatórias da plataforma SNES e região EU)
    > [ ] python -m source.main random --help (exibiu com sucesso a ajuda do comando random)
  * [ ] Testar comando info
    > [ ] python -m source.main info 1 (exibiu com sucesso as informações do item de index 1 da última pesquisa)
    > [ ] python -m source.main info --romid Y7WE (exibiu com sucesso as informações de '7 Wonders of the Ancient World')
    > [ ] python -m source.main info --help (exibiu com sucesso a ajuda do comando info)
  * [ ] Testar comando config
    > [ ] python -m source.main config get locale (exibiu com sucesso o valor da chave 'locale')
    > [ ] python -m source.main config set locale pt_br (alterou com sucesso o valor da chave 'locale' para 'pt_br')
    > [ ] python -m source.main config list (listou com sucesso todas as chaves e valores de configuração)
    > [ ] python -m source.main config reset locale (restaurou com sucesso o valor padrão da chave 'locale')
    > [ ] python -m source.main config reset all --force (restaurou com sucesso todos os valores padrão sem confirmação)
    > [ ] python -m source.main config --help (exibiu com sucesso a ajuda do comando config e seus subcomandos)
  * [ ] Testar comando platforms
    > [ ] python -m source.main platforms (exibiu com sucesso a lista de plataformas disponíveis)
    > [ ] python -m source.main platforms --help (exibiu com sucesso a ajuda do comando platforms)
  * [ ] Testar comando regions
    > [ ] python -m source.main regions (exibiu com sucesso a lista de regiões disponíveis)
    > [ ] python -m source.main regions --help (exibiu com sucesso a ajuda do comando regions)
  * [ ] Testar comando history
    > [ ] python -m source.main history (exibiu com sucesso o histórico de downloads)
    > [ ] python -m source.main history --failed (exibiu com sucesso apenas os downloads que falharam)
    > [ ] python -m source.main history --export csv 'C:\Github\CLIDOWNROM\history' (exportou o histórico para um arquivo CSV com sucesso)
    > [ ] python -m source.main history --help (exibiu com sucesso a ajuda do comando history)
  * [ ] Testar comando clear
    > [ ] python -m source.main clear (limpou a tela do terminal com sucesso)
  * [ ] Testar comando help
    > [ ] python -m source.main help (exibiu com sucesso a lista geral de comandos)
    > [ ] python -m source.main help search (exibiu com sucesso a ajuda específica para o comando 'search')
  * [ ] Testar comando exit
    > [ ] python -m source.main exit (encerrou o programa com sucesso)
    > [ ] python -m source.main quit (encerrou o programa com sucesso)

#### Task 2 - Teste automatizado
[ ] *CI/CD - Automação de Testes*
- [ ] Automatizá usando um framework de testes, como o pytest para Python. permitir rodar todos os testes com um único comando, garantindo que novas alterações não quebrem funcionalidades existentes (regressão).
- [ ] Integrar com github workflow
  * [ ] Configurar github actions para rodar os testes automaticamente a cada push
- [ ] Colocar badge no readme com resultado do teste. 
  * [ ] Configurar github actions para atualizar o badge no readme a cada push.


---
## Interfaces

---
### Fase 1 - Cli


---
### Fase 2 - Shell


---
### Fase 3 - TUI


---
### Fase 4 - GUI