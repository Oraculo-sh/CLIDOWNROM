import argparse
from ..utils.localization import t

def get_parser():
    """Cria e retorna o parser de argumentos para a aplicação."""
    parser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest='command')
    
    parser_search = subparsers.add_parser('search', help='Busca por uma ROM específica.')
    parser_search.add_argument('query', type=str, help='O título da ROM a ser buscada.')
    parser_search.add_argument('--source', type=str, choices=['api', 'local'], default='api', help='Define a fonte de dados.')
    parser_search.add_argument('-p', '--platform', nargs='+', metavar='PLATAFORMA', help='Filtra por plataformas.')
    parser_search.add_argument('-r', '--region', nargs='+', metavar='REGIÃO', help='Filtra por regiões.')
    
    parser_list = subparsers.add_parser('download-list', help='Baixa uma lista de ROMs.')
    parser_list.add_argument('filepath', type=str, nargs='?', default=None, help='Caminho opcional do ficheiro .json.')
    
    parser_update = subparsers.add_parser('update-db', help='Constrói/atualiza o banco de dados SQLite local.')
    
    return parser