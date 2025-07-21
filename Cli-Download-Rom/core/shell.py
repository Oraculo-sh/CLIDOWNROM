import cmd
import shlex
import os
import glob
import sys
from pathlib import Path

from ..utils.localization import t
from ..utils.config_loader import config
from .commands import handle_search, handle_download_list, handle_update_db

PLATFORM_KEYWORDS = {
    'nes': ['nes', 'nintendo'], 'snes': ['snes', 'super nintendo'],
    'n64': ['n64', 'nintendo 64'], 'gc': ['gc', 'gamecube'], 'wii': ['wii'],
    'wiiu': ['wiiu'], 'gb': ['gb', 'game boy'], 'gbc': ['gbc', 'game boy color'],
    'gba': ['gba', 'game boy advance'], 'nds': ['nds', 'nintendo ds'], 'dsi': ['dsi'],
    '3ds': ['3ds'], 'n3ds': ['n3ds', 'new 3ds'], 'ps1': ['ps1', 'psx', 'playstation'],
    'ps2': ['ps2', 'playstation 2'], 'ps3': ['ps3', 'playstation 3'],
    'psp': ['psp'], 'psv': ['psv', 'ps vita'], 'smd': ['smd', 'genesis', 'mega drive'],
    'scd': ['scd', 'sega cd'], 'sat': ['sat', 'saturn'], 'dc': ['dc', 'dreamcast']
}

class InteractiveShell(cmd.Cmd):
    intro = t.get_string("INTERACTIVE_SHELL_WELCOME")
    prompt = 'Downloader> '

    def __init__(self, parser):
        super().__init__()
        self.parser = parser
        if self.parser._subparsers:
             self.commands = list(self.parser._subparsers._group_actions[0].choices.keys())
        else:
             self.commands = []

    def help_search(self): print(t.get_string("HELP_SEARCH"))
    def help_download_list(self): print(t.get_string("HELP_DOWNLOAD_LIST"))
    def help_update_db(self): print(t.get_string("HELP_UPDATE_DB"))
    def help_exit(self): print(t.get_string("HELP_EXIT"))

    def do_search(self, arg_string):
        try:
            args = self.parser.parse_args(['search'] + shlex.split(arg_string, posix=(os.name != 'nt')))
            handle_search(args)
        except SystemExit: pass
    def do_download_list(self, arg_string):
        try:
            args = self.parser.parse_args(['download-list'] + shlex.split(arg_string, posix=(os.name != 'nt')))
            handle_download_list(args)
        except SystemExit: pass
    def do_update_db(self, arg_string):
        try:
            args = self.parser.parse_args(['update-db'] + shlex.split(arg_string, posix=(os.name != 'nt')))
            handle_update_db(args)
        except SystemExit: pass
    def do_clear(self, arg):
        os.system('cls' if os.name == 'nt' else 'clear')
    def do_cls(self, arg):
        self.do_clear(arg)
    def do_exit(self, arg):
        print(t.get_string("INTERACTIVE_SHELL_EXIT")); return True
    def do_quit(self, arg): return self.do_exit(arg)
    def do_EOF(self, arg): print(); return self.do_exit(arg)
    def emptyline(self): pass

    def completenames(self, text, *ignored):
        return [command for command in self.commands if command.startswith(text)]
    
    def complete(self, text, state):
        try:
            # A biblioteca readline não está disponível no Windows por padrão, então usamos um fallback
            line = ""
            if 'readline' in sys.modules:
                line = sys.modules['readline'].get_line_buffer()
            
            words = shlex.split(line, posix=(os.name != 'nt'))
            
            if len(words) == 0 or (len(words) == 1 and not line.endswith(' ')):
                return (self.completenames(text) + [None])[state]

            command = words[0]
            if command in self.commands:
                completer_method_name = f'complete_{command}'
                if hasattr(self, completer_method_name):
                    completer = getattr(self, completer_method_name)
                    return (completer(text, line, words) + [None])[state]
        except Exception:
            pass
        return None

    def complete_download_list(self, text, line, words):
        list_dir = Path(__file__).parent.parent / config['general']['lists_directory']
        text_to_match = str(list_dir / (text + '*'))
        matches = glob.glob(text_to_match)
        # Retorna o caminho relativo à pasta do projeto para ser mais limpo
        return [str(Path(config['general']['lists_directory']) / Path(m).name) for m in matches]
    
    def complete_search(self, text, line, words):
        last_arg = words[-1] if text == '' else words[-2]

        if text.startswith('-'):
            opts = ['--source', '--platform', '--region']
            return [o for o in opts if o.startswith(text)]
        if last_arg == '--source':
            opts = ['api', 'local']
            return [o for o in opts if o.startswith(text)]
        return []