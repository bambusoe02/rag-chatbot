"""Internationalization (i18n) support for multi-language RAG Chatbot."""

import os
import json
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import langdetect
try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0  # For consistent results
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available, using simple language detection")


class LanguageDetector:
    """Language detection utility"""
    
    # Polish characters for simple detection
    POLISH_CHARS = set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')
    
    # Common language patterns
    LANGUAGE_PATTERNS = {
        'pl': ['czy', 'jak', 'gdzie', 'kiedy', 'dlaczego', 'co', 'który', 'która'],
        'de': ['was', 'wie', 'wo', 'wann', 'warum', 'wer', 'welche'],
        'es': ['qué', 'cómo', 'dónde', 'cuándo', 'por qué', 'quién'],
        'fr': ['quoi', 'comment', 'où', 'quand', 'pourquoi', 'qui'],
    }
    
    def detect_language(self, text: str) -> str:
        """
        Detect language from text
        
        Args:
            text: Input text
            
        Returns:
            Language code (en, pl, de, etc.)
        """
        if not text or len(text.strip()) < 3:
            return 'en'  # Default to English
        
        # Try langdetect first (more accurate)
        if LANGDETECT_AVAILABLE:
            try:
                detected = detect(text)
                # Map common variations
                lang_map = {
                    'pl': 'pl',
                    'de': 'de',
                    'es': 'es',
                    'fr': 'fr',
                    'en': 'en',
                }
                return lang_map.get(detected, 'en')
            except Exception as e:
                logger.warning(f"Language detection failed: {e}")
        
        # Fallback to simple detection
        return self._simple_detect(text)
    
    def _simple_detect(self, text: str) -> str:
        """Simple language detection using character sets and patterns"""
        text_lower = text.lower()
        
        # Check for Polish characters
        if any(char in self.POLISH_CHARS for char in text):
            return 'pl'
        
        # Check for language-specific patterns
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            if any(pattern in text_lower for pattern in patterns):
                return lang
        
        # Default to English
        return 'en'


class TranslationManager:
    """Translation manager for backend messages"""
    
    def __init__(self):
        self.translations: Dict[str, Dict[str, str]] = {}
        self.default_language = 'en'
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files"""
        translations_dir = Path(__file__).parent.parent / "frontend" / "locales"
        
        if not translations_dir.exists():
            logger.warning(f"Translations directory not found: {translations_dir}")
            return
        
        for lang_file in translations_dir.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                logger.info(f"Loaded translations for {lang_code}")
            except Exception as e:
                logger.error(f"Failed to load translations for {lang_code}: {e}")
    
    def translate(self, key: str, language: str = 'en', **kwargs) -> str:
        """
        Translate a key to specified language
        
        Args:
            key: Translation key (e.g., "common.save")
            language: Target language code
            **kwargs: Variables to interpolate
            
        Returns:
            Translated string
        """
        # Get translation dict for language
        lang_dict = self.translations.get(language, self.translations.get(self.default_language, {}))
        
        # Navigate nested keys (e.g., "common.save" -> lang_dict["common"]["save"])
        keys = key.split('.')
        value = lang_dict
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                break
        
        # If translation not found, return key
        if not isinstance(value, str):
            logger.warning(f"Translation not found for key: {key} (lang: {language})")
            return key
        
        # Interpolate variables
        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing variable in translation {key}: {e}")
                return value
        
        return value
    
    def get_supported_languages(self) -> list:
        """Get list of supported language codes"""
        return list(self.translations.keys())


# Global instances
language_detector = LanguageDetector()
translation_manager = TranslationManager()


# Helper functions
def detect_language(text: str) -> str:
    """Detect language from text"""
    return language_detector.detect_language(text)


def translate(key: str, language: str = 'en', **kwargs) -> str:
    """Translate a key"""
    return translation_manager.translate(key, language, **kwargs)


def get_supported_languages() -> list:
    """Get supported languages"""
    return translation_manager.get_supported_languages()

