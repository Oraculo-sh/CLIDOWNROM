import locale
from pathlib import Path
from .config_loader import config

class Localization:
    def __init__(self):
        self.strings = {}
        self.load_language()

    def get_system_language(self):
        """Detecta o idioma do sistema e retorna no formato en_us."""
        try:
            lang_code, _ = locale.getdefaultlocale()
            return lang_code.lower()
        except Exception:
            return "en_us" # Padrão em caso de falha

    def load_language(self):
        """Carrega o arquivo .lang com base na configuração ou no idioma do sistema."""
        if not config:
            self._load_fallback()
            return

        lang_setting = config['general'].get('default_language', 'system')
        if lang_setting == 'system':
            lang_code = self.get_system_language()
        else:
            lang_code = lang_setting.lower()

        base_path = Path(__file__).parent.parent
        lang_file = base_path / 'locales' / f"{lang_code}.lang"

        if not lang_file.exists():
            print(f"Warning: Language file '{lang_file}' not found. Falling back to en_us.")
            lang_file = base_path / 'locales' / "en_us.lang"
            if not lang_file.exists():
                self._load_fallback()
                return

        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.strings[key.strip()] = value.strip().strip('"')
        except Exception as e:
            print(f"Error loading language file: {e}")
            self._load_fallback()

    def get_string(self, key, *args):
        """Retorna a string traduzida para a chave fornecida, formatando se necessário."""
        message = self.strings.get(key, key) # Retorna a própria chave se não for encontrada
        if args:
            return message.format(*args)
        return message

    def _load_fallback(self):
        """Carrega um conjunto mínimo de strings em inglês caso tudo falhe."""
        self.strings = {
            "DIR_STRUCTURE_CHECK": "⌁ Verifying directory structure...",
            "DIR_CREATED": "  → Creating directory: {}",
            "DIR_STRUCTURE_SUCCESS": "✔️ Directory structure checked successfully."
        }
        print("Warning: Could not load any language file. Using hardcoded fallback strings.")


# Instância única para ser usada em toda a aplicação
t = Localization()