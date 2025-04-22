"""
URL Parser Module
Handles special URL parsing, especially handling URLs with ampersands
and other special characters.
"""

import logging
import urllib.parse
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class URLParser:
    def __init__(self):
        """Initialize the URL parser."""
        logger.info("URL Parser initialized")

    def parse_url(self, url: str) -> str:
        """
        Parse and sanitize a URL.
        
        Args:
            url (str): URL to parse
            
        Returns:
            str: Parsed and sanitized URL
        """
        logger.debug(f"Parsing URL: {url}")
        
        try:
            # Parse the URL into components
            parsed = urllib.parse.urlparse(url)
            
            # Handle special characters in path
            path = parsed.path
            
            # Handle query parameters
            query_params = self._parse_query_params(parsed.query)
            
            # Rebuild the query string, properly handling special characters
            query_string = self._build_query_string(query_params)
            
            # Reconstruct the URL with proper escaping
            sanitized_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                path,
                parsed.params,
                query_string,
                parsed.fragment
            ))
            
            logger.debug(f"Parsed URL: {sanitized_url}")
            return sanitized_url
            
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {str(e)}")
            # Return the original URL if parsing fails
            return url

    def _parse_query_params(self, query_string: str) -> Dict[str, List[str]]:
        """
        Parse query parameters from a query string, handling special cases.
        
        Args:
            query_string (str): Query string to parse
            
        Returns:
            dict: Dictionary of parsed query parameters
        """
        # Special handling for ampersands in values
        if not query_string:
            return {}
        
        try:
            # Standard parsing
            params = urllib.parse.parse_qs(query_string, keep_blank_values=True)
            
            # Check for potentially problematic values
            for key, values in params.items():
                sanitized_values = []
                for value in values:
                    # Re-parse values with ampersands
                    if '&' in value and '=' in value:
                        logger.debug(f"Detected potential nested query parameters in value: {value}")
                        # This could be a nested query parameter or just an ampersand in a value
                        # We assume it's just a value and encode the ampersand
                        sanitized_value = value.replace('&', '%26')
                        sanitized_values.append(sanitized_value)
                    else:
                        sanitized_values.append(value)
                
                params[key] = sanitized_values
            
            return params
            
        except Exception as e:
            logger.error(f"Error parsing query parameters {query_string}: {str(e)}")
            # Alternative parsing method for problematic query strings
            params = {}
            parts = query_string.split('&')
            
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    key = urllib.parse.unquote(key)
                    value = urllib.parse.unquote(value)
                    
                    if key in params:
                        params[key].append(value)
                    else:
                        params[key] = [value]
                else:
                    # Handle parameters without values
                    key = urllib.parse.unquote(part)
                    params[key] = ['']
            
            return params

    def _build_query_string(self, params: Dict[str, List[str]]) -> str:
        """
        Build a query string from parameters, handling special cases.
        
        Args:
            params (dict): Dictionary of query parameters
            
        Returns:
            str: Built query string
        """
        if not params:
            return ''
        
        parts = []
        
        for key, values in params.items():
            for value in values:
                # Ensure proper encoding
                encoded_key = urllib.parse.quote(key, safe='')
                encoded_value = urllib.parse.quote(value, safe='')
                parts.append(f"{encoded_key}={encoded_value}")
        
        return '&'.join(parts)

    def append_query_param(self, url: str, param: str, value: str) -> str:
        """
        Append a query parameter to a URL.
        
        Args:
            url (str): URL to append to
            param (str): Parameter name
            value (str): Parameter value
            
        Returns:
            str: URL with appended parameter
        """
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # Add the new parameter
            query_params[param] = [value]
            
            # Rebuild the query string
            query_string = urllib.parse.urlencode(query_params, doseq=True)
            
            # Reconstruct the URL
            new_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                query_string,
                parsed.fragment
            ))
            
            return new_url
            
        except Exception as e:
            logger.error(f"Error appending query parameter to {url}: {str(e)}")
            # If something goes wrong, just append the parameter naively
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}{param}={urllib.parse.quote(value)}"

    def get_base_url(self, url: str) -> str:
        """
        Get the base URL (scheme + netloc).
        
        Args:
            url (str): URL to parse
            
        Returns:
            str: Base URL
        """
        try:
            parsed = urllib.parse.urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
        except Exception as e:
            logger.error(f"Error getting base URL from {url}: {str(e)}")
            return url

    def get_domain(self, url: str) -> str:
        """
        Extract the domain from a URL.
        
        Args:
            url (str): URL to parse
            
        Returns:
            str: Domain name
        """
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc
        except Exception as e:
            logger.error(f"Error extracting domain from {url}: {str(e)}")
            # Fallback method
            try:
                # Remove protocol
                domain = url.split('//')[-1]
                # Remove path
                domain = domain.split('/', 1)[0]
                return domain
            except:
                return url

    def join_url(self, base_url: str, relative_path: str) -> str:
        """
        Join a base URL and a relative path.
        
        Args:
            base_url (str): Base URL
            relative_path (str): Relative path
            
        Returns:
            str: Joined URL
        """
        try:
            # Handle special case where relative path already has the domain
            if relative_path.startswith('http'):
                return relative_path
                
            # Make sure base_url ends with a slash if it doesn't have one
            if not base_url.endswith('/'):
                base_url += '/'
                
            # Remove leading slash from relative path if it exists
            if relative_path.startswith('/'):
                relative_path = relative_path[1:]
                
            return urllib.parse.urljoin(base_url, relative_path)
            
        except Exception as e:
            logger.error(f"Error joining URLs {base_url} and {relative_path}: {str(e)}")
            # Simple fallback
            if base_url.endswith('/'):
                if relative_path.startswith('/'):
                    return base_url + relative_path[1:]
                else:
                    return base_url + relative_path
            else:
                if relative_path.startswith('/'):
                    return base_url + relative_path
                else:
                    return base_url + '/' + relative_path