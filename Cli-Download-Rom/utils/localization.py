import locale
from pathlib import Path
from .config_loader import config

class Localization:
    def __init__(self):
        self.strings = {}
        self.load_language()

    def get_system_language(self):
        try:
            lang_code, _ = locale.getdefaultlocale()
            if lang_code:
                return lang_code.lower()
            return "en_us"
        except Exception:
            return "en_us"

    def load_language(self):
        if not config:
            self._load_fallback()
            return

        lang_setting = config['general'].get('default_language', 'system')
        lang_code = self.get_system_language() if lang_setting == 'system' else lang_setting.lower()

        base_path = Path(__file__).parent.parent
        lang_file = base_path / 'locales' / f"{lang_code}.lang"

        if not lang_file.exists():
            print(f"Aviso: Ficheiro de idioma '{lang_file}' não encontrado. A usar en_us como padrão.")
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
            print(f"Erro ao carregar ficheiro de idioma: {e}")
            self._load_fallback()

    def get_string(self, key, *args):
        message = self.strings.get(key, f"[{key}]")
        if args:
            return message.format(*args)
        return message

    def _load_fallback(self):
        self.strings = { "APP_DESCRIPTION": "Command-line tool to download ROMs via CrocDB." }
        print("Aviso: Não foi possível carregar nenhum ficheiro de idioma. A usar textos de emergência.")

t = Localization()