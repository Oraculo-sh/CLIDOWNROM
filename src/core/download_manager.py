# -*- coding: utf-8 -*-
"""
CLI Download ROM - Download Manager

Gerenciador de downloads com suporte a múltiplas conexões,
verificação de integridade e retry automático.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

import os
import time
import hashlib
import shutil
import asyncio
import aiofiles
import httpx
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
from loguru import logger
from tqdm import tqdm

from ..api.crocdb_client import ROMEntry
from ..core.directory_manager import DirectoryManager
from ..utils import sanitize_filename


@dataclass
class DownloadProgress:
    """Representa o progresso de um download."""
    filename: str
    total_size: int
    downloaded: int
    speed: float
    eta: float
    percentage: float
    status: str  # 'downloading', 'completed', 'failed', 'verifying', 'moving'
    
    def __post_init__(self):
        if self.total_size > 0:
            self.percentage = (self.downloaded / self.total_size) * 100
        else:
            self.percentage = 0.0


@dataclass
class DownloadResult:
    """Representa o resultado de um download."""
    success: bool
    filename: str
    final_path: Optional[str]
    size: int
    duration: float
    error: Optional[str]
    attempts: int


class MirrorTester:
    """Testa a velocidade e confiabilidade de mirrors."""
    
    def __init__(self, test_timeout: int = 10, test_size: int = 1048576):
        """Inicializa o testador de mirrors.
        
        Args:
            test_timeout: Timeout para teste em segundos
            test_size: Tamanho do arquivo de teste em bytes
        """
        self.test_timeout = test_timeout
        self.test_size = test_size
        self.results = {}
    
    async def test_mirror(self, url: str, host: str, test_dir: Path) -> Tuple[bool, float]:
        """Testa a velocidade de um mirror.
        
        Args:
            url: URL para testar
            host: Nome do host
            test_dir: Diretório para salvar arquivo de teste
            
        Returns:
            Tupla (sucesso, velocidade_mb_s)
        """
        try:
            start_time = time.time()
            downloaded = 0
            
            async with httpx.AsyncClient(timeout=self.test_timeout, follow_redirects=True) as client:
                async with client.stream('GET', url) as response:
                    if response.status_code != 200:
                        return False, 0.0
                    
                    test_file = test_dir / f"test_{host}.tmp"
                    
                    async with aiofiles.open(test_file, 'wb') as f:
                        async for chunk in response.aiter_bytes(8192):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Para quando atingir o tamanho de teste
                            if downloaded >= self.test_size:
                                break
            
            duration = time.time() - start_time
            speed_mb_s = (downloaded / (1024 * 1024)) / duration
            
            # Remove arquivo de teste
            if test_file.exists():
                test_file.unlink()
            
            logger.info(f"Teste de mirror {host}: {speed_mb_s:.2f} MB/s")
            return True, speed_mb_s
            
        except Exception as e:
            logger.warning(f"Erro no teste do mirror {host}: {e}")
            return False, 0.0
    
    async def test_all_mirrors(self, rom_entry: ROMEntry, test_dir: Path) -> List[Tuple[str, float]]:
        """Testa todos os mirrors disponíveis para uma ROM.
        
        Args:
            rom_entry: Entrada da ROM
            test_dir: Diretório para testes
            
        Returns:
            Lista de tuplas (host, velocidade) ordenada por velocidade
        """
        tasks = []
        
        for link in rom_entry.links:
            if link.get('type') == 'Game':
                host = link.get('host', 'unknown')
                url = link.get('url', '')
                
                if url:
                    task = self.test_mirror(url, host, test_dir)
                    tasks.append((host, task))
        
        if not tasks:
            return []
        
        logger.info(f"Testando {len(tasks)} mirrors para {rom_entry.title}")
        
        results = []
        for host, task in tasks:
            success, speed = await task
            if success:
                results.append((host, speed))
        
        # Ordena por velocidade (maior primeiro)
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Teste de mirrors concluído. Melhor: {results[0][0] if results else 'nenhum'}")
        return results


class DownloadManager:
    """Gerenciador de downloads com suporte a múltiplas conexões."""
    
    def __init__(self, 
                 directory_manager: DirectoryManager,
                 max_concurrent: int = 4,
                 chunk_size: int = 8192,
                 timeout: int = 300,
                 max_retries: int = 3,
                 verify_downloads: bool = True):
        """Inicializa o gerenciador de downloads.
        
        Args:
            directory_manager: Gerenciador de diretórios
            max_concurrent: Número máximo de downloads simultâneos
            chunk_size: Tamanho do chunk em bytes
            timeout: Timeout para downloads em segundos
            max_retries: Número máximo de tentativas
            verify_downloads: Se deve verificar integridade dos downloads
        """
        self.dir_manager = directory_manager
        self.max_concurrent = max_concurrent
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_downloads = verify_downloads
        
        self.mirror_tester = MirrorTester()
        self.preferred_hosts = []
        self.progress_callback = None
        
        # Semáforo para controlar downloads simultâneos
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        logger.debug(f"Download Manager inicializado: {max_concurrent} downloads simultâneos")
    
    def set_progress_callback(self, callback: Callable[[DownloadProgress], None]):
        """Define callback para atualizações de progresso.
        
        Args:
            callback: Função que recebe DownloadProgress
        """
        self.progress_callback = callback
    
    def set_preferred_hosts(self, hosts: List[str]):
        """Define hosts preferidos em ordem de prioridade.
        
        Args:
            hosts: Lista de hosts preferidos
        """
        self.preferred_hosts = hosts
        logger.info(f"Hosts preferidos definidos: {hosts}")
    
    async def test_and_rank_mirrors(self, rom_entry: ROMEntry) -> List[str]:
        """Testa e classifica mirrors por velocidade.
        
        Args:
            rom_entry: Entrada da ROM
            
        Returns:
            Lista de hosts ordenados por velocidade
        """
        test_dir = self.dir_manager.ensure_test_host_directory('speed_test')
        
        try:
            results = await self.mirror_tester.test_all_mirrors(rom_entry, test_dir)
            return [host for host, speed in results]
        except Exception as e:
            logger.error(f"Erro ao testar mirrors: {e}")
            return []
    
    async def download_file(self, 
                           url: str, 
                           filename: str, 
                           expected_size: Optional[int] = None) -> DownloadResult:
        """Baixa um arquivo individual.
        
        Args:
            url: URL do arquivo
            filename: Nome do arquivo
            expected_size: Tamanho esperado em bytes
            
        Returns:
            Resultado do download
        """
        # Sanitiza o nome do arquivo
        sanitized_filename = sanitize_filename(filename)
        
        async with self.semaphore:
            return await self._download_file_internal(url, sanitized_filename, expected_size)
    
    async def _download_file_internal(self, 
                                     url: str, 
                                     filename: str, 
                                     expected_size: Optional[int] = None) -> DownloadResult:
        """Implementação interna do download."""
        temp_path = self.dir_manager.get_temp_download_path(filename)
        start_time = time.time()
        attempts = 0
        
        for attempt in range(self.max_retries + 1):
            attempts += 1
            
            try:
                logger.info(f"Iniciando download: {filename} (tentativa {attempt + 1})")
                
                # Atualiza progresso
                if self.progress_callback:
                    progress = DownloadProgress(
                        filename=filename,
                        total_size=expected_size or 0,
                        downloaded=0,
                        speed=0.0,
                        eta=0.0,
                        percentage=0.0,
                        status='downloading'
                    )
                    self.progress_callback(progress)
                
                # Faz o download
                success = await self._perform_download(url, temp_path, filename, expected_size)
                
                if success:
                    # Verifica integridade se habilitado
                    if self.verify_downloads:
                        if self.progress_callback:
                            progress.status = 'verifying'
                            self.progress_callback(progress)
                        
                        if not await self._verify_file(temp_path, expected_size):
                            logger.warning(f"Falha na verificação: {filename}")
                            if temp_path.exists():
                                temp_path.unlink()
                            continue
                    
                    duration = time.time() - start_time
                    file_size = temp_path.stat().st_size if temp_path.exists() else 0
                    
                    # Atualiza progresso final
                    if self.progress_callback:
                        progress.status = 'completed'
                        progress.downloaded = file_size
                        progress.percentage = 100.0
                        self.progress_callback(progress)
                    
                    logger.info(f"Download concluído: {filename} em {duration:.2f}s")
                    
                    return DownloadResult(
                        success=True,
                        filename=filename,
                        final_path=str(temp_path),
                        size=file_size,
                        duration=duration,
                        error=None,
                        attempts=attempts
                    )
                
            except Exception as e:
                logger.error(f"Erro no download (tentativa {attempt + 1}): {e}")
                
                if temp_path.exists():
                    temp_path.unlink()
                
                if attempt < self.max_retries:
                    await asyncio.sleep(1)  # Delay entre tentativas
        
        # Falha após todas as tentativas
        duration = time.time() - start_time
        
        if self.progress_callback:
            progress = DownloadProgress(
                filename=filename,
                total_size=expected_size or 0,
                downloaded=0,
                speed=0.0,
                eta=0.0,
                percentage=0.0,
                status='failed'
            )
            self.progress_callback(progress)
        
        return DownloadResult(
            success=False,
            filename=filename,
            final_path=None,
            size=0,
            duration=duration,
            error="Máximo de tentativas excedido",
            attempts=attempts
        )
    
    async def _perform_download(self, 
                               url: str, 
                               temp_path: Path, 
                               filename: str,
                               expected_size: Optional[int] = None) -> bool:
        """Executa o download do arquivo."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                async with client.stream('GET', url) as response:
                    if response.status_code != 200:
                        logger.error(f"Erro HTTP {response.status_code} para {url}")
                        return False
                    
                    total_size = expected_size
                    if not total_size:
                        content_length = response.headers.get('content-length')
                        if content_length:
                            total_size = int(content_length)
                    
                    downloaded = 0
                    start_time = time.time()
                    
                    async with aiofiles.open(temp_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(self.chunk_size):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Atualiza progresso
                            if self.progress_callback and total_size:
                                elapsed = time.time() - start_time
                                speed = downloaded / elapsed if elapsed > 0 else 0
                                eta = (total_size - downloaded) / speed if speed > 0 else 0
                                
                                progress = DownloadProgress(
                                    filename=filename,
                                    total_size=total_size,
                                    downloaded=downloaded,
                                    speed=speed,
                                    eta=eta,
                                    percentage=(downloaded / total_size) * 100,
                                    status='downloading'
                                )
                                self.progress_callback(progress)
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Erro durante download: {e}")
            return False
    
    async def _verify_file(self, file_path: Path, expected_size: Optional[int] = None) -> bool:
        """Verifica a integridade de um arquivo baixado.
        
        Args:
            file_path: Caminho do arquivo
            expected_size: Tamanho esperado em bytes
            
        Returns:
            True se o arquivo está íntegro
        """
        try:
            if not file_path.exists():
                logger.error(f"Arquivo não encontrado para verificação: {file_path}")
                return False
            
            file_size = file_path.stat().st_size
            
            # Verifica tamanho se fornecido (com tolerância para pequenas diferenças)
            if expected_size and file_size != expected_size:
                # Permite diferença de até 1% ou 100 bytes (o que for maior)
                tolerance = max(100, int(expected_size * 0.01))
                size_diff = abs(file_size - expected_size)
                
                if size_diff > tolerance:
                    logger.error(f"Tamanho incorreto: esperado {expected_size}, obtido {file_size} (diferença: {size_diff} bytes)")
                    return False
                else:
                    logger.warning(f"Pequena diferença de tamanho: esperado {expected_size}, obtido {file_size} (diferença: {size_diff} bytes, dentro da tolerância)")
            
            # Verifica se o arquivo não está vazio
            if file_size == 0:
                logger.error("Arquivo vazio")
                return False
            
            # Verifica se consegue ler o início do arquivo
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)  # Lê os primeiros 1KB
            except Exception as e:
                logger.error(f"Erro ao ler arquivo: {e}")
                return False
            
            logger.debug(f"Verificação bem-sucedida: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro na verificação do arquivo: {e}")
            return False
    
    async def move_to_final_destination(self, 
                                       temp_path: Path, 
                                       platform: str, 
                                       filename: str) -> Optional[str]:
        """Move arquivo do diretório temporário para o destino final.
        
        Args:
            temp_path: Caminho temporário do arquivo
            platform: Plataforma da ROM
            filename: Nome do arquivo
            
        Returns:
            Caminho final do arquivo ou None em caso de erro
        """
        try:
            final_path = self.dir_manager.get_rom_path(platform, filename)
            
            # Garante que o diretório de destino existe
            final_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move o arquivo
            shutil.move(str(temp_path), str(final_path))
            
            logger.info(f"Arquivo movido para: {final_path}")
            return str(final_path)
            
        except Exception as e:
            logger.error(f"Erro ao mover arquivo: {e}")
            return None
    
    async def download_rom(self, rom_entry: ROMEntry, download_boxart: bool = True) -> DownloadResult:
        """Baixa uma ROM completa (arquivo + capa opcional).
        
        Args:
            rom_entry: Entrada da ROM
            download_boxart: Se deve baixar a capa
            
        Returns:
            Resultado do download
        """
        logger.info(f"Iniciando download da ROM: {rom_entry.title}")
        
        # Encontra o melhor link de download
        best_link = rom_entry.get_best_download_link(self.preferred_hosts)
        
        if not best_link:
            logger.error(f"Nenhum link de download encontrado para: {rom_entry.title}")
            return DownloadResult(
                success=False,
                filename=rom_entry.title,
                final_path=None,
                size=0,
                duration=0,
                error="Nenhum link de download disponível",
                attempts=0
            )
        
        url = best_link['url']
        filename = best_link['filename']
        expected_size = best_link.get('size')
        
        # Baixa o arquivo principal
        result = await self.download_file(url, filename, expected_size)
        
        if result.success and result.final_path:
            # Move para destino final
            final_path = await self.move_to_final_destination(
                Path(result.final_path), 
                rom_entry.platform, 
                filename
            )
            
            if final_path:
                result.final_path = final_path
                
                # Baixa capa se solicitado
                if download_boxart and rom_entry.boxart_url:
                    await self._download_boxart(rom_entry)
            
        return result
    
    async def _download_boxart(self, rom_entry: ROMEntry):
        """Baixa a capa de uma ROM.
        
        Args:
            rom_entry: Entrada da ROM
        """
        try:
            if not rom_entry.boxart_url:
                return
            
            # Extrai nome do arquivo da URL
            parsed_url = urlparse(rom_entry.boxart_url)
            boxart_filename = Path(parsed_url.path).name
            
            if not boxart_filename:
                boxart_filename = f"{rom_entry.slug}_boxart.png"
            
            logger.info(f"Baixando capa: {boxart_filename}")
            
            # Baixa a capa
            result = await self.download_file(rom_entry.boxart_url, boxart_filename)
            
            if result.success and result.final_path:
                # Move para diretório de capas
                boxart_path = self.dir_manager.get_boxart_path(rom_entry.platform, boxart_filename)
                boxart_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.move(result.final_path, str(boxart_path))
                logger.info(f"Capa salva em: {boxart_path}")
            else:
                logger.warning(f"Falha no download da capa: {rom_entry.title}")
                
        except Exception as e:
            logger.warning(f"Erro ao baixar capa para {rom_entry.title}: {e}")
    
    async def download_multiple_roms(self, 
                                    rom_entries: List[ROMEntry], 
                                    download_boxart: bool = True) -> List[DownloadResult]:
        """Baixa múltiplas ROMs simultaneamente.
        
        Args:
            rom_entries: Lista de entradas de ROM
            download_boxart: Se deve baixar capas
            
        Returns:
            Lista de resultados de download
        """
        logger.info(f"Iniciando download de {len(rom_entries)} ROMs")
        
        tasks = []
        for rom_entry in rom_entries:
            task = self.download_rom(rom_entry, download_boxart)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Erro no download de {rom_entries[i].title}: {result}")
                processed_results.append(DownloadResult(
                    success=False,
                    filename=rom_entries[i].title,
                    final_path=None,
                    size=0,
                    duration=0,
                    error=str(result),
                    attempts=0
                ))
            else:
                processed_results.append(result)
        
        successful = sum(1 for r in processed_results if r.success)
        logger.info(f"Downloads concluídos: {successful}/{len(rom_entries)} bem-sucedidos")
        
        return processed_results