#!/usr/bin/env python
"""
AI Web Scraping Agent - Setup Script
"""

from setuptools import setup, find_packages
import os

# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="web-scraping-agent",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An autonomous agent for web scraping with containerized processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/web-scraping-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
    "console_scripts": [
        "scraper-agent=web_scraping_agent.cli:main",
        "scraper-api=web_scraping_agent.api_server:start",
    ],
},
    include_package_data=True,
    package_data={
        '': ['config/*.json', 'selectors/*.json'],
    },
    # Create directories if they don't exist
    data_files=[
        ('containers', []),
        ('data', []),
        ('output', []),
        ('logs', []),
    ],
)

