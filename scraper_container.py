#!/usr/bin/env python
"""
AI Web Scraping Agent - Container Module
This module provides a container for web scraping operations that:
1. Isolates the scraping logic from the main agent
2. Handles request management, retries, and proxies
3. Extracts the requested data from web pages
"""

import requests
import time
import random
import logging
import json
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from urllib.parse import urlparse, urljoin

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("container.log"), logging.StreamHandler()]
)
logger = logging.getLogger("ScraperContainer")

class ScraperContainer:
    """
    Container for web scraping operations.
    Acts as an isolated environment for making requests and parsing responses.
    """
    
    def __init__(self, job_id: str, url: str, selectors: Dict, config: Dict):
        """
        Initialize the scraper container.
        
        Args:
            job_id: Unique identifier for the scraping job
            url: The URL to scrape
            selectors: Dictionary containing selector information
            config: Configuration dictionary
        """
        self.job_id = job_id
        self.url = url
        self.selectors = selectors
        self.config = config
        
        # Initialize HTTP session
        self.session = requests.Session()
        self.rotate_user_agent()
        
        logger.info(f"Container initialized for job {job_id}")
    
    def rotate_user_agent(self):
        """Rotate the user agent to avoid detection"""
        if "user_agents" in self.config and self.config["user_agents"]:
            user_agent = random.choice(self.config["user_agents"])
        else:
            # Default user agent if none provided
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        # Update session headers
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
        
        logger.info(f"Rotated User-Agent: {user_agent}")
    
    def get_page_content(self, url: str) -> Optional[str]:
        """
        Fetch the content of a webpage with retry logic.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content of the page or None if failed
        """
        max_retries = self.config.get("max_retries", 3)
        
        for attempt in range(max_retries):
            try:
                # Add randomized delay
                delay_range = self.config.get("delay_between_requests", [1, 5])
                delay = random.uniform(delay_range[0], delay_range[1])
                logger.info(f"Waiting {delay:.2f} seconds before request...")
                time.sleep(delay)
                
                # Rotate user agent for each attempt
                self.rotate_user_agent()
                
                if self.config.get("use_proxy", False) and self.config.get("proxy_api_key"):
                    # Use proxy service like ScraperAPI
                    proxy_url = f"http://api.scraperapi.com?api_key={self.config['proxy_api_key']}&url={url}"
                    logger.info(f"Using proxy service for request to {urlparse(url).netloc}")
                    response = self.session.get(proxy_url, timeout=30)
                else:
                    # Standard request
                    logger.info(f"Making direct request to {url}")
                    response = self.session.get(url, timeout=15)
                
                # Check if request was successful
                if response.status_code == 200:
                    logger.info(f"Successfully fetched page: {url}")
                    return response.text
                else:
                    logger.warning(f"Failed to fetch page (Status: {response.status_code}): {url}")
            
            except Exception as e:
                logger.error(f"Error during request (Attempt {attempt+1}/{max_retries}): {str(e)}")
            
            # Wait longer between retries (exponential backoff)
            retry_delay = random.uniform(5, 15) * (2 ** attempt)
            logger.info(f"Retrying in {retry_delay:.2f} seconds...")
            time.sleep(retry_delay)
        
        logger.error(f"All {max_retries} attempts to fetch {url} failed")
        return None

    def parse_with_selector(self, html_content: str) -> List[Dict]:
        """
        Parse HTML content using the provided selector information.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            List of dictionaries with extracted data
        """
        if not html_content:
            logger.error("No HTML content to parse")
            return []
        
        results = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get selector type and main selector
            selector_type = self.selectors.get("type", "css")
            main_selector = self.selectors.get("selector", "")
            
            # Find all elements matching the main selector
            if selector_type == "css":
                elements = soup.select(main_selector)
            elif selector_type == "xpath":
                # BeautifulSoup doesn't support XPath natively
                # This is a placeholder - would need lxml for real XPath support
                logger.warning("XPath not directly supported, using CSS fallback")
                elements = soup.select(self.selectors.get("css_fallback", main_selector))
            else:
                logger.error(f"Unsupported selector type: {selector_type}")
                return []
            
            logger.info(f"Found {len(elements)} elements matching the main selector")
            
            # Extract data from each element
            for element in elements:
                item_data = {}
                
                # Process each field extraction rule
                extraction_rules = self.selectors.get("extract", {})
                for field_name, rule in extraction_rules.items():
                    try:
                        # Get the rule type and target selector
                        rule_type = rule.get("type", "text")
                        target_selector = rule.get("selector", "")
                        
                        # Find the target element (if a sub-selector is specified)
                        target_element = element.select_one(target_selector) if target_selector else element
                        
                        # Skip if target element not found
                        if not target_element:
                            item_data[field_name] = ""
                            continue
                        
                        # Extract the data based on rule type
                        if rule_type == "text":
                            item_data[field_name] = target_element.get_text(strip=True)
                        
                        elif rule_type == "attribute":
                            attr_name = rule.get("attribute", "")
                            item_data[field_name] = target_element.get(attr_name, "")
                        
                        elif rule_type == "html":
                            item_data[field_name] = str(target_element)
                        
                        else:
                            logger.warning(f"Unsupported rule type: {rule_type}")
                            item_data[field_name] = ""
                            
                    except Exception as e:
                        logger.error(f"Error extracting field '{field_name}': {str(e)}")
                        item_data[field_name] = ""
                
                # Add metadata to the item
                item_data["scraped_at"] = datetime.now().isoformat()
                item_data["source_url"] = self.url
                
                results.append(item_data)
            
        except Exception as e:
            logger.error(f"Error parsing content: {str(e)}")
        
        return results

    def handle_pagination(self, html_content: str) -> Optional[str]:
        """
        Extract the next page URL from the current page.
        
        Args:
            html_content: HTML content of the current page
            
        Returns:
            URL of the next page or None if no next page found
        """
        if not html_content:
            return None
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Common pagination selectors
            pagination_selectors = [
                "a.next", 
                "a.pagination-next",
                "a[rel='next']",
                ".pagination a:contains('Next')",
                ".pagination a:contains('»')"
            ]
            
            # Try each selector
            for selector in pagination_selectors:
                next_link = soup.select_one(selector)
                if next_link and next_link.has_attr('href'):
                    next_url = next_link['href']
                    
                    # Handle relative URLs
                    if next_url.startswith('/') or not next_url.startswith('http'):
                        next_url = urljoin(self.url, next_url)
                    
                    logger.info(f"Found next page: {next_url}")
                    return next_url
            
            logger.info("No next page found")
            return None
            
        except Exception as e:
            logger.error(f"Error finding next page: {str(e)}")
            return None

    def scrape(self, max_pages: int = 1) -> List[Dict]:
        """
        Perform the scraping operation.
        
        Args:
            max_pages: Maximum number of pages to scrape (for pagination)
            
        Returns:
            List of dictionaries with scraped data
        """
        all_data = []
        current_url = self.url
        current_page = 1
        
        while current_url and current_page <= max_pages:
            logger.info(f"Scraping page {current_page}: {current_url}")
            
            # Get page content
            html_content = self.get_page_content(current_url)
            if not html_content:
                logger.error(f"Failed to get content for page {current_page}")
                break
            
            # Parse the page content
            page_data = self.parse_with_selector(html_content)
            if page_data:
                # Add data from this page
                all_data.extend(page_data)
                logger.info(f"Extracted {len(page_data)} items from page {current_page}")
            else:
                logger.warning(f"No data extracted from page {current_page}")
            
            # Check if we need to paginate
            if max_pages > 1 and current_page < max_pages:
                next_url = self.handle_pagination(html_content)
                if next_url:
                    current_url = next_url
                    current_page += 1
                else:
                    logger.info("No more pages found, ending pagination")
                    break
            else:
                break
        
        logger.info(f"Scraping completed. Total items extracted: {len(all_data)}")
        return all_data


# Standalone execution for testing
if __name__ == "__main__":
    # Example configuration
    test_config = {
        "max_retries": 3,
        "delay_between_requests": [1, 3],
        "use_proxy": False
    }
    
    # Example selectors
    test_selectors = {
        "type": "css",
        "selector": ".product-item",
        "extract": {
            "product_name": {
                "type": "text",
                "selector": ".product-title"
            },
            "price": {
                "type": "text",
                "selector": ".product-price"
            }
        }
    }
    
    # Create container and test
    container = ScraperContainer(
        job_id="test",
        url="https://example.com/products",
        selectors=test_selectors,
        config=test_config
    )
    
    results = container.scrape()
    print(f"Scraped {len(results)} items")