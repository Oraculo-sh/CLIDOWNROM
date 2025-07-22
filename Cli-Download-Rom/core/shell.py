from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from ui.completer import CliCompleter
from utils.localization import _
import os

def start_interactive_shell(parser, config, handle_command_func):
    """
    Inicia o shell interativo com autocomplete e histórico de comandos.
    """
    print(_("welcome_interactive_mode"))
    print(_("interactive_mode_hint"))

    history_file = os.path.join(os.path.expanduser("~"), ".clidownrom_history")
    history = FileHistory(history_file)

    platforms = parser.get_choices("platforms_cache_file", lambda _: None, config, "platforms")
    regions = parser.get_choices("regions_cache_file", lambda _: None, config, "regions")

    command_map = {
        'search': {
            'platforms': platforms,
            'regions': regions,
        },
        'help': {},
        'exit': {}
    }
    
    completer = CliCompleter(command_map)
    session = PromptSession(
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        complete_while_typing=True
    )

    while True:
        try:
            user_input = session.prompt("CliDownRom> ")
            if user_input.lower().strip() in ["exit", "quit"]:
                break
            
            if user_input.strip():
                handle_command_func(user_input, parser, config)

        except (KeyboardInterrupt, EOFError):
            break
    
    print(f"\n{_('goodbye_message')}")