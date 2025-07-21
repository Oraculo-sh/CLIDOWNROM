import sys
import argparse

from .core.parser import get_parser
from .core.shell import InteractiveShell
from .core.commands import handle_search, handle_download, handle_download_list

def start():
    """Ponto de entrada que decide entre o modo CLI Padrão e o Shell Interativo."""
    parser = get_parser()
    if len(sys.argv) > 1:
        try:
            args = parser.parse_args()
            if hasattr(args, 'command') and args.command:
                if args.command == 'search': handle_search(args)
                elif args.command == 'download': handle_download(args)
                elif args.command == 'download-list': handle_download_list(args)
            else:
                parser.print_help()
        except argparse.ArgumentError:
             parser.print_help()
    else:
        InteractiveShell(parser).cmdloop()