"""
Settings Module
Handles loading and accessing configuration settings.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        config_file (str, optional): Path to configuration file. Defaults to None.
        
    Returns:
        dict: Configuration dictionary
    """
    # Default config file path
    if config_file is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_file = os.path.join(base_dir, 'config', 'settings.json')
    
    # Initialize with default settings
    config = {
        # General settings
        'general': {
            'debug': False,
            'data_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'storage', 'data'),
            'selector_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'storage', 'selectors'),
            'feedback_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'storage', 'feedback'),
            'log_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'),
            'default_output_format': 'csv'
        },
        
        # AI settings
        'ai': {
            'provider': 'anthropic',  # or 'openai'
            'model': 'claude-3-opus-20240229',  # for Anthropic
            'temperature': 0.2,
            'max_tokens': 1000
        },
        
        # Scraper settings
        'scraper': {
            'request_timeout': 30,
            'use_proxy': True,
            'use_dns_protection': True,
            'max_retries': 3,
            'retry_delay': 2,
            'backoff_factor': 2.0,
            'user_agents': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            ]
        },
        
        # Proxy settings
        'proxy': {
            'service': 'brightdata',  # or 'scraperapi', 'zyte'
            'proxy_file': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'proxies.txt'),
            'max_uses': 10,
            'rotation_interval': 300  # 5 minutes
        },
        
        # DNS protection settings
        'dns_protection': {
            'dns_servers': [
                '8.8.8.8',        # Google
                '8.8.4.4',        # Google
                '1.1.1.1',        # Cloudflare
                '9.9.9.9',        # Quad9
                '208.67.222.222', # OpenDNS
                '208.67.220.220'  # OpenDNS
            ],
            'rate_limit': 2,      # seconds between requests to same domain
            'min_delay': 1,       # minimum delay in seconds
            'max_delay': 5,       # maximum delay in seconds
            'max_retries': 3,     # maximum retries for DNS resolution
            'retry_delay': 5      # delay between retries in seconds
        },
        
        # Docker settings
        'docker': {
            'image_name': 'web-scraper-ai',
            'container_name': 'web-scraper-container',
            'use_docker': True
        }
    }
    
    # Load settings from file if it exists
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                
            # Update config with file settings
            _update_config(config, file_config)
            
            logger.info(f"Loaded configuration from {config_file}")
            
        except Exception as e:
            logger.error(f"Error loading configuration from {config_file}: {str(e)}")
            logger.info("Using default configuration")
    else:
        logger.warning(f"Configuration file {config_file} not found, using default configuration")
        
        # Write default config to file
        try:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Created default configuration file at {config_file}")
        except Exception as e:
            logger.error(f"Error creating default configuration file at {config_file}: {str(e)}")
    
    # Load specific service configurations
    _load_service_configs(config)
    
    # Override with environment variables
    _override_with_env(config)
    
    return config

def _update_config(config: Dict[str, Any], updates: Dict[str, Any]) -> None:
    """
    Update configuration recursively.
    
    Args:
        config (dict): Configuration to update
        updates (dict): Updates to apply
    """
    for key, value in updates.items():
        if key in config and isinstance(config[key], dict) and isinstance(value, dict):
            _update_config(config[key], value)
        else:
            config[key] = value

def _load_service_configs(config: Dict[str, Any]) -> None:
    """
    Load service-specific configurations.
    
    Args:
        config (dict): Main configuration dictionary
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Load AI service configuration
    ai_config_file = os.path.join(base_dir, 'config', 'ai_config.json')
    if os.path.exists(ai_config_file):
        try:
            with open(ai_config_file, 'r') as f:
                ai_config = json.load(f)
            _update_config(config['ai'], ai_config)
            logger.info(f"Loaded AI configuration from {ai_config_file}")
        except Exception as e:
            logger.error(f"Error loading AI configuration from {ai_config_file}: {str(e)}")
    
    # Load scraper configuration
    scraper_config_file = os.path.join(base_dir, 'config', 'scraper_config.json')
    if os.path.exists(scraper_config_file):
        try:
            with open(scraper_config_file, 'r') as f:
                scraper_config = json.load(f)
            _update_config(config['scraper'], scraper_config)
            logger.info(f"Loaded scraper configuration from {scraper_config_file}")
        except Exception as e:
            logger.error(f"Error loading scraper configuration from {scraper_config_file}: {str(e)}")

def _override_with_env(config: Dict[str, Any], prefix: str = 'SCRAPER_') -> None:
    """
    Override configuration with environment variables.
    
    Args:
        config (dict): Configuration to update
        prefix (str, optional): Environment variable prefix. Defaults to 'SCRAPER_'.
    """
    # For each environment variable starting with the prefix
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        
        # Remove prefix and split by double underscore to get nested keys
        config_key = key[len(prefix):]
        keys = config_key.split('__')
        
        # Navigate to the correct nested dictionary
        current = config
        for k in keys[:-1]:
            k = k.lower()
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value, converting to appropriate type
        final_key = keys[-1].lower()
        
        # Try to determine the type from the existing value
        if final_key in current:
            existing_value = current[final_key]
            if isinstance(existing_value, bool):
                # Convert to boolean
                current[final_key] = value.lower() in ('true', 'yes', '1', 'y')
            elif isinstance(existing_value, int):
                # Convert to integer
                try:
                    current[final_key] = int(value)
                except ValueError:
                    logger.warning(f"Could not convert environment variable {key}={value} to int")
            elif isinstance(existing_value, float):
                # Convert to float
                try:
                    current[final_key] = float(value)
                except ValueError:
                    logger.warning(f"Could not convert environment variable {key}={value} to float")
            elif isinstance(existing_value, list):
                # Convert to list (comma-separated)
                current[final_key] = [item.strip() for item in value.split(',')]
            else:
                # Keep as string
                current[final_key] = value
        else:
            # No existing value to determine type, try to guess
            if value.lower() in ('true', 'false', 'yes', 'no', 'y', 'n', '1', '0'):
                current[final_key] = value.lower() in ('true', 'yes', 'y', '1')
            elif value.isdigit():
                current[final_key] = int(value)
            elif '.' in value and all(part.isdigit() for part in value.split('.', 1)):
                current[final_key] = float(value)
            elif ',' in value:
                current[final_key] = [item.strip() for item in value.split(',')]
            else:
                current[final_key] = value

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value by key.
    
    Args:
        key (str): Configuration key (can be nested with dots, e.g. 'scraper.timeout')
        default (any, optional): Default value if key not found. Defaults to None.
        
    Returns:
        any: Configuration value
    """
    config = load_config()
    keys = key.split('.')
    
    # Navigate to the requested key
    current = config
    for k in keys:
        if k in current:
            current = current[k]
        else:
            return default
    
    return current