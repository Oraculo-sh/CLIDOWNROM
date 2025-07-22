import sys
from .utils.config_loader import load_config
from .utils.logging_config import setup_logging
from .core.parser import create_parser
from .core.shell import start_interactive_shell
from .core.commands import handle_search
from .utils.localization import _, load_language

class App:
    def __init__(self):
        """Inicializa a aplicação, carregando configuração e preparando o ambiente."""
        self.config = load_config('config.yml')
        setup_logging(self.config)
        load_language(self.config.get("general", {}).get("default_language"))
        self.parser = create_parser(self.config)
        self.log = setup_logging()

    def run(self):
        """Inicia a execução da aplicação, decidindo entre modo CLI e interativo."""
        if len(sys.argv) > 1:
            command_line_input = " ".join(sys.argv[1:])
            self.handle_command(command_line_input)
        else:
            start_interactive_shell(self.parser, self.config, self.handle_command)

    def handle_command(self, user_input):
        """
        Processa um único comando, seja da linha de comando ou do shell interativo.
        """
        try:
            args = self.parser.parse_args(user_input.split())
            
            if args.search_key:
                handle_search(args, self.config)
            else:
                print(_("usage_interactive_prompt"))

        except SystemExit:
            pass
        except Exception as e:
            self.log.error(_("log_command_error").format(error=e))
            print(_("error_command_failed"))