# Cli-Download-Rom/__main__.py

# --- Imports de Bibliotecas Padrão e Externas ---
import logging
import sys
from dotenv import load_dotenv

# --- Imports dos Módulos do Nosso Projeto ---
# É crucial que o settings.json esteja configurado para o VS Code encontrar estes módulos.
from utils.directory_manager import create_project_structure
from utils.config_loader import config
from utils.logging_manager import setup_logging
from utils.dependency_checker import check_and_clone_dependencies
from scripts.check_updates import check_for_tool_updates, check_for_crocdb_updates
import cli


def main():
    """
    Ponto de entrada principal da aplicação.
    """
    # Carrega as variáveis de ambiente do arquivo .env (se existir)
    load_dotenv()

    # Sai se o config.yml não puder ser lido
    if not config:
        print("ERRO: Falha ao carregar o arquivo de configuração 'config.yml'. A aplicação não pode continuar.")
        return 
        
    # Cria a estrutura de pastas do projeto, se necessário
    create_project_structure()
    
    # Verifica o Git e clona as dependências (CrocDB) se for a primeira execução
    check_and_clone_dependencies()

    # Verifica se há atualizações para a ferramenta e para o banco de dados
    check_for_tool_updates()
    check_for_crocdb_updates()

    # Configura o sistema de logging (arquivos e console)
    setup_logging()

    try:
        # Inicia a interface de linha de comando (modo CLI ou Interativo)
        cli.start()
    except Exception:
        # Pega qualquer erro crítico que possa ter escapado e o registra
        logging.critical("Ocorreu um erro crítico e não tratado no fluxo principal da aplicação.", exc_info=True)
        print("\n❌ Um erro crítico ocorreu. Verifique o arquivo 'crash.log' para mais detalhes.")
        sys.exit(1)


if __name__ == "__main__":
    main()