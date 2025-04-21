#!/usr/bin/env python
"""
AI Web Scraping Agent Package
"""

__version__ = "1.0.0"
__author__ = "Kanav"
__email__ = "gathekanav@gmail.com"

from .agent import WebScraperAgent
from .scraper_container import ScraperContainer
from .data_processor import DataProcessor

__all__ = [
    "WebScraperAgent",
    "ScraperContainer",
    "DataProcessor",
]