import cmd
import shlex
import os
import glob
import sys
from pathlib import Path

from ..utils.localization import t
from ..utils.config_loader import config
from .commands import handle_search, handle_download, handle_download_list

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
    def help_download(self): print(t.get_string("HELP_DOWNLOAD"))
    def help_exit(self): print(t.get_string("HELP_EXIT"))

    def do_search(self, arg_string):
        try:
            args = self.parser.parse_args(['search'] + shlex.split(arg_string, posix=(os.name != 'nt')))
            handle_search(args)
        except SystemExit: pass
    def do_download(self, arg_string):
        try:
            args = self.parser.parse_args(['download'] + shlex.split(arg_string, posix=(os.name != 'nt')))
            handle_download(args)
        except SystemExit: pass
    def do_download_list(self, arg_string):
        try:
            # Para permitir a chamada interativa sem argumentos
            args_list = ['download-list'] + shlex.split(arg_string, posix=(os.name != 'nt'))
            args = self.parser.parse_args(args_list)
            handle_download_list(args)
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
        except Exception: pass
        return None

    def complete_download_list(self, text, line, words):
        list_dir = Path(__file__).parent.parent / config['general']['lists_directory']
        text_to_match = str(list_dir / (text + '*'))
        matches = glob.glob(text_to_match)
        return [os.path.basename(m) for m in matches]

    def complete_search(self, text, line, words):
        # Lógica de autocompletar para flags
        last_word = words[-1] if text == '' else words[-2] if len(words) > 1 else ''
        if text.startswith('-'):
            opts = ['--platform', '--region', '--slug', '--rom_id']
            return [o for o in opts if o.startswith(text)]
        return []

    def complete_download(self, text, line, words):
        # Lógica de autocompletar para flags
        if text.startswith('-'):
            opts = ['--slug', '--rom_id', '--mirror', '--noboxart', '--noaria2c']
            return [o for o in opts if o.startswith(text)]
        return []