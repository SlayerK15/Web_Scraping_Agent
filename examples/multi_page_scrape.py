#!/usr/bin/env python
"""
Example script showing how to scrape multiple pages with pagination
"""
import os
import sys
import json
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the agent
from agent import WebScraperAgent
from scraper_container import ScraperContainer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MultiPageExample")

def main():
    """Example of scraping multiple pages with pagination"""
    
    # Initialize the agent
    logger.info("Initializing WebScraperAgent")
    agent = WebScraperAgent()
    
    # Target URL to scrape (first page)
    target_url = "https://example.com/products?page=1"
    
    # Load a selector file
    selector_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "selectors",
        "product_listing.json"
    )
    
    with open(selector_file, 'r') as f:
        selectors = json.load(f)
    
    # Create a job name with timestamp
    job_name = f"MultiPageProducts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create a scraping job
    logger.info(f"Creating scraping job for URL: {target_url}")
    job_id = agent.create_scraping_job(
        url=target_url,
        selectors=selectors,
        job_name=job_name
    )
    
    logger.info(f"Created job with ID: {job_id}")
    
    # Load job information
    job_file = os.path.join("containers", f"{job_id}.json")
    with open(job_file, 'r') as f:
        job_info = json.load(f)
    
    # Set up a scraper container with pagination enabled
    container = ScraperContainer(
        job_id=job_id,
        url=job_info["url"],
        selectors=job_info["selectors"],
        config={
            "max_retries": 3,
            "delay_between_requests": [2, 5],
            "use_proxy": False
        }
    )
    
    # Scrape multiple pages (up to 5)
    logger.info("Starting multi-page scraping (max 5 pages)")
    raw_data = container.scrape(max_pages=5)
    
    logger.info(f"Scraped {len(raw_data)} items across multiple pages")
    
    # Save raw data
    data_file = os.path.join("data", f"{job_id}_raw.json")
    with open(data_file, 'w') as f:
        json.dump(raw_data, f, indent=2)
    
    # Process data and save to Excel using the agent
    logger.info("Processing data and saving to Excel")
    processed_data = agent.process_data(raw_data, job_info["selectors"])
    
    output_file = os.path.join("output", f"{job_name}.xlsx")
    agent.save_to_excel(processed_data, output_file)
    
    logger.info(f"Multi-page scraping completed. Data saved to {output_file}")
    logger.info(f"Total items: {len(processed_data)}")

if __name__ == "__main__":
    main()