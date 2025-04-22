"""
Web Scraper Module
This module handles the actual web scraping based on the selectors
provided by the AI agent.
"""

import os
import sys
import json
import logging
import time
import random
import argparse
import re
from typing import Dict, List, Any, Optional
import traceback

import requests
from bs4 import BeautifulSoup
import urllib.parse

from scraper.proxy_manager import ProxyManager
from scraper.dns_protection import DNSProtection
from scraper.url_parser import URLParser

logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self, use_proxy: bool = True, dns_protection: bool = True):
        """
        Initialize the scraper.
        
        Args:
            use_proxy (bool, optional): Whether to use proxy rotation. Defaults to True.
            dns_protection (bool, optional): Whether to use DNS protection. Defaults to True.
        """
        self.proxy_manager = ProxyManager() if use_proxy else None
        self.dns_protection = DNSProtection() if dns_protection else None
        self.url_parser = URLParser()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        logger.info("Scraper initialized")

    def scrape(self, url: str, selectors: Dict[str, Any], pages: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape data from a URL using provided selectors.
        
        Args:
            url (str): URL to scrape
            selectors (dict): Selectors configuration
            pages (int, optional): Number of pages to scrape. Defaults to 1.
            
        Returns:
            list: List of scraped data items
        """
        logger.info(f"Starting scraping of {url} for {pages} pages")
        
        all_items = []
        current_url = url
        
        # Safely access the selectors and pagination configuration
        selector_list = selectors.get('selectors', [])
        pagination = selectors.get('pagination', {'selector': '', 'type': 'link'})
        
        for page in range(1, pages + 1):
            logger.info(f"Scraping page {page} of {pages}: {current_url}")
            
            # Parse the URL to handle any special parameters
            parsed_url = self.url_parser.parse_url(current_url)
            
            # Apply DNS protection measures if enabled
            if self.dns_protection:
                self.dns_protection.pre_request(parsed_url)
            
            # Get proxy if enabled
            proxy = None
            if self.proxy_manager:
                proxy = self.proxy_manager.get_proxy()
                logger.info(f"Using proxy: {proxy}")
            
            # Random delay to be less detectable
            time.sleep(random.uniform(1, 3))
            
            try:
                # Make request with proxy if available
                response = self._make_request(parsed_url, proxy)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch {parsed_url}, status code: {response.status_code}")
                    if page > 1:
                        # If we've already got some data, just return what we have
                        break
                    elif self.proxy_manager:
                        # Try with a different proxy
                        logger.info("Retrying with a different proxy...")
                        proxy = self.proxy_manager.get_proxy(blacklist=[proxy])
                        response = self._make_request(parsed_url, proxy)
                        
                        if response.status_code != 200:
                            logger.error(f"Failed again with status code: {response.status_code}")
                            break
                    else:
                        break
                
                # Parse the HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract data using selectors
                page_items = self._extract_data(soup, selector_list)
                all_items.extend(page_items)
                
                logger.info(f"Extracted {len(page_items)} items from page {page}")
                
                # If we've reached the requested number of pages, stop
                if page >= pages:
                    break
                
                # Get next page URL if pagination is configured
                if pagination and pagination.get('selector'):
                    next_page_url = self._get_next_page_url(soup, pagination, current_url)
                    
                    if not next_page_url or next_page_url == current_url:
                        logger.info("No next page found or next page is the same as current")
                        break
                    
                    current_url = next_page_url
                else:
                    # No pagination configured, so we can only scrape one page
                    logger.info("No pagination selector configured, stopping after first page")
                    break
                
                # Random delay between pages
                time.sleep(random.uniform(2, 5))
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on page {page}: {str(e)}")
                # If we have a proxy, try with a different one
                if self.proxy_manager and proxy:
                    logger.info("Retrying with a different proxy due to request error...")
                    try:
                        proxy = self.proxy_manager.get_proxy(blacklist=[proxy])
                        response = self._make_request(parsed_url, proxy)
                        # Continue with the same logic as above
                    except requests.exceptions.RequestException as e2:
                        logger.error(f"Second request also failed: {str(e2)}")
                        # If we've already got some data, just return what we have
                        if page > 1:
                            break
                        else:
                            raise
                else:
                    # If we've already got some data, just return what we have
                    if page > 1:
                        break
                    else:
                        raise
            except Exception as e:
                logger.error(f"Error on page {page}: {str(e)}")
                logger.error(traceback.format_exc())
                # If we've already got some data, just return what we have
                if page > 1:
                    break
                else:
                    raise
        
        logger.info(f"Scraping completed. Total items scraped: {len(all_items)}")
        return all_items

    def _make_request(self, url: str, proxy: Optional[str] = None) -> requests.Response:
        """
        Make an HTTP request with error handling and proxy support.
        
        Args:
            url (str): URL to request
            proxy (str, optional): Proxy to use. Defaults to None.
            
        Returns:
            requests.Response: Response object
        """
        # Randomize User-Agent for each request to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        ]
        
        headers = dict(self.headers)
        headers['User-Agent'] = random.choice(user_agents)
        
        # Setup proxy if provided
        proxies = None
        if proxy:
            if proxy.startswith('http'):
                proxies = {'http': proxy, 'https': proxy}
            else:
                proxies = {'http': f'http://{proxy}', 'https': f'https://{proxy}'}
        
        # Make the request
        return requests.get(
            url, 
            headers=headers, 
            proxies=proxies, 
            timeout=30,
            allow_redirects=True
        )

    def _extract_data(self, soup: BeautifulSoup, selector_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract data from HTML using selectors.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page
            selector_list (list): List of selector configurations
            
        Returns:
            list: List of extracted data items
        """
        if not selector_list:
            logger.warning("No selectors provided for data extraction")
            return []
        
        # Determine if we're extracting multiple items or just one
        # Look for a 'container' selector which would indicate multiple items
        container_selector = None
        for selector in selector_list:
            if selector.get('name') == 'container' or selector.get('container', False):
                container_selector = selector.get('selector')
                break
        
        # If we have a container selector, extract multiple items
        if container_selector:
            containers = soup.select(container_selector)
            logger.info(f"Found {len(containers)} containers using selector: {container_selector}")
            
            items = []
            for container in containers:
                item = {}
                for selector in selector_list:
                    # Skip the container selector itself
                    if selector.get('name') == 'container' or selector.get('container', False):
                        continue
                    
                    # Extract data from this container
                    value = self._extract_element(container, selector)
                    if value is not None:
                        item[selector.get('name')] = value
                
                if item:  # Only add non-empty items
                    items.append(item)
                    
            return items
            
        else:
            # No container selector, extract a single item
            item = {}
            for selector in selector_list:
                value = self._extract_element(soup, selector)
                if value is not None:
                    item[selector.get('name')] = value
                    
            return [item] if item else []

    def _extract_element(self, soup: BeautifulSoup, selector: Dict[str, Any]) -> Any:
        """
        Extract a single element using a selector configuration.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object to extract from
            selector (dict): Selector configuration
            
        Returns:
            Any: Extracted value
        """
        try:
            selector_str = selector.get('selector', '')
            selector_type = selector.get('type', 'text')
            attribute = selector.get('attribute', '')
            multiple = selector.get('multiple', False)
            post_processing = selector.get('post_processing', '')
            
            if not selector_str:
                logger.warning(f"Empty selector for {selector.get('name')}")
                return None
            
            # Find elements
            elements = soup.select(selector_str)
            
            if not elements:
                logger.debug(f"No elements found for selector: {selector_str}")
                return None if not multiple else []
            
            # Process the elements based on type and whether multiple
            if multiple:
                result = []
                for element in elements:
                    value = self._extract_value(element, selector_type, attribute)
                    if value is not None:
                        result.append(value)
                return result
            else:
                return self._extract_value(elements[0], selector_type, attribute)
                
        except Exception as e:
            logger.error(f"Error extracting element with selector {selector.get('selector')}: {str(e)}")
            return None

    def _extract_value(self, element: Any, selector_type: str, attribute: str = '') -> Any:
        """
        Extract value from an element based on selector type.
        
        Args:
            element: BeautifulSoup element
            selector_type (str): Type of data to extract (text, attribute, etc.)
            attribute (str, optional): Attribute name if type is 'attribute'. Defaults to ''.
            
        Returns:
            Any: Extracted value
        """
        try:
            if selector_type == 'text':
                return element.get_text(strip=True)
            elif selector_type == 'html':
                return str(element)
            elif selector_type == 'attribute':
                return element.get(attribute, '')
            elif selector_type == 'href':
                return element.get('href', '')
            elif selector_type == 'src':
                return element.get('src', '')
            elif selector_type == 'innerText':
                return element.string.strip() if element.string else ''
            else:
                logger.warning(f"Unknown selector type: {selector_type}")
                return element.get_text(strip=True)  # Default to text
        except Exception as e:
            logger.error(f"Error extracting value of type {selector_type}: {str(e)}")
            return None

    def _get_next_page_url(self, soup: BeautifulSoup, pagination: Dict[str, Any], current_url: str) -> Optional[str]:
        """
        Get the URL for the next page.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the current page
            pagination (dict): Pagination configuration
            current_url (str): Current page URL
            
        Returns:
            str: Next page URL or None if not found
        """
        selector = pagination.get('selector', '')
        pagination_type = pagination.get('type', 'link')
        
        if not selector:
            logger.warning("No pagination selector provided")
            return None
        
        try:
            elements = soup.select(selector)
            
            if not elements:
                logger.info(f"No pagination element found with selector: {selector}")
                return None
            
            next_link = elements[0]
            
            # Handle different pagination types
            if pagination_type == 'link':
                href = next_link.get('href')
                if not href:
                    logger.warning("Pagination element has no href attribute")
                    return None
                
                # Convert relative URL to absolute
                if href.startswith('/'):
                    parsed_url = urllib.parse.urlparse(current_url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    next_url = base_url + href
                elif href.startswith('http'):
                    next_url = href
                else:
                    # Handle relative paths that don't start with /
                    parsed_url = urllib.parse.urlparse(current_url)
                    base_path = '/'.join(parsed_url.path.split('/')[:-1])
                    if not base_path.endswith('/'):
                        base_path += '/'
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{base_path}"
                    next_url = base_url + href
                
                return next_url
                
            elif pagination_type == 'button':
                # For buttons that use JavaScript, we might need to parse the onclick attribute
                # or similar to determine the next page. This is a simplified example.
                onclick = next_link.get('onclick', '')
                if 'location.href' in onclick:
                    href_match = re.search(r"location\.href\s*=\s*['\"](.*?)['\"]", onclick)
                    if href_match:
                        href = href_match.group(1)
                        # Convert relative URL to absolute
                        if href.startswith('/'):
                            parsed_url = urllib.parse.urlparse(current_url)
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                            return base_url + href
                        elif href.startswith('http'):
                            return href
                        else:
                            # Relative path
                            parsed_url = urllib.parse.urlparse(current_url)
                            base_path = '/'.join(parsed_url.path.split('/')[:-1])
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{base_path}/"
                            return base_url + href
                
                # If we couldn't parse onclick, just return None
                logger.warning("Could not determine next page URL from button")
                return None
                
            elif pagination_type == 'parameter':
                # For pagination that uses URL parameters
                parsed_url = urllib.parse.urlparse(current_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                
                # Try to find a page parameter
                page_param = pagination.get('parameter', 'page')
                current_page = int(query_params.get(page_param, ['1'])[0])
                next_page = current_page + 1
                
                # Update the query parameters
                query_params[page_param] = [str(next_page)]
                new_query = urllib.parse.urlencode(query_params, doseq=True)
                
                # Construct the new URL
                new_parts = list(parsed_url)
                new_parts[4] = new_query
                return urllib.parse.urlunparse(new_parts)
                
            else:
                logger.warning(f"Unknown pagination type: {pagination_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting next page URL: {str(e)}")
            return None


def main():
    """
    Main function when the module is run directly.
    This function is used when the scraper is run inside a Docker container.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Web Scraper')
    parser.add_argument('config_file', help='Path to the scraper configuration file')
    args = parser.parse_args()
    
    logger.info(f"Starting scraper with config file: {args.config_file}")
    
    try:
        # Read configuration
        with open(args.config_file, 'r') as f:
            config = json.load(f)
        
        url = config.get('url')
        pages = config.get('pages', 1)
        selectors = config.get('selectors', {})
        output_format = config.get('output_format', 'json')
        
        if not url:
            logger.error("No URL provided in configuration")
            sys.exit(1)
        
        if not selectors:
            logger.error("No selectors provided in configuration")
            sys.exit(1)
        
        # Initialize and run the scraper
        scraper = Scraper(use_proxy=True, dns_protection=True)
        scraped_data = scraper.scrape(url, selectors, pages)
        
        # Save the scraped data
        output_file = os.path.join(os.path.dirname(args.config_file), 'scraped_data.json')
        with open(output_file, 'w') as f:
            json.dump(scraped_data, f, indent=2)
        
        logger.info(f"Scraped data saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error running scraper: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()