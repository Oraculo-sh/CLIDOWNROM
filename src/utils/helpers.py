# -*- coding: utf-8 -*-
"""
CLI Download ROM - Helper Utilities

Funções auxiliares para formatação, validação, busca e outras operações comuns.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

import re
import os
import time
import hashlib
import platform
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse
from unidecode import unidecode
from Levenshtein import distance as levenshtein_distance
from loguru import logger


def format_file_size(size_bytes: int) -> str:
    """Formata tamanho de arquivo em formato legível.
    
    Args:
        size_bytes: Tamanho em bytes
        
    Returns:
        String formatada (ex: "1.5 GB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """Formata duração em formato legível.
    
    Args:
        seconds: Duração em segundos
        
    Returns:
        String formatada (ex: "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_speed(bytes_per_second: float) -> str:
    """Formata velocidade de download.
    
    Args:
        bytes_per_second: Velocidade em bytes por segundo
        
    Returns:
        String formatada (ex: "1.5 MB/s")
    """
    return f"{format_file_size(int(bytes_per_second))}/s"


def format_eta(seconds: float) -> str:
    """Formata tempo estimado de conclusão.
    
    Args:
        seconds: Segundos restantes
        
    Returns:
        String formatada
    """
    if seconds <= 0:
        return "--"
    elif seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes}m"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def sanitize_filename(filename: str) -> str:
    """Sanitiza nome de arquivo removendo caracteres inválidos.
    
    Args:
        filename: Nome do arquivo original
        
    Returns:
        Nome sanitizado
    """
    import html
    
    # Decodifica entidades HTML
    sanitized = html.unescape(filename)
    
    # Remove caracteres inválidos para nomes de arquivo
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', sanitized)
    
    # Remove espaços extras e pontos no final
    sanitized = sanitized.strip(' .')
    
    # Limita o tamanho do nome
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200-len(ext)] + ext
    
    return sanitized


def normalize_text(text: str) -> str:
    """Normaliza texto para comparação.
    
    Args:
        text: Texto original
        
    Returns:
        Texto normalizado
    """
    # Remove acentos e converte para ASCII
    normalized = unidecode(text)
    
    # Converte para minúsculas
    normalized = normalized.lower()
    
    # Remove caracteres especiais, mantendo apenas letras, números e espaços
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
    
    # Remove espaços extras
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def calculate_similarity(text1: str, text2: str) -> float:
    """Calcula similaridade entre dois textos usando distância de Levenshtein.
    
    Args:
        text1: Primeiro texto
        text2: Segundo texto
        
    Returns:
        Valor de similaridade entre 0.0 e 1.0
    """
    if not text1 or not text2:
        return 0.0
    
    # Normaliza os textos
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    
    if norm1 == norm2:
        return 1.0
    
    # Calcula distância de Levenshtein
    max_len = max(len(norm1), len(norm2))
    if max_len == 0:
        return 1.0
    
    distance = levenshtein_distance(norm1, norm2)
    similarity = 1.0 - (distance / max_len)
    
    return max(0.0, similarity)


def extract_year_from_title(title: str) -> Optional[int]:
    """Extrai ano do título de um jogo.
    
    Args:
        title: Título do jogo
        
    Returns:
        Ano extraído ou None
    """
    # Procura por padrões de ano (1980-2030)
    year_patterns = [
        r'\b(19[8-9]\d|20[0-3]\d)\b',  # Anos entre 1980-2030
        r'\((19[8-9]\d|20[0-3]\d)\)',   # Anos entre parênteses
        r'\[(19[8-9]\d|20[0-3]\d)\]'    # Anos entre colchetes
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, title)
        if match:
            return int(match.group(1))
    
    return None


def extract_region_from_title(title: str) -> List[str]:
    """Extrai códigos de região do título.
    
    Args:
        title: Título do jogo
        
    Returns:
        Lista de códigos de região encontrados
    """
    region_patterns = {
        'USA': r'\b(USA?|US|NTSC-U)\b',
        'EUR': r'\b(EUR?|Europe|PAL)\b',
        'JPN': r'\b(JPN?|Japan|NTSC-J)\b',
        'BRA': r'\b(BRA?|Brazil)\b',
        'KOR': r'\b(KOR?|Korea)\b',
        'CHN': r'\b(CHN?|China)\b'
    }
    
    found_regions = []
    title_upper = title.upper()
    
    for region, pattern in region_patterns.items():
        if re.search(pattern, title_upper):
            found_regions.append(region)
    
    return found_regions


def validate_url(url: str) -> bool:
    """Valida se uma URL é válida.
    
    Args:
        url: URL para validar
        
    Returns:
        True se a URL é válida
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def get_file_hash(file_path: Path, algorithm: str = 'md5') -> Optional[str]:
    """Calcula hash de um arquivo.
    
    Args:
        file_path: Caminho do arquivo
        algorithm: Algoritmo de hash (md5, sha1, sha256)
        
    Returns:
        Hash do arquivo ou None em caso de erro
    """
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
        
    except Exception as e:
        logger.error(f"Erro ao calcular hash de {file_path}: {e}")
        return None


def get_system_info() -> Dict[str, str]:
    """Obtém informações do sistema.
    
    Returns:
        Dicionário com informações do sistema
    """
    return {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version()
    }


def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """Cria uma barra de progresso textual.
    
    Args:
        current: Valor atual
        total: Valor total
        width: Largura da barra
        
    Returns:
        String da barra de progresso
    """
    if total <= 0:
        return '[' + ' ' * width + '] 0%'
    
    percentage = min(100, (current / total) * 100)
    filled = int((current / total) * width)
    
    bar = '█' * filled + '░' * (width - filled)
    return f'[{bar}] {percentage:.1f}%'


def truncate_text(text: str, max_length: int, suffix: str = '...') -> str:
    """Trunca texto se exceder o tamanho máximo.
    
    Args:
        text: Texto original
        max_length: Tamanho máximo
        suffix: Sufixo para texto truncado
        
    Returns:
        Texto truncado se necessário
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_file_size(size_str: str) -> Optional[int]:
    """Converte string de tamanho para bytes.
    
    Args:
        size_str: String de tamanho (ex: "1.5 GB")
        
    Returns:
        Tamanho em bytes ou None
    """
    try:
        size_str = size_str.strip().upper()
        
        # Mapeamento de unidades
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4
        }
        
        # Procura por padrão número + unidade
        match = re.match(r'^([0-9.]+)\s*([A-Z]+)$', size_str)
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            
            if unit in units:
                return int(value * units[unit])
        
        # Tenta apenas número (assume bytes)
        try:
            return int(float(size_str))
        except ValueError:
            pass
        
        return None
        
    except Exception:
        return None


def is_valid_platform(platform: str, valid_platforms: List[str]) -> bool:
    """Verifica se uma plataforma é válida.
    
    Args:
        platform: Nome da plataforma
        valid_platforms: Lista de plataformas válidas
        
    Returns:
        True se a plataforma é válida
    """
    if not platform or not valid_platforms:
        return False
    
    platform_normalized = normalize_text(platform)
    
    for valid_platform in valid_platforms:
        if normalize_text(valid_platform) == platform_normalized:
            return True
    
    return False


def find_best_match(query: str, options: List[str], threshold: float = 0.6) -> Optional[str]:
    """Encontra a melhor correspondência para uma consulta.
    
    Args:
        query: Texto de consulta
        options: Lista de opções
        threshold: Limite mínimo de similaridade
        
    Returns:
        Melhor correspondência ou None
    """
    if not query or not options:
        return None
    
    best_match = None
    best_score = 0.0
    
    for option in options:
        score = calculate_similarity(query, option)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = option
    
    return best_match


def clean_temp_files(temp_dir: Path, max_age_hours: int = 24):
    """Remove arquivos temporários antigos.
    
    Args:
        temp_dir: Diretório temporário
        max_age_hours: Idade máxima em horas
    """
    try:
        if not temp_dir.exists():
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        removed_count = 0
        removed_size = 0
        
        for file_path in temp_dir.rglob('*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                
                if file_age > max_age_seconds:
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        removed_count += 1
                        removed_size += file_size
                        logger.debug(f"Arquivo temporário removido: {file_path}")
                    except Exception as e:
                        logger.warning(f"Erro ao remover arquivo temporário {file_path}: {e}")
        
        if removed_count > 0:
            logger.info(f"Limpeza de arquivos temporários: {removed_count} arquivos, {format_file_size(removed_size)}")
        
        # Remove diretórios vazios
        for dir_path in temp_dir.rglob('*'):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                    logger.debug(f"Diretório vazio removido: {dir_path}")
                except Exception:
                    pass
                    
    except Exception as e:
        logger.error(f"Erro na limpeza de arquivos temporários: {e}")


def get_available_disk_space(path: Path) -> int:
    """Obtém espaço disponível em disco.
    
    Args:
        path: Caminho para verificar
        
    Returns:
        Espaço disponível em bytes
    """
    try:
        if platform.system() == 'Windows':
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(str(path)),
                ctypes.pointer(free_bytes),
                None,
                None
            )
            return free_bytes.value
        else:
            stat = os.statvfs(str(path))
            return stat.f_bavail * stat.f_frsize
    except Exception as e:
        logger.error(f"Erro ao obter espaço em disco: {e}")
        return 0


def check_disk_space(path: Path, required_bytes: int) -> bool:
    """Verifica se há espaço suficiente em disco.
    
    Args:
        path: Caminho para verificar
        required_bytes: Bytes necessários
        
    Returns:
        True se há espaço suficiente
    """
    available = get_available_disk_space(path)
    return available >= required_bytes


def create_backup_filename(original_path: Path) -> Path:
    """Cria nome de arquivo de backup.
    
    Args:
        original_path: Caminho original
        
    Returns:
        Caminho do backup
    """
    timestamp = int(time.time())
    name = original_path.stem
    suffix = original_path.suffix
    
    backup_name = f"{name}_backup_{timestamp}{suffix}"
    return original_path.parent / backup_name