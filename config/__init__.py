"""
Config package for the web scraper AI.
This package contains configuration modules and settings for the application.
"""

__version__ = '0.1.0'

from config.settings import load_config, get_config_value

__all__ = ['load_config', 'get_config_value']