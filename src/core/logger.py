# -*- coding: utf-8 -*-
"""
CLI Download ROM - Logging System

Sistema de logging da aplicação.
Configura logs para arquivo e console com rotação automática.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger


class LogManager:
    """Gerenciador de logs da aplicação."""
    
    def __init__(self, log_dir: str = "logs"):
        """Inicializa o gerenciador de logs.
        
        Args:
            log_dir: Diretório para armazenar os logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Caminhos dos arquivos de log
        self.lastlog_path = Path.cwd() / "lastlog.txt"
        self.session_log_path = self._get_session_log_path()
        
        # Remove configurações padrão do loguru
        logger.remove()
        
        # Configurações aplicadas
        self._configured = False
    
    def _get_session_log_path(self) -> Path:
        """Gera o caminho do log da sessão atual.
        
        Returns:
            Caminho para o arquivo de log da sessão.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.log_dir / f"log-{timestamp}.log"
    
    def setup_logging(self, 
                     level: str = "INFO",
                     console_enabled: bool = True,
                     file_enabled: bool = True,
                     max_log_files: int = 10,
                     max_log_size: str = "10 MB") -> bool:
        """Configura o sistema de logging.
        
        Args:
            level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_enabled: Habilita log no console
            file_enabled: Habilita log em arquivo
            max_log_files: Número máximo de arquivos de log
            max_log_size: Tamanho máximo de cada arquivo de log
            
        Returns:
            True se a configuração foi bem-sucedida.
        """
        try:
            # Configuração do console
            if console_enabled:
                logger.add(
                    sys.stderr,
                    level=level,
                    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                           "<level>{level: <8}</level> | "
                           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                           "<level>{message}</level>",
                    colorize=True
                )
            
            # Configuração do arquivo lastlog (sobrescreve a cada execução)
            if file_enabled:
                # Remove lastlog anterior se existir
                if self.lastlog_path.exists():
                    self.lastlog_path.unlink()
                
                logger.add(
                    str(self.lastlog_path),
                    level="DEBUG",  # Lastlog sempre captura tudo
                    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                           "{level: <8} | "
                           "{name}:{function}:{line} - "
                           "{message}",
                    mode="w",  # Sobrescreve o arquivo
                    encoding="utf-8"
                )
                
                # Configuração do log da sessão (com rotação)
                logger.add(
                    str(self.session_log_path),
                    level=level,
                    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                           "{level: <8} | "
                           "{name}:{function}:{line} - "
                           "{message}",
                    rotation=max_log_size,
                    retention=max_log_files,
                    compression="zip",
                    encoding="utf-8"
                )
            
            self._configured = True
            logger.info("Sistema de logging configurado com sucesso")
            logger.info(f"Nível de log: {level}")
            logger.info(f"Console habilitado: {console_enabled}")
            logger.info(f"Arquivo habilitado: {file_enabled}")
            
            if file_enabled:
                logger.info(f"Lastlog: {self.lastlog_path}")
                logger.info(f"Log da sessão: {self.session_log_path}")
            
            return True
            
        except Exception as e:
            print(f"Erro ao configurar logging: {e}")
            return False
    
    def log_download_start(self, rom_name: str, url: str, size: int = None):
        """Registra o início de um download.
        
        Args:
            rom_name: Nome da ROM
            url: URL do download
            size: Tamanho do arquivo em bytes (opcional)
        """
        size_str = f" ({self._format_size(size)})" if size else ""
        logger.info(f"Iniciando download: {rom_name}{size_str}")
        logger.debug(f"URL: {url}")
    
    def log_download_progress(self, rom_name: str, progress: float, speed: str = None):
        """Registra o progresso de um download.
        
        Args:
            rom_name: Nome da ROM
            progress: Progresso em porcentagem (0-100)
            speed: Velocidade de download (opcional)
        """
        speed_str = f" - {speed}" if speed else ""
        logger.debug(f"Download {rom_name}: {progress:.1f}%{speed_str}")
    
    def log_download_complete(self, rom_name: str, duration: float, final_path: str):
        """Registra a conclusão de um download.
        
        Args:
            rom_name: Nome da ROM
            duration: Duração do download em segundos
            final_path: Caminho final do arquivo
        """
        logger.info(f"Download concluído: {rom_name} em {duration:.2f}s")
        logger.info(f"Arquivo salvo em: {final_path}")
    
    def log_download_error(self, rom_name: str, error: str, attempt: int = None):
        """Registra um erro de download.
        
        Args:
            rom_name: Nome da ROM
            error: Descrição do erro
            attempt: Número da tentativa (opcional)
        """
        attempt_str = f" (tentativa {attempt})" if attempt else ""
        logger.error(f"Erro no download{attempt_str}: {rom_name} - {error}")
    
    def log_api_request(self, endpoint: str, params: dict = None):
        """Registra uma requisição à API.
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da requisição (opcional)
        """
        params_str = f" com parâmetros: {params}" if params else ""
        logger.debug(f"Requisição API: {endpoint}{params_str}")
    
    def log_api_response(self, endpoint: str, status_code: int, response_time: float = None):
        """Registra a resposta de uma requisição à API.
        
        Args:
            endpoint: Endpoint da API
            status_code: Código de status HTTP
            response_time: Tempo de resposta em segundos (opcional)
        """
        time_str = f" em {response_time:.3f}s" if response_time else ""
        logger.debug(f"Resposta API {endpoint}: {status_code}{time_str}")
    
    def log_cache_hit(self, key: str):
        """Registra um cache hit.
        
        Args:
            key: Chave do cache
        """
        logger.debug(f"Cache hit: {key}")
    
    def log_cache_miss(self, key: str):
        """Registra um cache miss.
        
        Args:
            key: Chave do cache
        """
        logger.debug(f"Cache miss: {key}")
    
    def log_mirror_test(self, host: str, speed: float, success: bool):
        """Registra o resultado de um teste de mirror.
        
        Args:
            host: Nome do host/mirror
            speed: Velocidade medida em MB/s
            success: Se o teste foi bem-sucedido
        """
        if success:
            logger.info(f"Teste de mirror {host}: {speed:.2f} MB/s")
        else:
            logger.warning(f"Teste de mirror {host}: falhou")
    
    def log_file_verification(self, filename: str, success: bool, error: str = None):
        """Registra o resultado de uma verificação de arquivo.
        
        Args:
            filename: Nome do arquivo
            success: Se a verificação foi bem-sucedida
            error: Descrição do erro (se houver)
        """
        if success:
            logger.info(f"Verificação de arquivo bem-sucedida: {filename}")
        else:
            error_str = f" - {error}" if error else ""
            logger.error(f"Falha na verificação de arquivo: {filename}{error_str}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Formata o tamanho em bytes para uma string legível.
        
        Args:
            size_bytes: Tamanho em bytes
            
        Returns:
            String formatada com o tamanho.
        """
        if size_bytes is None:
            return "tamanho desconhecido"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def get_log_files(self) -> list:
        """Retorna lista de arquivos de log existentes.
        
        Returns:
            Lista de caminhos para arquivos de log.
        """
        log_files = []
        
        # Adiciona lastlog se existir
        if self.lastlog_path.exists():
            log_files.append(self.lastlog_path)
        
        # Adiciona logs da sessão
        if self.log_dir.exists():
            for log_file in self.log_dir.glob("log-*.log*"):
                log_files.append(log_file)
        
        return sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def clean_old_logs(self, keep_days: int = 30) -> int:
        """Remove logs antigos.
        
        Args:
            keep_days: Número de dias para manter os logs
            
        Returns:
            Número de arquivos removidos.
        """
        if not self.log_dir.exists():
            return 0
        
        removed_count = 0
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        try:
            for log_file in self.log_dir.glob("log-*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    removed_count += 1
                    logger.debug(f"Log antigo removido: {log_file}")
            
            if removed_count > 0:
                logger.info(f"Removidos {removed_count} arquivos de log antigos")
            
        except Exception as e:
            logger.error(f"Erro ao limpar logs antigos: {e}")
        
        return removed_count


# Instância global do gerenciador de logs
_log_manager = None


def setup_logging(level: str = "INFO",
                 console_enabled: bool = True,
                 file_enabled: bool = True,
                 max_log_files: int = 10,
                 max_log_size: str = "10 MB") -> bool:
    """Configura o sistema de logging global.
    
    Args:
        level: Nível de log
        console_enabled: Habilita log no console
        file_enabled: Habilita log em arquivo
        max_log_files: Número máximo de arquivos de log
        max_log_size: Tamanho máximo de cada arquivo de log
        
    Returns:
        True se a configuração foi bem-sucedida.
    """
    global _log_manager
    
    if _log_manager is None:
        _log_manager = LogManager()
    
    return _log_manager.setup_logging(
        level=level,
        console_enabled=console_enabled,
        file_enabled=file_enabled,
        max_log_files=max_log_files,
        max_log_size=max_log_size
    )


def get_log_manager() -> Optional[LogManager]:
    """Retorna a instância global do gerenciador de logs.
    
    Returns:
        Instância do LogManager ou None se não configurado.
    """
    return _log_manager