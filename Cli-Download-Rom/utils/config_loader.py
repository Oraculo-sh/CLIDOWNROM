import yaml
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent.parent / 'config.yml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print("ERROR: 'config.yml' file not found!")
        return None
    except yaml.YAMLError as e:
        print(f"ERROR reading config file: {e}")
        return None

config = load_config()