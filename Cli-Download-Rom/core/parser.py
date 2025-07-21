import argparse
from ..utils.localization import t

def get_parser():
    parser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest='command')
    
    parser_search = subparsers.add_parser('search', help=t.get_string('HELP_SEARCH'))
    parser_search.add_argument('query', type=str, help='O título da ROM a ser buscada.')
    parser_search.add_argument('-p', '--platform', nargs='+', metavar='PLATAFORMA', help='Filtra por uma ou mais plataformas (ex: n64 snes).')
    parser_search.add_argument('-r', '--region', nargs='+', metavar='REGIÃO', help='Filtra por uma ou mais regiões (ex: us eu jp).')
    parser_search.add_argument('--slug', type=str, help='Busca direta por um slug específico.')
    parser_search.add_argument('--rom_id', type=str, help='Busca direta por um rom_id específico.')

    parser_download = subparsers.add_parser('download', help=t.get_string('HELP_DOWNLOAD'))
    group = parser_download.add_mutually_exclusive_group(required=True)
    group.add_argument('--slug', type=str, help='O slug da ROM a ser baixada.')
    group.add_argument('--rom_id', type=str, help='O rom_id da ROM a ser baixada.')
    parser_download.add_argument('--mirror', type=str, help='Prioriza um mirror específico para o download.')
    parser_download.add_argument('--noboxart', action='store_true', help='Não baixa a boxart.')
    parser_download.add_argument('--noaria2c', action='store_true', help='Usa o downloader padrão em vez do aria2c.')
    
    parser_list = subparsers.add_parser('download-list', help=t.get_string('HELP_DOWNLOAD_LIST'))
    parser_list.add_argument('filepath', type=str, nargs='?', default=None, help='Caminho opcional do ficheiro .json.')
    parser_list.add_argument('--mirror', type=str, help='Prioriza um mirror específico para a lista.')
    parser_list.add_argument('--noboxart', action='store_true', help='Não baixa as boxarts da lista.')
    parser_list.add_argument('--noaria2c', action='store_true', help='Usa o downloader padrão para a lista.')
    
    return parser