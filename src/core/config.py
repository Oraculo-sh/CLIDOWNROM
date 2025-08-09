# -*- coding: utf-8 -*-
"""
CLI Download ROM - Configuration Manager

Gerenciador de configurações da aplicação.
Carrega e gerencia configurações de arquivo YAML.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class ConfigManager:
    """Gerenciador de configurações da aplicação."""
    
    DEFAULT_CONFIG = {
        'api': {
            'base_url': 'https://api.crocdb.net',
            'timeout': 30,
            'max_retries': 3,
            'retry_delay': 1
        },
        'download': {
            'max_concurrent': 4,
            'chunk_size': 8192,
            'verify_downloads': True,
            'download_boxart': True,
            'preferred_hosts': [],
            'timeout': 300
        },
        'cache': {
            'enabled': True,
            'ttl_hours': 24,
            'max_size_mb': 100
        },
        'interface': {
            'language': 'auto',
            'theme': 'default',
            'show_progress': True,
            'confirm_downloads': True
        },
        'logging': {
            'level': 'INFO',
            'file_enabled': True,
            'console_enabled': True,
            'max_log_files': 10,
            'max_log_size_mb': 10
        },
        'directories': {
            'roms': 'ROMS',
            'temp': 'TEMP',
            'logs': 'logs',
            'cache': 'cache'
        },
        'performance': {
            'test_mirrors': True,
            'mirror_test_timeout': 10,
            'mirror_test_file_size': 1048576  # 1MB
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Inicializa o gerenciador de configurações.
        
        Args:
            config_path: Caminho para o arquivo de configuração personalizado.
        """
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self.config = self.DEFAULT_CONFIG.copy()
        self.user_config_path = self._get_user_config_path()
    
    def _get_default_config_path(self) -> Path:
        """Retorna o caminho padrão do arquivo de configuração."""
        return Path.cwd() / 'config' / 'config.yml'
    
    def _get_user_config_path(self) -> Path:
        """Retorna o caminho do arquivo de configuração do usuário."""
        return Path.cwd() / 'config' / 'user_config.yml'
    
    def load_config(self) -> bool:
        """Carrega as configurações dos arquivos.
        
        Returns:
            True se as configurações foram carregadas com sucesso.
        """
        try:
            # Carrega configuração padrão se existir
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    default_config = yaml.safe_load(f)
                    if default_config:
                        self._merge_config(self.config, default_config)
                        logger.info(f"Configuração padrão carregada: {self.config_path}")
            
            # Carrega configuração do usuário se existir
            if self.user_config_path.exists():
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._merge_config(self.config, user_config)
                        logger.info(f"Configuração do usuário carregada: {self.user_config_path}")
            
            # Carrega variáveis de ambiente
            self._load_env_variables()
            
            # Valida configurações
            self._validate_config()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            return False
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Mescla configurações recursivamente.
        
        Args:
            base: Configuração base
            override: Configuração para sobrescrever
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _load_env_variables(self):
        """Carrega configurações de variáveis de ambiente."""
        env_mappings = {
            'CLIDOWNROM_API_URL': ('api', 'base_url'),
            'CLIDOWNROM_LANGUAGE': ('interface', 'language'),
            'CLIDOWNROM_LOG_LEVEL': ('logging', 'level'),
            'CLIDOWNROM_MAX_CONCURRENT': ('download', 'max_concurrent'),
            'CLIDOWNROM_CACHE_TTL': ('cache', 'ttl_hours')
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                if section not in self.config:
                    self.config[section] = {}
                
                # Converte tipos quando necessário
                if key in ['max_concurrent', 'ttl_hours']:
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning(f"Valor inválido para {env_var}: {value}")
                        continue
                
                self.config[section][key] = value
                logger.debug(f"Configuração carregada de variável de ambiente: {env_var}")
    
    def _validate_config(self):
        """Valida as configurações carregadas."""
        # Valida URL da API
        api_url = self.config['api']['base_url']
        if not api_url.startswith(('http://', 'https://')):
            raise ValueError(f"URL da API inválida: {api_url}")
        
        # Valida valores numéricos
        numeric_validations = [
            ('api', 'timeout', 1, 300),
            ('api', 'max_retries', 0, 10),
            ('download', 'max_concurrent', 1, 20),
            ('download', 'chunk_size', 1024, 1048576),
            ('cache', 'ttl_hours', 1, 168),  # 1 hora a 1 semana
            ('cache', 'max_size_mb', 10, 1000)
        ]
        
        for section, key, min_val, max_val in numeric_validations:
            value = self.config[section][key]
            if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                logger.warning(
                    f"Valor inválido para {section}.{key}: {value}. "
                    f"Usando valor padrão: {self.DEFAULT_CONFIG[section][key]}"
                )
                self.config[section][key] = self.DEFAULT_CONFIG[section][key]
        
        # Valida idioma
        valid_languages = ['auto', 'pt-BR', 'en-US', 'es-ES', 'fr-FR']
        language = self.config['interface']['language']
        if language not in valid_languages:
            logger.warning(f"Idioma inválido: {language}. Usando 'auto'")
            self.config['interface']['language'] = 'auto'
        
        # Valida nível de log
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        log_level = self.config['logging']['level'].upper()
        if log_level not in valid_log_levels:
            logger.warning(f"Nível de log inválido: {log_level}. Usando 'INFO'")
            self.config['logging']['level'] = 'INFO'
        else:
            self.config['logging']['level'] = log_level
    
    def save_config(self, user_config: bool = True) -> bool:
        """Salva as configurações em arquivo.
        
        Args:
            user_config: Se True, salva como configuração do usuário.
            
        Returns:
            True se as configurações foram salvas com sucesso.
        """
        try:
            target_path = self.user_config_path if user_config else self.config_path
            
            # Garante que o diretório existe
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            logger.info(f"Configurações salvas: {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            return False
    
    def create_default_config(self) -> bool:
        """Cria o arquivo de configuração padrão.
        
        Returns:
            True se o arquivo foi criado com sucesso.
        """
        try:
            # Garante que o diretório existe
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False,
                         allow_unicode=True, indent=2)
            
            logger.info(f"Arquivo de configuração padrão criado: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar arquivo de configuração padrão: {e}")
            return False
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """Obtém um valor de configuração.
        
        Args:
            section: Seção da configuração
            key: Chave específica (opcional)
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração ou valor padrão.
        """
        try:
            if key is None:
                return self.config.get(section, default)
            else:
                return self.config.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """Define um valor de configuração.
        
        Args:
            section: Seção da configuração
            key: Chave da configuração
            value: Valor a ser definido
            
        Returns:
            True se o valor foi definido com sucesso.
        """
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = value
            return True
            
        except Exception as e:
            logger.error(f"Erro ao definir configuração {section}.{key}: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """Retorna todas as configurações.
        
        Returns:
            Dicionário com todas as configurações.
        """
        return self.config.copy()
    
    def reset_to_defaults(self) -> bool:
        """Reseta as configurações para os valores padrão.
        
        Returns:
            True se as configurações foram resetadas com sucesso.
        """
        try:
            self.config = self.DEFAULT_CONFIG.copy()
            logger.info("Configurações resetadas para valores padrão")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao resetar configurações: {e}")
            return False