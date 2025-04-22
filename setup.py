"""
Package setup script for web-scraper-ai
"""

from setuptools import setup, find_packages

# Read requirements from file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="web-scraper-ai",
    version="0.1.0",
    description="AI-powered web scraper with automatic selector generation",
    author="Web Scraper AI Team",
    author_email="info@example.com",
    url="https://github.com/example/web-scraper-ai",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'webscraper=cli.commands:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
)