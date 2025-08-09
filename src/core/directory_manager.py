# -*- coding: utf-8 -*-
"""
CLI Download ROM - Directory Manager

Gerenciador de diretórios da aplicação.
Cria e mantém a estrutura de pastas necessária.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List
from loguru import logger


class DirectoryManager:
    """Gerenciador de diretórios da aplicação."""
    
    def __init__(self, base_path: str = None):
        """Inicializa o gerenciador de diretórios.
        
        Args:
            base_path: Caminho base da aplicação. Se None, usa o diretório atual.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self._setup_paths()
    
    def _setup_paths(self):
        """Configura os caminhos dos diretórios."""
        self.paths = {
            'base': self.base_path,
            'roms': self.base_path / 'ROMS',
            'temp': self.base_path / 'TEMP',
            'temp_downloads': self.base_path / 'TEMP' / 'downloads',
            'temp_test': self.base_path / 'TEMP' / 'teste',
            'logs': self.base_path / 'logs',
            'config': self.base_path / 'config',
            'cache': self.base_path / 'cache',
            'locales': self.base_path / 'locales'
        }
    
    def ensure_directories(self) -> bool:
        """Garante que todos os diretórios necessários existam.
        
        Returns:
            True se todos os diretórios foram criados/verificados com sucesso.
        """
        try:
            for name, path in self.paths.items():
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Diretório criado: {path}")
                else:
                    logger.debug(f"Diretório já existe: {path}")
            
            # Cria arquivo .gitkeep nos diretórios vazios
            self._create_gitkeep_files()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar diretórios: {e}")
            return False
    
    def _create_gitkeep_files(self):
        """Cria arquivos .gitkeep em diretórios que devem ser versionados vazios."""
        gitkeep_dirs = ['temp', 'temp_downloads', 'temp_test', 'logs', 'cache']
        
        for dir_name in gitkeep_dirs:
            if dir_name in self.paths:
                gitkeep_path = self.paths[dir_name] / '.gitkeep'
                if not gitkeep_path.exists():
                    gitkeep_path.touch()
    
    def ensure_platform_directory(self, platform: str) -> Path:
        """Garante que o diretório da plataforma existe.
        
        Args:
            platform: Nome da plataforma (ex: 'snes', 'n64')
            
        Returns:
            Caminho para o diretório da plataforma.
        """
        platform_path = self.paths['roms'] / platform
        boxart_path = platform_path / 'boxart'
        
        platform_path.mkdir(parents=True, exist_ok=True)
        boxart_path.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Diretório da plataforma garantido: {platform_path}")
        return platform_path
    
    def ensure_test_host_directory(self, host: str) -> Path:
        """Garante que o diretório de teste do host existe.
        
        Args:
            host: Nome do host/mirror
            
        Returns:
            Caminho para o diretório de teste do host.
        """
        host_path = self.paths['temp_test'] / host
        host_path.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Diretório de teste do host garantido: {host_path}")
        return host_path
    
    def get_path(self, name: str) -> Path:
        """Retorna o caminho de um diretório específico.
        
        Args:
            name: Nome do diretório
            
        Returns:
            Caminho para o diretório.
            
        Raises:
            KeyError: Se o nome do diretório não for encontrado.
        """
        if name not in self.paths:
            raise KeyError(f"Diretório '{name}' não encontrado")
        
        return self.paths[name]
    
    def get_rom_path(self, platform: str, filename: str) -> Path:
        """Retorna o caminho completo para um arquivo ROM.
        
        Args:
            platform: Nome da plataforma
            filename: Nome do arquivo
            
        Returns:
            Caminho completo para o arquivo ROM.
        """
        platform_path = self.ensure_platform_directory(platform)
        return platform_path / filename
    
    def get_boxart_path(self, platform: str, filename: str) -> Path:
        """Retorna o caminho completo para um arquivo de capa.
        
        Args:
            platform: Nome da plataforma
            filename: Nome do arquivo de capa
            
        Returns:
            Caminho completo para o arquivo de capa.
        """
        platform_path = self.ensure_platform_directory(platform)
        return platform_path / 'boxart' / filename
    
    def get_temp_download_path(self, filename: str) -> Path:
        """Retorna o caminho temporário para download.
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            Caminho temporário para o arquivo.
        """
        return self.paths['temp_downloads'] / filename
    
    def clean_temp_directory(self) -> bool:
        """Limpa o diretório temporário.
        
        Returns:
            True se a limpeza foi bem-sucedida.
        """
        try:
            temp_path = self.paths['temp']
            
            if temp_path.exists():
                # Remove todos os arquivos e subdiretórios
                for item in temp_path.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                
                # Recria os subdiretórios necessários
                self.paths['temp_downloads'].mkdir(exist_ok=True)
                self.paths['temp_test'].mkdir(exist_ok=True)
                
                # Recria os arquivos .gitkeep
                self._create_gitkeep_files()
                
                logger.info("Diretório temporário limpo com sucesso")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar diretório temporário: {e}")
            return False
    
    def get_disk_usage(self) -> Dict[str, Dict[str, int]]:
        """Retorna informações de uso de disco dos diretórios principais.
        
        Returns:
            Dicionário com informações de uso de disco.
        """
        usage_info = {}
        
        for name, path in self.paths.items():
            if path.exists():
                try:
                    total_size = 0
                    file_count = 0
                    
                    for item in path.rglob('*'):
                        if item.is_file():
                            total_size += item.stat().st_size
                            file_count += 1
                    
                    usage_info[name] = {
                        'size_bytes': total_size,
                        'size_mb': round(total_size / (1024 * 1024), 2),
                        'file_count': file_count
                    }
                    
                except Exception as e:
                    logger.warning(f"Erro ao calcular uso do diretório {name}: {e}")
                    usage_info[name] = {
                        'size_bytes': 0,
                        'size_mb': 0,
                        'file_count': 0
                    }
        
        return usage_info
    
    def list_platforms(self) -> List[str]:
        """Lista todas as plataformas com ROMs baixadas.
        
        Returns:
            Lista de nomes de plataformas.
        """
        platforms = []
        roms_path = self.paths['roms']
        
        if roms_path.exists():
            for item in roms_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    platforms.append(item.name)
        
        return sorted(platforms)
    
    def get_platform_stats(self, platform: str) -> Dict[str, int]:
        """Retorna estatísticas de uma plataforma específica.
        
        Args:
            platform: Nome da plataforma
            
        Returns:
            Dicionário com estatísticas da plataforma.
        """
        platform_path = self.paths['roms'] / platform
        boxart_path = platform_path / 'boxart'
        
        stats = {
            'rom_count': 0,
            'boxart_count': 0,
            'total_size_bytes': 0
        }
        
        if platform_path.exists():
            # Conta ROMs
            for item in platform_path.iterdir():
                if item.is_file():
                    stats['rom_count'] += 1
                    stats['total_size_bytes'] += item.stat().st_size
            
            # Conta capas
            if boxart_path.exists():
                for item in boxart_path.iterdir():
                    if item.is_file():
                        stats['boxart_count'] += 1
                        stats['total_size_bytes'] += item.stat().st_size
        
        return stats