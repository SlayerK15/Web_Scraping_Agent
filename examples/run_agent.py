#!/usr/bin/env python
"""
Example script showing how to use the WebScraperAgent
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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ExampleScript")

def main():
    """Example of using the WebScraperAgent"""
    
    # Initialize the agent
    logger.info("Initializing WebScraperAgent")
    agent = WebScraperAgent()
    
    # Target URL to scrape
    target_url = "https://example.com/products"
    
    # Load a selector file
    selector_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "selectors",
        "product_listing.json"
    )
    
    with open(selector_file, 'r') as f:
        selectors = json.load(f)
    
    # Create a job name with timestamp
    job_name = f"ExampleProducts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create a scraping job
    logger.info(f"Creating scraping job for URL: {target_url}")
    job_id = agent.create_scraping_job(
        url=target_url,
        selectors=selectors,
        job_name=job_name
    )
    
    logger.info(f"Created job with ID: {job_id}")
    
    # Execute the job
    logger.info(f"Executing job: {job_id}")
    success = agent.execute_job(job_id)
    
    if success:
        logger.info(f"Job {job_id} completed successfully!")
        
        # Get job status
        status = agent.get_job_status(job_id)
        
        if "output_file" in status:
            logger.info(f"Output saved to: {status['output_file']}")
            logger.info(f"Scraped {status.get('items_count', 0)} items")
    else:
        logger.error(f"Job {job_id} failed!")
        
        # Get job status to see the error
        status = agent.get_job_status(job_id)
        if "error" in status:
            logger.error(f"Error: {status['error']}")

if __name__ == "__main__":
    main()