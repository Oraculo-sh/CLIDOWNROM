from core.shell import start_interactive_shell
from core.commands import handle_search
from utils.localization import _
from utils.logging_config import setup_logging

log = setup_logging()

def handle_command(user_input, parser, config):
    """
    Função intermediária que processa um comando (do shell ou da CLI).
    """
    try:
        args = parser.parse_args(user_input.split())
        if args.search_key:
            handle_search(args, config)
        else:
            print(_("usage_interactive_prompt"))
    except SystemExit:
        pass
    except Exception as e:
        log.error(_("log_command_error").format(error=e))
        print(_("error_command_failed"))


def main_cli(parser, config):
    """
    Ponto de entrada principal para a CLI.
    Decide se entra no modo interativo ou executa um comando direto.
    """
    import sys
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        handle_command(user_input, parser, config)
    else:
        start_interactive_shell(parser, config, handle_command)