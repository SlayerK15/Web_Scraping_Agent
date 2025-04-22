#!/usr/bin/env python3
"""
Web Scraper AI - Main Entry Point
This script initializes the AI agent and handles command-line arguments.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import Agent
from utils.logger import setup_logger

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Web Scraper AI')
    parser.add_argument('--url', type=str, help='URL to scrape')
    parser.add_argument('--pages', type=int, default=1, help='Number of pages to scrape')
    parser.add_argument('--data', type=str, help='Description of data to scrape')
    parser.add_argument('--format', type=str, choices=['csv', 'excel'], default='csv', 
                        help='Output format (csv or excel)')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--use-saved-selector', action='store_true', 
                        help='Use saved selector if available')
    return parser.parse_args()

def main():
    """Main entry point of the application."""
    # Load environment variables
    load_dotenv()
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logger(log_level)
    
    if not args.url:
        print("Error: URL is required")
        print("Example: python main.py --url https://example.com --data 'product titles and prices' --pages 3")
        sys.exit(1)
    
    if not args.data:
        print("Error: Data description is required")
        print("Example: python main.py --url https://example.com --data 'product titles and prices' --pages 3")
        sys.exit(1)
    
    logger.info(f"Starting Web Scraper AI for URL: {args.url}")
    logger.info(f"Looking for data: {args.data}")
    logger.info(f"Number of pages: {args.pages}")
    
    try:
        # Initialize the agent
        agent = Agent()
        
        # Run the agent with the provided arguments
        result = agent.run(
            url=args.url,
            data_description=args.data,
            pages=args.pages,
            output_format=args.format,
            output_path=args.output,
            use_saved_selector=args.use_saved_selector
        )
        
        logger.info(f"Scraping completed successfully. Data saved to: {result}")
        
        # Get user feedback
        rating = input("Please rate the accuracy of the scraped data (1-10): ")
        feedback = input("Any additional feedback or incorrect data to report? ")
        
        # Process feedback
        agent.process_feedback(rating, feedback, args.url, args.data)
        
        logger.info("Thank you for your feedback!")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()