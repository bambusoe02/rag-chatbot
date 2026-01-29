"""Internationalization utilities for Streamlit frontend."""

import json
import os
from pathlib import Path
from typing import Dict, Optional
import streamlit as st
from loguru import logger

# Translation cache
_translations: Dict[str, Dict] = {}
_translations_loaded = False


def load_translations():
    """Load all translation files."""
    global _translations, _translations_loaded
    
    if _translations_loaded:
        return
    
    locales_dir = Path(__file__).parent.parent / "locales"
    
    if not locales_dir.exists():
        return
    
    for lang_file in locales_dir.glob("*.json"):
        lang_code = lang_file.stem
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                _translations[lang_code] = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load translation {lang_code}: {e}")
    
    _translations_loaded = True


def get_language() -> str:
    """Get current language from session state."""
    if "language" not in st.session_state:
        st.session_state.language = "en"  # Default to English
    return st.session_state.language


def set_language(lang: str):
    """Set current language."""
    st.session_state.language = lang


def t(key: str, **kwargs) -> str:
    """
    Translate a key.
    
    Args:
        key: Translation key (e.g., "common.save")
        **kwargs: Variables to interpolate
        
    Returns:
        Translated string
    """
    load_translations()
    
    lang = get_language()
    lang_dict = _translations.get(lang, _translations.get("en", {}))
    
    # Navigate nested keys
    keys = key.split('.')
    value = lang_dict
    
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            break
    
    # If not found, try English
    if not isinstance(value, str) and lang != "en":
        lang_dict = _translations.get("en", {})
        value = lang_dict
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                break
    
    # If still not found, return key
    if not isinstance(value, str):
        return key
    
    # Interpolate variables
    if kwargs:
        try:
            return value.format(**kwargs)
        except KeyError:
            return value
    
    return value


def get_supported_languages() -> Dict[str, str]:
    """Get supported languages with display names."""
    return {
        "en": "English",
        "pl": "Polski",
        "de": "Deutsch"
    }

