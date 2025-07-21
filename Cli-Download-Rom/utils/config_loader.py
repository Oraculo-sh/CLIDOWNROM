import yaml
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent.parent / 'config.yml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print("ERRO: Ficheiro 'config.yml' não foi encontrado!")
        return None
    except yaml.YAMLError as e:
        print(f"ERRO ao ler o ficheiro de configuração: {e}")
        return None

config = load_config()