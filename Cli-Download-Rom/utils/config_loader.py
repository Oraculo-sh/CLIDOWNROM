# Cli-Download-Rom/utils/config_loader.py

import yaml
from pathlib import Path

def load_config():
    """Carrega o arquivo de configuração config.yml."""
    # O caminho é relativo à pasta principal do pacote (Cli-Download-Rom)
    config_path = Path(__file__).parent.parent / 'config.yml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print("ERRO: Arquivo 'config.yml' não foi encontrado!")
        return None
    except yaml.YAMLError as e:
        print(f"ERRO ao ler o arquivo de configuração: {e}")
        return None

# Carrega a configuração uma vez para ser importada por outros módulos
config = load_config()