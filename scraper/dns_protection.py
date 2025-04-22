"""
DNS Protection Module
Implements various DNS protection strategies to prevent getting banned
while scraping.
"""

import logging
import random
import socket
import time
from typing import Dict, Any, List, Optional
import dns.resolver

from config.settings import load_config

logger = logging.getLogger(__name__)

class DNSProtection:
    def __init__(self):
        """Initialize DNS protection with configuration."""
        self.config = load_config().get('dns_protection', {})
        
        # Load DNS servers
        self.dns_servers = self.config.get('dns_servers', [
            '8.8.8.8',        # Google
            '8.8.4.4',        # Google
            '1.1.1.1',        # Cloudflare
            '9.9.9.9',        # Quad9
            '208.67.222.222', # OpenDNS
            '208.67.220.220'  # OpenDNS
        ])
        
        # Domain cache to avoid repeated lookups
        self.domain_cache = {}
        
        # Tracking for rate limiting
        self.last_access = {}
        self.rate_limit = self.config.get('rate_limit', 2)  # seconds between requests to same domain
        
        # Request delay settings
        self.min_delay = self.config.get('min_delay', 1)
        self.max_delay = self.config.get('max_delay', 5)
        
        # Retry settings
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 5)
        
        logger.info("DNS Protection initialized")

    def pre_request(self, url: str) -> bool:
        """
        Apply DNS protection measures before making a request.
        
        Args:
            url (str): The URL to be requested
            
        Returns:
            bool: True if the request should proceed, False if it should be delayed
        """
        try:
            # Extract domain from URL
            domain = url.split('//')[-1].split('/')[0]
            
            # Check rate limiting for domain
            current_time = time.time()
            if domain in self.last_access:
                time_since_last = current_time - self.last_access[domain]
                if time_since_last < self.rate_limit:
                    # Sleep to respect rate limit
                    sleep_time = self.rate_limit - time_since_last
                    logger.info(f"Rate limiting for {domain}, sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
            
            # Update last access time
            self.last_access[domain] = current_time
            
            # Random delay to mimic human behavior
            delay = random.uniform(self.min_delay, self.max_delay)
            logger.debug(f"Random delay for {domain}: {delay:.2f} seconds")
            time.sleep(delay)
            
            # Resolve domain with DNS protection
            self.resolve_domain(domain)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in DNS protection pre-request: {str(e)}")
            return False

    def resolve_domain(self, domain: str) -> Optional[str]:
        """
        Resolve a domain to IP address with DNS protection.
        
        Args:
            domain (str): Domain to resolve
            
        Returns:
            str: IP address or None if resolution failed
        """
        # Check cache first
        if domain in self.domain_cache:
            cache_time, ip = self.domain_cache[domain]
            # Cache is valid for 1 hour
            if time.time() - cache_time < 3600:
                logger.debug(f"Using cached IP for {domain}: {ip}")
                return ip
        
        # Choose random DNS server
        dns_server = random.choice(self.dns_servers)
        
        try:
            logger.debug(f"Resolving {domain} using DNS server {dns_server}")
            
            # Create a new resolver
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            resolver.timeout = 5
            resolver.lifetime = 10
            
            # Resolve domain
            answers = resolver.resolve(domain, 'A')
            
            if answers:
                # Get a random IP if multiple are returned
                ip = random.choice([answer.address for answer in answers])
                logger.debug(f"Resolved {domain} to {ip}")
                
                # Cache the result
                self.domain_cache[domain] = (time.time(), ip)
                
                return ip
            else:
                logger.warning(f"No DNS records found for {domain}")
                return None
                
        except Exception as e:
            logger.error(f"DNS resolution failed for {domain}: {str(e)}")
            
            # Try with another DNS server on failure
            for _ in range(self.max_retries):
                try:
                    dns_server = random.choice(self.dns_servers)
                    logger.debug(f"Retrying with DNS server {dns_server}")
                    
                    resolver = dns.resolver.Resolver()
                    resolver.nameservers = [dns_server]
                    
                    answers = resolver.resolve(domain, 'A')
                    
                    if answers:
                        ip = random.choice([answer.address for answer in answers])
                        logger.debug(f"Resolved {domain} to {ip} after retry")
                        
                        # Cache the result
                        self.domain_cache[domain] = (time.time(), ip)
                        
                        return ip
                except:
                    logger.warning(f"Retry failed for DNS resolution of {domain}")
                    time.sleep(self.retry_delay)
            
            return None

    def rotate_user_agent(self) -> str:
        """
        Get a random user agent to use for requests.
        
        Returns:
            str: Random user agent string
        """
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        return random.choice(user_agents)

    def get_request_headers(self, domain: Optional[str] = None) -> Dict[str, str]:
        """
        Generate request headers with anti-detection measures.
        
        Args:
            domain (str, optional): Domain for the request. Defaults to None.
            
        Returns:
            dict: Dictionary of request headers
        """
        user_agent = self.rotate_user_agent()
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        # Add Referer for common sites
        if domain:
            common_referers = {
                'google.com': 'https://www.google.com/',
                'bing.com': 'https://www.bing.com/',
                'yahoo.com': 'https://search.yahoo.com/',
                'duckduckgo.com': 'https://duckduckgo.com/'
            }
            
            # Add a referer that makes sense (not the same as the domain being requested)
            potential_referers = [ref for site, ref in common_referers.items() if site not in domain]
            if potential_referers:
                headers['Referer'] = random.choice(potential_referers)
        
        return headers

    def clear_cache(self):
        """Clear the domain resolution cache."""
        self.domain_cache = {}
        logger.info("DNS cache cleared")