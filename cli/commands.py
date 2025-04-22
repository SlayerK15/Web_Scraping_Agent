"""
Command Line Interface Module
Implements command-line interface for the web scraper AI.
"""

import os
import sys
import argparse
import logging
from typing import List, Optional, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import Agent
from agent.storage import SelectorStorage
from utils.logger import setup_logger
from config.settings import load_config

logger = logging.getLogger(__name__)

def scrape_command(args: argparse.Namespace) -> None:
    """
    Run the scrape command.
    
    Args:
        args (argparse.Namespace): Command arguments
    """
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(log_level)
    
    logger.info(f"Starting scrape command for URL: {args.url}")
    
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
            use_saved_selector=not args.regenerate_selector
        )
        
        logger.info(f"Scraping completed successfully. Data saved to: {result}")
        print(f"Scraping completed successfully. Data saved to: {result}")
        
        # Get user feedback if not running in quiet mode
        if not args.quiet:
            rating = input("Please rate the accuracy of the scraped data (1-10): ")
            feedback = input("Any additional feedback or incorrect data to report? ")
            
            # Process feedback
            agent.process_feedback(rating, feedback, args.url, args.data)
            
            logger.info("Thank you for your feedback!")
            print("Thank you for your feedback!")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        if args.debug:
            import traceback
            logger.error(traceback.format_exc())
        print(f"Error: {str(e)}")
        sys.exit(1)

def list_selectors_command(args: argparse.Namespace) -> None:
    """
    List saved selectors.
    
    Args:
        args (argparse.Namespace): Command arguments
    """
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(log_level)
    
    logger.info("Listing saved selectors")
    
    try:
        # Initialize selector storage
        selector_storage = SelectorStorage()
        
        # Get list of selectors
        selectors = selector_storage.list_selectors()
        
        if not selectors:
            logger.info("No saved selectors found")
            print("No saved selectors found.")
            return
        
        # Print selectors
        print("\nSaved Selectors:")
        print("----------------")
        for task_id, timestamp in selectors.items():
            # Convert timestamp to readable date if it's a number
            if isinstance(timestamp, (int, float)):
                from datetime import datetime
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            else:
                date_str = str(timestamp)
                
            print(f"ID: {task_id}")
            print(f"Created: {date_str}")
            print("----------------")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        if args.debug:
            import traceback
            logger.error(traceback.format_exc())
        print(f"Error: {str(e)}")
        sys.exit(1)

def show_selector_command(args: argparse.Namespace) -> None:
    """
    Show a specific selector.
    
    Args:
        args (argparse.Namespace): Command arguments
    """
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(log_level)
    
    logger.info(f"Showing selector with ID: {args.id}")
    
    try:
        # Initialize selector storage
        selector_storage = SelectorStorage()
        
        # Get selector
        selector = selector_storage.get_selector(args.id)
        
        if not selector:
            logger.warning(f"No selector found with ID: {args.id}")
            print(f"No selector found with ID: {args.id}")
            return
        
        # Print selector details
        import json
        print(f"\nSelector ID: {args.id}")
        print("-------------------")
        print(json.dumps(selector, indent=2))
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        if args.debug:
            import traceback
            logger.error(traceback.format_exc())
        print(f"Error: {str(e)}")
        sys.exit(1)

def delete_selector_command(args: argparse.Namespace) -> None:
    """
    Delete a specific selector.
    
    Args:
        args (argparse.Namespace): Command arguments
    """
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(log_level)
    
    logger.info(f"Deleting selector with ID: {args.id}")
    
    try:
        # Initialize selector storage
        selector_storage = SelectorStorage()
        
        # Check if selector exists
        selector = selector_storage.get_selector(args.id)
        
        if not selector:
            logger.warning(f"No selector found with ID: {args.id}")
            print(f"No selector found with ID: {args.id}")
            return
        
        # Confirm deletion
        if not args.force:
            confirm = input(f"Are you sure you want to delete selector with ID '{args.id}'? (y/n): ")
            if confirm.lower() not in ['y', 'yes']:
                print("Deletion cancelled.")
                return
        
        # Delete selector
        result = selector_storage.delete_selector(args.id)
        
        if result:
            logger.info(f"Selector {args.id} deleted successfully")
            print(f"Selector {args.id} deleted successfully.")
        else:
            logger.error(f"Failed to delete selector {args.id}")
            print(f"Failed to delete selector {args.id}.")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        if args.debug:
            import traceback
            logger.error(traceback.format_exc())
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    """Main function for the CLI."""
    # Create parser
    parser = argparse.ArgumentParser(description='Web Scraper AI Command Line Interface')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape a website')
    scrape_parser.add_argument('--url', type=str, required=True, help='URL to scrape')
    scrape_parser.add_argument('--data', type=str, required=True, help='Description of data to scrape')
    scrape_parser.add_argument('--pages', type=int, default=1, help='Number of pages to scrape')
    scrape_parser.add_argument('--format', type=str, choices=['csv', 'excel', 'json'], default='csv', 
                         help='Output format')
    scrape_parser.add_argument('--output', type=str, help='Output file path')
    scrape_parser.add_argument('--regenerate-selector', action='store_true', 
                         help='Regenerate selector even if one exists')
    scrape_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    scrape_parser.add_argument('--quiet', action='store_true', help='Do not ask for feedback')
    
    # List selectors command
    list_parser = subparsers.add_parser('list-selectors', help='List saved selectors')
    list_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Show selector command
    show_parser = subparsers.add_parser('show-selector', help='Show a specific selector')
    show_parser.add_argument('--id', type=str, required=True, help='Selector ID to show')
    show_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Delete selector command
    delete_parser = subparsers.add_parser('delete-selector', help='Delete a specific selector')
    delete_parser.add_argument('--id', type=str, required=True, help='Selector ID to delete')
    delete_parser.add_argument('--force', action='store_true', help='Do not ask for confirmation')
    delete_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command specified
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Run the appropriate command
    if args.command == 'scrape':
        scrape_command(args)
    elif args.command == 'list-selectors':
        list_selectors_command(args)
    elif args.command == 'show-selector':
        show_selector_command(args)
    elif args.command == 'delete-selector':
        delete_selector_command(args)

if __name__ == '__main__':
    main()