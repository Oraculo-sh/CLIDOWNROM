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
from copy import deepcopy


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
            'logs': 'logs'
            # 'cache' removido: agora segue automaticamente o diretório TEMP
        },
        # --- NEW: search defaults ---
        'search': {
            'max_results': 100,
            'results_per_page': 10
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
        self.config = deepcopy(self.DEFAULT_CONFIG)
        # Snapshot do estado carregado para detecção de mudanças
        self._loaded_snapshot: Dict[str, Any] = {}
        self.load_config()
        # guarda snapshot após carregar/validar
        self._loaded_snapshot = deepcopy(self.config)
    
    def _get_default_config_path(self) -> Path:
        """Retorna o caminho padrão do arquivo de configuração."""
        return Path.cwd() / 'src' / 'config' / 'config.yml'

    def load_config(self) -> bool:
        """Carrega as configurações do arquivo e ambiente.
        
        Returns:
            True se as configurações foram carregadas com sucesso.
        """
        try:
            # Começa pelos defaults em código
            self.config = deepcopy(self.DEFAULT_CONFIG)

            # Carrega overrides de config.yml (se existir)
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self._merge_config(self.config, file_config)
                        logger.info(f"Configuração carregada: {self.config_path}")
            else:
                # Aviso quando arquivo não existir; seguir com defaults e env vars
                logger.warning(f"Arquivo de configuração não encontrado em {self.config_path}. Usando valores padrão em memória.")
            
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

    # +++ NEW: language normalization helper +++
    def _normalize_language(self, lang: Any) -> str:
        """Normaliza o código de idioma para o formato suportado.
        Aceita variações como en, pt, es, ru, hi, ja, zh e formatos com hífen
        (ex.: en-US, pt-BR, es-ES), mapeando para códigos canônicos.
        """
        try:
            s = str(lang).strip().lower()
        except Exception:
            return 'auto'
        if not s:
            return 'auto'
        s = s.replace('-', '_')

        # Aliases curtos para códigos canônicos
        short_aliases = {
            'en': 'en_us',
            'pt': 'pt_br',
            'es': 'es_es',
            'ru': 'ru_ru',
            'hi': 'hi_in',
            'ja': 'ja_jp',
            'zh': 'zh_cn',  # padrão para simplificado
        }
        if s in short_aliases:
            s = short_aliases[s]

        # Conjunto de idiomas suportados
        supported = {
            'en_us',
            'pt_br',
            'es_es',
            'ru_ru',
            'hi_in',
            'ja_jp',
            'zh_cn',
        }
        return s if (s in supported or s == 'auto') else 'auto'

    def _validate_config(self):
        """Valida as configurações carregadas."""
        # Valida URL da API
        api_url = self.config['api']['base_url']
        if not isinstance(api_url, str) or not api_url.startswith(('http://', 'https://')):
            logger.warning(
                f"URL da API inválida: {api_url}. Usando valor padrão: {self.DEFAULT_CONFIG['api']['base_url']}"
            )
            self.config['api']['base_url'] = self.DEFAULT_CONFIG['api']['base_url']
        
        # Valida valores numéricos
        numeric_validations = [
            ('api', 'timeout', 1, 300),
            ('api', 'max_retries', 0, 10),
            ('download', 'max_concurrent', 1, 20),
            ('download', 'chunk_size', 1024, 1048576),
            ('cache', 'ttl_hours', 1, 168),  # 1 hora a 1 semana
            ('cache', 'max_size_mb', 10, 1000),
            # --- NEW: search validation ---
            ('search', 'max_results', 1, 1000),
            ('search', 'results_per_page', 1, 200),
        ]
        
        for section, key, min_val, max_val in numeric_validations:
            value = self.config[section][key]
            if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                logger.warning(
                    f"Valor inválido para {section}.{key}: {value}. "
                    f"Usando valor padrão: {self.DEFAULT_CONFIG[section][key]}"
                )
                self.config[section][key] = self.DEFAULT_CONFIG[section][key]
        
        # Valida e normaliza idioma
        lang_raw = self.config['interface']['language']
        lang_norm = self._normalize_language(lang_raw)
        if lang_norm != lang_raw:
            logger.info(f"Normalizando interface.language de '{lang_raw}' para '{lang_norm}'")
        self.config['interface']['language'] = lang_norm
        
        # Valida nível de log
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        log_level = self.config['logging']['level'].upper()
        if log_level not in valid_log_levels:
            logger.warning(f"Nível de log inválido: {log_level}. Usando 'INFO'")
            self.config['logging']['level'] = 'INFO'
        else:
            self.config['logging']['level'] = log_level
    
    def save_config(self) -> bool:
        """Salva as configurações em arquivo somente se houver mudanças desde o último carregamento.
        
        Returns:
            True se as configurações foram salvas com sucesso ou não havia mudanças.
        """
        try:
            # Se não houve mudanças, não grava
            if self._loaded_snapshot == self.config:
                logger.debug("Nenhuma alteração na configuração; não é necessário salvar.")
                return True

            # Garante que o diretório exista
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            logger.info(f"Configurações salvas: {self.config_path}")
            # Atualiza snapshot após salvar
            self._loaded_snapshot = deepcopy(self.config)
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
        
        Suporta dois formatos de chamada:
        - get('section') ou get('section', 'key', default)
        - get('section.key', default)
        
        Também tolera mau uso comum onde o segundo argumento é o "default"
        em vez de "key" (ex.: get('api', {}) ).
        
        Args:
            section: Seção da configuração ou caminho pontuado (ex.: 'logging.level')
            key: Chave específica (opcional quando "section" não é pontuado)
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração ou valor padrão.
        """
        try:
            # Caso: segundo argumento foi passado como default (mau uso)
            if key is not None and not isinstance(key, str):
                default = key
                key = None
            
            # Suporte a caminho pontuado (ex.: 'logging.level')
            if key is None and isinstance(section, str) and '.' in section:
                parts = section.split('.')
                current: Any = self.config
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        return default
                return current
            
            # Comportamento padrão (seção e chave separadas)
            if key is None:
                return self.config.get(section, default)
            else:
                return self.config.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def set(self, section: str, key: Any = None, value: Any = None) -> bool:
        """Define um valor de configuração.
        
        Suporta dois formatos de chamada:
        - set('section', 'key', value)
        - set('section.key', value)
        
        Args:
            section: Seção ou caminho pontuado (ex.: 'logging.level')
            key: Chave da configuração OU valor quando usar caminho pontuado
            value: Valor a ser definido (obrigatório quando "key" for a chave)
            
        Returns:
            True se o valor foi definido com sucesso.
        """
        try:
            # Modo caminho pontuado: set('logging.level', 'DEBUG')
            if value is None and isinstance(section, str) and '.' in section and key is not None:
                value = key
                parts = section.split('.')
                current = self.config
                for part in parts[:-1]:
                    if part not in current or not isinstance(current[part], dict):
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
                return True
            
            # Modo padrão: set('logging', 'level', 'DEBUG')
            if not isinstance(key, str):
                raise ValueError("Parâmetros inválidos para set: esperava (section, key, value) ou ('section.key', value)")
            if section not in self.config or not isinstance(self.config[section], dict):
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
        return deepcopy(self.config)
    
    def reset_to_defaults(self) -> bool:
        """Reseta as configurações para os valores padrão.
        
        Returns:
            True se as configurações foram resetadas com sucesso.
        """
        try:
            self.config = deepcopy(self.DEFAULT_CONFIG)
            logger.info("Configurações resetadas para valores padrão")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao resetar configurações: {e}")
            return False