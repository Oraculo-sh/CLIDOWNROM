from pathlib import Path
from .config_loader import config
from .localization import t # Importa a instância de tradução

def create_project_structure():
    """
    Verifica e cria a estrutura de diretórios necessária para o projeto.
    """
    if not config:
        print("Error: Config file could not be loaded. Aborting directory creation.")
        return

    base_path = Path(__file__).parent.parent

    # ... (lógica de diretórios permanece a mesma) ...
    all_dirs = [
        config['general']['roms_directory'],
        # ... etc
    ]

    print(t.get_string("DIR_STRUCTURE_CHECK"))
    for dir_name in all_dirs:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            print(t.get_string("DIR_CREATED", dir_path)) # Passa o argumento para formatar
            dir_path.mkdir(parents=True, exist_ok=True)
    print(t.get_string("DIR_STRUCTURE_SUCCESS"))