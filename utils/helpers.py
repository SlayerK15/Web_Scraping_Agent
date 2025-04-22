"""
Helper Utilities Module
Contains general helper functions used throughout the application.
"""

import logging
import os
import re
import hashlib
import json
import time
import random
import string
from typing import Any, Dict, List, Optional, Union
import urllib.parse

logger = logging.getLogger(__name__)

def generate_hash(text: str) -> str:
    """
    Generate a deterministic hash from text.
    
    Args:
        text (str): Text to hash
        
    Returns:
        str: Hash string
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename.
    
    Args:
        filename (str): Filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:250] + ext
    
    # Ensure we have a valid filename
    if not sanitized:
        sanitized = 'unnamed_file'
    
    return sanitized

def ensure_dir(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory (str): Directory path
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Created directory: {directory}")

def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Read a JSON file.
    
    Args:
        file_path (str): Path to JSON file
        
    Returns:
        dict: JSON data as dictionary
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON file {file_path}: {str(e)}")
        return {}

def write_json_file(data: Any, file_path: str) -> bool:
    """
    Write data to a JSON file.
    
    Args:
        data (any): Data to write
        file_path (str): Path to JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        directory = os.path.dirname(file_path)
        if directory:
            ensure_dir(directory)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error writing JSON file {file_path}: {str(e)}")
        return False

def retry_function(func: callable, max_retries: int = 3, delay: int = 2, 
                  backoff_factor: float = 2.0, exceptions: tuple = (Exception,),
                  logger: Optional[logging.Logger] = None) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func (callable): Function to retry
        max_retries (int, optional): Maximum number of retries. Defaults to 3.
        delay (int, optional): Initial delay in seconds. Defaults to 2.
        backoff_factor (float, optional): Backoff factor. Defaults to 2.0.
        exceptions (tuple, optional): Exceptions to catch. Defaults to (Exception,).
        logger (Logger, optional): Logger instance. Defaults to None.
        
    Returns:
        any: Result of the function call
    """
    retries = 0
    current_delay = delay
    
    while retries <= max_retries:
        try:
            return func()
        except exceptions as e:
            retries += 1
            if retries > max_retries:
                if logger:
                    logger.error(f"Max retries ({max_retries}) exceeded: {str(e)}")
                raise
            
            if logger:
                logger.warning(f"Retry {retries}/{max_retries} after error: {str(e)}")
            
            # Sleep with jitter
            jitter = random.uniform(0.8, 1.2)
            sleep_time = current_delay * jitter
            time.sleep(sleep_time)
            
            # Increase delay for next retry
            current_delay *= backoff_factor

def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Split a list into chunks of size n.
    
    Args:
        lst (list): List to split
        n (int): Chunk size
        
    Returns:
        list: List of chunks
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    
    Args:
        d (dict): Dictionary to flatten
        parent_key (str, optional): Parent key. Defaults to ''.
        sep (str, optional): Separator. Defaults to '_'.
        
    Returns:
        dict: Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def is_url(text: str) -> bool:
    """
    Check if a string is a valid URL.
    
    Args:
        text (str): String to check
        
    Returns:
        bool: True if string is a valid URL, False otherwise
    """
    try:
        result = urllib.parse.urlparse(text)
        return all([result.scheme, result.netloc])
    except:
        return False

def generate_temp_filename(prefix: str = 'temp', suffix: str = '') -> str:
    """
    Generate a unique temporary filename.
    
    Args:
        prefix (str, optional): Filename prefix. Defaults to 'temp'.
        suffix (str, optional): Filename suffix. Defaults to ''.
        
    Returns:
        str: Temporary filename
    """
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    filename = f"{prefix}_{timestamp}_{random_str}{suffix}"
    return filename

def format_time_elapsed(seconds: float) -> str:
    """
    Format elapsed time in a human-readable format.
    
    Args:
        seconds (float): Elapsed time in seconds
        
    Returns:
        str: Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.2f} hours"

def extract_domain(url: str) -> str:
    """
    Extract domain from a URL.
    
    Args:
        url (str): URL to extract domain from
        
    Returns:
        str: Domain name
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return ""

def truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text (str): String to truncate
        max_length (int, optional): Maximum length. Defaults to 100.
        suffix (str, optional): Suffix to add if truncated. Defaults to '...'.
        
    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries, with values from dict2 taking precedence.
    
    Args:
        dict1 (dict): First dictionary
        dict2 (dict): Second dictionary
        
    Returns:
        dict: Merged dictionary
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

def safe_eval(expr: str, globals_dict: Optional[Dict[str, Any]] = None, 
             locals_dict: Optional[Dict[str, Any]] = None) -> Any:
    """
    Safely evaluate a Python expression.
    
    Args:
        expr (str): Expression to evaluate
        globals_dict (dict, optional): Globals dictionary. Defaults to None.
        locals_dict (dict, optional): Locals dictionary. Defaults to None.
        
    Returns:
        any: Result of evaluation
    """
    # Define a restricted globals dictionary if not provided
    if globals_dict is None:
        globals_dict = {
            "__builtins__": {
                name: getattr(__builtins__, name)
                for name in ['abs', 'all', 'any', 'bool', 'dict', 'float', 'int', 
                             'len', 'list', 'max', 'min', 'range', 'round', 'str', 
                             'sum', 'tuple', 'zip']
            }
        }
    
    try:
        return eval(expr, globals_dict, locals_dict)
    except Exception as e:
        logger.error(f"Error evaluating expression '{expr}': {str(e)}")
        return None

def get_current_timestamp() -> int:
    """
    Get current timestamp in seconds.
    
    Returns:
        int: Current timestamp
    """
    return int(time.time())

def format_timestamp(timestamp: int, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format a timestamp as a string.
    
    Args:
        timestamp (int): Timestamp in seconds
        format_str (str, optional): Format string. Defaults to '%Y-%m-%d %H:%M:%S'.
        
    Returns:
        str: Formatted timestamp
    """
    try:
        return time.strftime(format_str, time.localtime(timestamp))
    except Exception as e:
        logger.error(f"Error formatting timestamp {timestamp}: {str(e)}")
        return str(timestamp)