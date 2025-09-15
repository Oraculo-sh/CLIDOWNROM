# -*- coding: utf-8 -*-
"""
CLI Download ROM - Cache Manager

Gerenciador de cache centralizado para dados JSON e binários.
Usa um diretório de cache por namespace dentro de TEMP/cache e aplica TTL e limite de tamanho.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""
from __future__ import annotations

import json
import time
import hashlib
from pathlib import Path
from typing import Any, Optional, Tuple, Dict, List, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from .directory_manager import DirectoryManager
    from .config_manager import ConfigManager


class CacheManager:
    """Gerenciador de cache com TTL e política de limpeza por tamanho (LRU por mtime).

    - Namespaces: cada categoria de cache tem seu subdiretório (ex.: 'search', 'rom_info', 'boxart').
    - TTL: itens expirados são ignorados e removidos sob demanda.
    - Limite de tamanho: quando excedido, remove os itens menos recentes primeiro.
    - Suporte a JSON (texto) e binário (bytes).
    """

    def __init__(
        self,
        directory_manager: "DirectoryManager",
        config_manager: "ConfigManager",
        namespace: str = "general",
    ) -> None:
        self.dm = directory_manager
        self.cfg = config_manager
        self.namespace = self._normalize_namespace(namespace)

        # Diretórios
        self.cache_root: Path = self.dm.get_path("cache")
        self.cache_root.mkdir(parents=True, exist_ok=True)
        self.ns_dir: Path = self.cache_root / self.namespace
        self.ns_dir.mkdir(parents=True, exist_ok=True)

        # Configurações
        cache_cfg = (self.cfg.config or {}).get("cache", {})
        ttl_hours = int(cache_cfg.get("ttl_hours", 24))
        self.ttl_seconds: int = max(0, ttl_hours) * 3600
        max_size_mb = int(cache_cfg.get("max_size_mb", 100))
        self.max_size_bytes: int = max(10, max_size_mb) * 1024 * 1024

        logger.debug(
            f"CacheManager(namespace={self.namespace}, ttl={self.ttl_seconds}s, max_size={self.max_size_bytes}B)"
        )

    # ----------------------- Helpers -----------------------
    def _normalize_namespace(self, ns: str) -> str:
        s = (ns or "general").strip().lower()
        return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in s) or "general"

    def _hash_key(self, key: str) -> str:
        if not isinstance(key, str):
            key = str(key)
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _path_for(self, key: str, ext: str) -> Path:
        return self.ns_dir / f"{self._hash_key(key)}.{ext}"

    def _is_expired(self, path: Path) -> bool:
        if self.ttl_seconds <= 0:
            return False  # TTL desativado
        try:
            mtime = path.stat().st_mtime
            return (time.time() - mtime) > self.ttl_seconds
        except FileNotFoundError:
            return True
        except Exception as e:
            logger.debug(f"Falha ao ler mtime de {path}: {e}")
            return True

    def _touch(self, path: Path) -> None:
        try:
            now = time.time()
            path.touch(exist_ok=True)
            # Atualiza atime/mtime
            os_utime = getattr(__import__("os"), "utime")
            os_utime(path, (now, now))
        except Exception:
            pass

    # ----------------------- JSON API -----------------------
    def get_json(self, key: str) -> Optional[Any]:
        path = self._path_for(key, "json")
        if not path.exists():
            logger.debug(f"Cache miss (json): {key}")
            return None
        if self._is_expired(path):
            logger.debug(f"Cache expired (json): {key}")
            self._safe_delete(path)
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self._touch(path)
            logger.debug(f"Cache hit (json): {key}")
            return data
        except Exception as e:
            logger.debug(f"Falha ao ler json cache {path}: {e}")
            self._safe_delete(path)
            return None

    def set_json(self, key: str, value: Any) -> bool:
        path = self._path_for(key, "json")
        try:
            tmp = path.with_suffix(".json.tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False)
            tmp.replace(path)
            self._enforce_limits()
            logger.debug(f"Cache store (json): {key}")
            return True
        except Exception as e:
            logger.warning(f"Falha ao gravar json cache {path}: {e}")
            return False

    # ----------------------- BYTES API -----------------------
    def get_bytes(self, key: str) -> Optional[bytes]:
        path = self._path_for(key, "bin")
        if not path.exists():
            logger.debug(f"Cache miss (bin): {key}")
            return None
        if self._is_expired(path):
            logger.debug(f"Cache expired (bin): {key}")
            self._safe_delete(path)
            return None
        try:
            data = path.read_bytes()
            self._touch(path)
            logger.debug(f"Cache hit (bin): {key}")
            return data
        except Exception as e:
            logger.debug(f"Falha ao ler bin cache {path}: {e}")
            self._safe_delete(path)
            return None

    def set_bytes(self, key: str, data: bytes) -> bool:
        path = self._path_for(key, "bin")
        try:
            tmp = path.with_suffix(".bin.tmp")
            tmp.write_bytes(data)
            tmp.replace(path)
            self._enforce_limits()
            logger.debug(f"Cache store (bin): {key}")
            return True
        except Exception as e:
            logger.warning(f"Falha ao gravar bin cache {path}: {e}")
            return False

    # ----------------------- Maintenance -----------------------
    def purge_expired(self) -> Tuple[int, int]:
        """Remove itens expirados no namespace atual.
        Returns: (removidos, restantes)
        """
        removed = 0
        total = 0
        for file in self.ns_dir.glob("*.*"):
            if not file.is_file():
                continue
            total += 1
            if self._is_expired(file):
                self._safe_delete(file)
                removed += 1
        logger.debug(f"Cache purge_expired ns={self.namespace}: removed={removed}, total_before={total}")
        return removed, max(0, total - removed)

    def clear_namespace(self) -> int:
        """Limpa todo o namespace.
        Returns: quantidade de arquivos removidos
        """
        count = 0
        for file in self.ns_dir.glob("*.*"):
            if file.is_file():
                if self._safe_delete(file):
                    count += 1
        logger.info(f"Cache clear ns={self.namespace}: removed={count}")
        return count

    def _enforce_limits(self) -> None:
        """Garante que o diretório não ultrapasse o max_size_bytes, removendo LRU."""
        try:
            files = [f for f in self.ns_dir.glob("*.*") if f.is_file()]
            total_size = sum(f.stat().st_size for f in files)
            if total_size <= self.max_size_bytes:
                return
            # Ordena por mtime crescente (mais antigo primeiro)
            files.sort(key=lambda p: p.stat().st_mtime)
            for f in files:
                if total_size <= self.max_size_bytes:
                    break
                size = f.stat().st_size
                if self._safe_delete(f):
                    total_size -= size
            logger.debug(
                f"Cache enforce_limits ns={self.namespace}: size={total_size}B / limit={self.max_size_bytes}B"
            )
        except Exception as e:
            logger.warning(f"Falha ao aplicar limite de cache em ns={self.namespace}: {e}")

    def _safe_delete(self, path: Path) -> bool:
        try:
            if path.exists():
                path.unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.debug(f"Falha ao remover arquivo de cache {path}: {e}")
            return False

    # ----------------------- Info -----------------------
    def stats(self) -> Dict[str, Any]:
        files = [f for f in self.ns_dir.glob("*.*") if f.is_file()]
        total_size = 0
        expired = 0
        for f in files:
            try:
                total_size += f.stat().st_size
                if self._is_expired(f):
                    expired += 1
            except Exception:
                pass
        return {
            "namespace": self.namespace,
            "files": len(files),
            "expired": expired,
            "size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "ttl_seconds": self.ttl_seconds,
            "limit_bytes": self.max_size_bytes,
        }