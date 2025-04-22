"""
Proxy Manager Module
Handles proxy rotation and management for the web scraper.
"""

import os
import json
import logging
import random
import time
import requests
from typing import List, Optional, Dict, Any
import threading

from config.settings import load_config

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self, proxy_file: Optional[str] = None, proxy_service: Optional[str] = None):
        """
        Initialize the proxy manager.
        
        Args:
            proxy_file (str, optional): Path to a file containing proxies. Defaults to None.
            proxy_service (str, optional): Name of a proxy service to use. Defaults to None.
        """
        self.config = load_config().get('proxy', {})
        self.proxy_file = proxy_file or self.config.get('proxy_file')
        self.proxy_service = proxy_service or self.config.get('service')
        self.api_key = os.environ.get(f"{self.proxy_service.upper()}_API_KEY") if self.proxy_service else None
        
        # Proxy rotation settings
        self.max_uses = self.config.get('max_uses', 10)
        self.rotation_interval = self.config.get('rotation_interval', 5 * 60)  # 5 minutes default
        
        # Proxy tracking
        self.proxies = []
        self.proxy_uses = {}
        self.blacklisted_proxies = set()
        self.last_rotation_time = time.time()
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Initialize proxies
        self._initialize_proxies()
        
        logger.info(f"Proxy manager initialized with {len(self.proxies)} proxies")

    def _initialize_proxies(self):
        """Initialize the list of proxies from file or service."""
        try:
            if self.proxy_file and os.path.exists(self.proxy_file):
                self._load_proxies_from_file()
            elif self.proxy_service:
                self._load_proxies_from_service()
            else:
                # Default to a few public proxies as fallback
                # Note: Public proxies are often unreliable, this is just for testing
                self.proxies = [
                    "103.152.112.162:80",
                    "193.239.86.249:3128",
                    "94.231.94.163:3128"
                ]
                logger.warning("Using fallback public proxies. These may be unreliable.")
        except Exception as e:
            logger.error(f"Error initializing proxies: {str(e)}")
            # Set empty list to avoid None
            self.proxies = []

    def _load_proxies_from_file(self):
        """Load proxies from a file."""
        try:
            with open(self.proxy_file, 'r') as f:
                content = f.read()
                
                # Try to parse as JSON first
                try:
                    proxy_data = json.loads(content)
                    if isinstance(proxy_data, list):
                        self.proxies = proxy_data
                    elif isinstance(proxy_data, dict) and 'proxies' in proxy_data:
                        self.proxies = proxy_data['proxies']
                    else:
                        logger.warning("Unexpected JSON format in proxy file, trying line-by-line parsing")
                        self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
                except json.JSONDecodeError:
                    # Not JSON, try line-by-line
                    self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
                    
            logger.info(f"Loaded {len(self.proxies)} proxies from file {self.proxy_file}")
        except Exception as e:
            logger.error(f"Error loading proxies from file: {str(e)}")
            self.proxies = []

    def _load_proxies_from_service(self):
        """Load proxies from a proxy service."""
        try:
            if not self.api_key:
                logger.warning(f"No API key found for {self.proxy_service}. "
                              f"Set {self.proxy_service.upper()}_API_KEY environment variable.")
                self.proxies = []
                return
            
            if self.proxy_service.lower() == 'brightdata':
                self._load_from_brightdata()
            elif self.proxy_service.lower() == 'scraperapi':
                self._load_from_scraperapi()
            elif self.proxy_service.lower() == 'zyte':
                self._load_from_zyte()
            else:
                logger.warning(f"Unsupported proxy service: {self.proxy_service}")
                self.proxies = []
                
            logger.info(f"Loaded {len(self.proxies)} proxies from {self.proxy_service}")
        except Exception as e:
            logger.error(f"Error loading proxies from service {self.proxy_service}: {str(e)}")
            self.proxies = []

    def _load_from_brightdata(self):
        """Load proxies from BrightData."""
        # This is an example of how you might interface with BrightData's API
        # The actual implementation would depend on their API documentation
        try:
            endpoint = "https://api.brightdata.com/proxy/list"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                proxy_data = response.json()
                self.proxies = proxy_data.get('proxies', [])
            else:
                logger.error(f"BrightData API error: {response.status_code} - {response.text}")
                self.proxies = []
        except Exception as e:
            logger.error(f"Error loading proxies from BrightData: {str(e)}")
            self.proxies = []

    def _load_from_scraperapi(self):
        """Load proxies from ScraperAPI."""
        # ScraperAPI typically uses a single endpoint with your API key as a parameter
        # So we'll just create that endpoint here
        self.proxies = [f"http://proxy-server.scraperapi.com:8001?api_key={self.api_key}"]
        logger.info("Using ScraperAPI proxy endpoint")

    def _load_from_zyte(self):
        """Load proxies from Zyte."""
        # Zyte (formerly Scrapinghub) typically provides a smartproxy endpoint
        self.proxies = [f"http://proxy.zyte.com:8011?apikey={self.api_key}"]
        logger.info("Using Zyte proxy endpoint")

    def get_proxy(self, blacklist: Optional[List[str]] = None) -> Optional[str]:
        """
        Get a proxy from the pool.
        
        Args:
            blacklist (list, optional): List of proxies to avoid. Defaults to None.
            
        Returns:
            str: Proxy string or None if no proxies available
        """
        with self.lock:
            # Check if we need to rotate proxies
            current_time = time.time()
            if current_time - self.last_rotation_time > self.rotation_interval:
                logger.info("Rotating proxies due to time interval")
                self._initialize_proxies()
                self.proxy_uses = {}
                self.last_rotation_time = current_time
            
            # Remove blacklisted proxies from consideration
            available_proxies = [p for p in self.proxies if p not in self.blacklisted_proxies]
            if blacklist:
                available_proxies = [p for p in available_proxies if p not in blacklist]
            
            if not available_proxies:
                logger.warning("No proxies available")
                return None
            
            # Find the least used proxy
            least_used_proxy = min(available_proxies, key=lambda p: self.proxy_uses.get(p, 0))
            
            # If the least used proxy has reached max uses, reset counts or get a new batch
            if self.proxy_uses.get(least_used_proxy, 0) >= self.max_uses:
                logger.info("All proxies have reached max uses, refreshing proxy list")
                self._initialize_proxies()
                self.proxy_uses = {}
                return self.get_proxy(blacklist)
            
            # Increment use count
            self.proxy_uses[least_used_proxy] = self.proxy_uses.get(least_used_proxy, 0) + 1
            
            return least_used_proxy

    def blacklist_proxy(self, proxy: str):
        """
        Add a proxy to the blacklist.
        
        Args:
            proxy (str): Proxy to blacklist
        """
        with self.lock:
            self.blacklisted_proxies.add(proxy)
            logger.info(f"Proxy {proxy} added to blacklist")

    def test_proxy(self, proxy: str) -> bool:
        """
        Test if a proxy is working.
        
        Args:
            proxy (str): Proxy to test
            
        Returns:
            bool: True if the proxy is working, False otherwise
        """
        try:
            proxies = {'http': proxy, 'https': proxy} if not proxy.startswith('http') else {'http': proxy, 'https': proxy}
            response = requests.get(
                'https://www.google.com', 
                proxies=proxies, 
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Proxy {proxy} test failed: {str(e)}")
            return False

    def test_all_proxies(self) -> Dict[str, bool]:
        """
        Test all proxies and return their status.
        
        Returns:
            dict: Dictionary mapping proxies to their status (True if working)
        """
        results = {}
        for proxy in self.proxies:
            results[proxy] = self.test_proxy(proxy)
            # Sleep to avoid overloading
            time.sleep(1)
        
        # Update the blacklist based on test results
        for proxy, status in results.items():
            if not status:
                self.blacklist_proxy(proxy)
        
        return results

    def get_random_proxy(self) -> Optional[str]:
        """
        Get a random proxy from the pool.
        
        Returns:
            str: Random proxy or None if no proxies available
        """
        with self.lock:
            available_proxies = [p for p in self.proxies if p not in self.blacklisted_proxies]
            
            if not available_proxies:
                logger.warning("No proxies available for random selection")
                return None
            
            return random.choice(available_proxies)