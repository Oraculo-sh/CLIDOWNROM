# -*- coding: utf-8 -*-
"""
CLI Download ROM - Internationalization System

Sistema de internacionalização com suporte a múltiplos idiomas.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

import os
import yaml
import locale
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger


class I18nManager:
    """Gerenciador de internacionalização.

    Nota sobre idioma base: 'en_us' é o locale canônico e serve como template
    para todos os demais. Novos locales devem ser criados a partir de
    locales/en_us.yaml. Chaves ausentes em outros locales farão fallback
    automático para 'en_us'.
    """
    
    def __init__(self, locales_dir: Path, default_language: str = 'en_us'):
        """Inicializa o gerenciador de i18n.
        
        Args:
            locales_dir: Diretório dos arquivos de tradução
            default_language: Idioma padrão
        """
        self.locales_dir = locales_dir
        self.default_language = default_language
        self.current_language = default_language
        self.translations = {}
        self.fallback_translations = {}
        
        # Carrega idioma padrão
        self._load_language(default_language, is_fallback=True)
        
        # Detecta idioma do sistema
        system_language = self._detect_system_language()
        if system_language != default_language:
            self.set_language(system_language)
        
        logger.debug(f"I18n Manager inicializado: idioma atual = {self.current_language}")
    
    def _detect_system_language(self) -> str:
        """Detecta o idioma do sistema operacional.
        
        Returns:
            Código do idioma detectado
        """
        try:
            # Tenta obter idioma do sistema
            system_locale = locale.getdefaultlocale()[0]
            
            if system_locale:
                # Converte para código completo minúsculo com underscore (ex: 'pt_BR' -> 'pt_br')
                language_code = system_locale.lower().replace('-', '_')
                
                # Verifica se temos tradução para este idioma
                if self._language_file_exists(language_code):
                    logger.info(f"Idioma do sistema detectado: {language_code}")
                    return language_code
            
            # Tenta variáveis de ambiente
            for env_var in ['LANG', 'LANGUAGE', 'LC_ALL', 'LC_MESSAGES']:
                env_value = os.environ.get(env_var)
                if env_value:
                    language_code = env_value.split('.')[0].lower().replace('-', '_')
                    if self._language_file_exists(language_code):
                        logger.info(f"Idioma detectado via {env_var}: {language_code}")
                        return language_code
            
        except Exception as e:
            logger.warning(f"Erro ao detectar idioma do sistema: {e}")
        
        logger.info(f"Usando idioma padrão: {self.default_language}")
        return self.default_language
    
    def _language_file_exists(self, language_code: str) -> bool:
        """Verifica se existe arquivo de tradução para o idioma.
        
        Args:
            language_code: Código do idioma
            
        Returns:
            True se o arquivo existe
        """
        language_file = self.locales_dir / f"{language_code}.yaml"
        return language_file.exists()
    
    def _load_language(self, language_code: str, is_fallback: bool = False) -> bool:
        """Carrega arquivo de tradução.
        
        Args:
            language_code: Código do idioma
            is_fallback: Se é o idioma de fallback
            
        Returns:
            True se carregado com sucesso
        """
        language_file = self.locales_dir / f"{language_code}.yaml"
        
        try:
            if not language_file.exists():
                logger.warning(f"Arquivo de tradução não encontrado: {language_file}")
                return False
            
            with open(language_file, 'r', encoding='utf-8') as f:
                translations = yaml.safe_load(f) or {}
            
            if is_fallback:
                self.fallback_translations = translations
                logger.debug(f"Traduções de fallback carregadas: {language_code}")
            else:
                self.translations = translations
                logger.debug(f"Traduções carregadas: {language_code}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar traduções de {language_code}: {e}")
            return False
    
    def set_language(self, language_code: str) -> bool:
        """Define o idioma atual.
        
        Args:
            language_code: Código do idioma
            
        Returns:
            True se definido com sucesso
        """
        if language_code == self.current_language:
            return True
        
        if self._load_language(language_code):
            self.current_language = language_code
            logger.info(f"Idioma alterado para: {language_code}")
            return True
        else:
            logger.warning(f"Falha ao definir idioma: {language_code}")
            return False
    
    def get_available_languages(self) -> List[str]:
        """Obtém lista de idiomas disponíveis.
        
        Returns:
            Lista de códigos de idioma
        """
        languages: List[str] = []
        
        try:
            for file_path in self.locales_dir.glob('*.yaml'):
                language_code = file_path.stem
                languages.append(language_code)
        except Exception as e:
            logger.error(f"Erro ao listar idiomas disponíveis: {e}")
        
        return sorted(languages)
    
    def get_language_name(self, language_code: str) -> str:
        """Obtém nome do idioma dinamicamente dos arquivos de tradução.
        
        Args:
            language_code: Código do idioma
            
        Returns:
            Nome do idioma
        """
        # Tenta obter o nome do idioma do próprio arquivo de tradução
        language_file = self.locales_dir / f"{language_code}.yaml"
        
        if language_file.exists():
            try:
                import yaml
                with open(language_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                # Tenta obter o nome do idioma do arquivo
                if isinstance(data, dict):
                    # Procura por chaves comuns que podem conter o nome do idioma
                    language_name = (
                        data.get('language', {}).get('name') or
                        data.get('app', {}).get('language_name') or
                        data.get('meta', {}).get('language_name')
                    )
                    
                    if language_name:
                        return language_name
                        
            except Exception as e:
                logger.debug(f"Erro ao ler nome do idioma de {language_file}: {e}")
        
        # Fallback para nomes conhecidos se não conseguir ler do arquivo
        fallback_names = {
            'en_us': 'English (US)',
            'pt_br': 'Português (Brasil)',
            'es_es': 'Español (España)',
            'fr_fr': 'Français (France)',
            'de_de': 'Deutsch (Deutschland)',
            'it_it': 'Italiano (Italia)',
            'ja_jp': '日本語',
            'ko_kr': '한국어',
            'zh_cn': '中文(简体)',
            'zh_tw': '中文(繁體)',
            'ru_ru': 'Русский',
            'hi_in': 'हिन्दी (भारत)'
        }
        
        return fallback_names.get(language_code, language_code.upper())
    
    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Optional[Any]:
        """Obtém valor aninhado usando notação de ponto.
        
        Args:
            data: Dicionário de dados
            key_path: Caminho da chave (ex: 'menu.file.open')
            
        Returns:
            Valor encontrado ou None
        """
        keys = key_path.split('.')
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return None
    
    def t(self, key: str, **kwargs) -> str:
        """Traduz uma chave.
        
        Args:
            key: Chave de tradução
            **kwargs: Variáveis para interpolação
            
        Returns:
            Texto traduzido
        """
        # Ordem de resolução: idioma atual -> fallback (en_us) -> chave literal
        # Tenta obter tradução no idioma atual
        translation = self._get_nested_value(self.translations, key)
        
        # Se não encontrar, tenta no idioma de fallback
        if translation is None:
            translation = self._get_nested_value(self.fallback_translations, key)
        
        # Se ainda não encontrar, retorna a própria chave
        if translation is None:
            logger.warning(f"Tradução não encontrada: {key}")
            translation = key
        
        # Aplica interpolação de variáveis
        if kwargs and isinstance(translation, str):
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"Erro na interpolação da tradução '{key}': {e}")
        
        return str(translation)
    
    def tn(self, key: str, count: int, **kwargs) -> str:
        """Traduz com suporte a pluralização.
        
        Args:
            key: Chave de tradução
            count: Número para determinar plural
            **kwargs: Variáveis para interpolação
            
        Returns:
            Texto traduzido com pluralização
        """
        # Adiciona count às variáveis
        kwargs['count'] = count
        
        # Determina se é singular ou plural
        if count == 1:
            plural_key = f"{key}.singular"
        else:
            plural_key = f"{key}.plural"
        
        # Tenta obter tradução plural específica
        translation = self._get_nested_value(self.translations, plural_key)
        
        if translation is None:
            translation = self._get_nested_value(self.fallback_translations, plural_key)
        
        # Se não encontrar plural, usa a chave base
        if translation is None:
            return self.t(key, **kwargs)
        
        # Aplica interpolação
        if isinstance(translation, str):
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"Erro na interpolação da tradução plural '{plural_key}': {e}")
        
        return str(translation)
    
    def get_current_language(self) -> str:
        """Obtém o idioma atual.
        
        Returns:
            Código do idioma atual
        """
        return self.current_language
    
    def reload_translations(self) -> bool:
        """Recarrega as traduções do idioma atual.
        
        Returns:
            True se recarregado com sucesso
        """
        logger.info("Recarregando traduções")
        
        # Recarrega fallback
        fallback_success = self._load_language(self.default_language, is_fallback=True)
        
        # Recarrega idioma atual se diferente do padrão
        current_success = True
        if self.current_language != self.default_language:
            current_success = self._load_language(self.current_language)
        
        return fallback_success and current_success


# Instância global do gerenciador de i18n
_i18n_manager: Optional[I18nManager] = None


def init_i18n(locales_dir: Path, default_language: str = 'en_us') -> I18nManager:
    """Inicializa o sistema de i18n.
    
    Args:
        locales_dir: Diretório dos arquivos de tradução
        default_language: Idioma padrão (por convenção, 'en_us' é o fallback canônico)
        
    Returns:
        Instância do gerenciador de i18n
    """
    global _i18n_manager
    _i18n_manager = I18nManager(locales_dir, default_language)
    return _i18n_manager


def get_i18n() -> Optional[I18nManager]:
    """Obtém a instância global do gerenciador de i18n.
    
    Returns:
        Instância do gerenciador ou None se não inicializado
    """
    return _i18n_manager


def t(key: str, **kwargs) -> str:
    """Função de conveniência para tradução.
    
    Args:
        key: Chave de tradução
        **kwargs: Variáveis para interpolação
        
    Returns:
        Texto traduzido
    """
    if _i18n_manager:
        return _i18n_manager.t(key, **kwargs)
    else:
        logger.warning("Sistema de i18n não inicializado")
        return key


def tn(key: str, count: int, **kwargs) -> str:
    """Função de conveniência para tradução com pluralização.
    
    Args:
        key: Chave de tradução
        count: Número para determinar plural
        **kwargs: Variáveis para interpolação
        
    Returns:
        Texto traduzido com pluralização
    """
    if _i18n_manager:
        return _i18n_manager.tn(key, count, **kwargs)
    else:
        logger.warning("Sistema de i18n não inicializado")
        return f"{key} ({count})"