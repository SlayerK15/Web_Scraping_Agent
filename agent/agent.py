"""
AI Agent Orchestrator
This module serves as the main orchestrator for the web scraping process,
coordinating between selector generation, scraping, and data processing.
"""

import os
import json
import logging
import tempfile
from pathlib import Path
import docker
import time

from agent.selector_generator import SelectorGenerator
from agent.storage import SelectorStorage
from agent.feedback_handler import FeedbackHandler
from scraper.scraper import Scraper
from data.processor import DataProcessor
from data.cleaner import DataCleaner
from data.exporter import DataExporter
from utils.helpers import generate_hash
from config.settings import load_config

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self):
        """Initialize the agent with all necessary components."""
        self.config = load_config()
        self.selector_generator = SelectorGenerator()
        self.selector_storage = SelectorStorage()
        self.feedback_handler = FeedbackHandler()
        self.scraper = Scraper()
        self.data_processor = DataProcessor()
        self.data_cleaner = DataCleaner()
        self.data_exporter = DataExporter()
        
        # Initialize docker client
        self.docker_client = docker.from_env()
        
        logger.info("Agent initialized successfully")

    def run(self, url, data_description, pages=1, output_format='csv', 
            output_path=None, use_saved_selector=True):
        """
        Run the complete scraping workflow.
        
        Args:
            url (str): The URL to scrape
            data_description (str): Description of data to scrape
            pages (int): Number of pages to scrape
            output_format (str): Format for output (csv or excel)
            output_path (str): Path where to save the output
            use_saved_selector (bool): Whether to use saved selectors or generate new ones
            
        Returns:
            str: Path to the saved data file
        """
        logger.info(f"Starting scraping workflow for {url}")
        
        # Generate a unique task ID based on URL and data description
        task_id = generate_hash(f"{url}_{data_description}")
        
        # Check if we have a saved selector and should use it
        selectors = None
        if use_saved_selector:
            selectors = self.selector_storage.get_selector(task_id)
            if selectors:
                logger.info(f"Using saved selectors for task {task_id}")
        
        # If no saved selector or not using saved, generate new selectors
        if not selectors:
            logger.info("Generating selectors using AI")
            selectors = self.selector_generator.generate_selectors(url, data_description)
            
            # Save the selectors for future use
            self.selector_storage.save_selector(task_id, selectors)
            logger.info(f"Selectors saved with task ID: {task_id}")
        
        # Create a temporary directory for data exchange with the container
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temporary directory: {temp_dir}")
            
            # Create config file for the scraper inside the temp directory
            config_path = os.path.join(temp_dir, 'scraper_config.json')
            with open(config_path, 'w') as f:
                json.dump({
                    'url': url,
                    'pages': pages,
                    'selectors': selectors,
                    'output_format': output_format
                }, f)
            
            # Run the scraper in docker container
            logger.info("Starting Docker container for scraping")
            scraped_data = self._run_scraper_container(temp_dir)
            
            if not scraped_data or len(scraped_data) == 0:
                logger.warning("No data scraped. Trying to refine selectors and retry.")
                # Refine selectors and try again if first attempt failed
                refined_selectors = self.selector_generator.refine_selectors(
                    url, data_description, selectors, "No data was scraped"
                )
                
                # Update selectors in storage
                self.selector_storage.save_selector(task_id, refined_selectors)
                
                # Update config file with refined selectors
                with open(config_path, 'w') as f:
                    json.dump({
                        'url': url,
                        'pages': pages,
                        'selectors': refined_selectors,
                        'output_format': output_format
                    }, f)
                
                # Try scraping again
                logger.info("Retrying scraping with refined selectors")
                scraped_data = self._run_scraper_container(temp_dir)
            
            # Process and clean the scraped data
            logger.info("Processing and cleaning scraped data")
            processed_data = self.data_processor.process(scraped_data)
            cleaned_data = self.data_cleaner.clean(processed_data)
            
            # Determine output path if not provided
            if not output_path:
                output_dir = os.path.join(os.getcwd(), 'storage', 'data')
                os.makedirs(output_dir, exist_ok=True)
                
                filename = f"scraped_data_{int(time.time())}"
                output_path = os.path.join(output_dir, filename)
            
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Export the cleaned data
            logger.info(f"Exporting data in {output_format} format")
            output_file = self.data_exporter.export(
                cleaned_data, 
                output_format, 
                output_path
            )
            
            logger.info(f"Data successfully exported to {output_file}")
            return output_file

    def _run_scraper_container(self, host_dir):
        """
        Run the scraper in a Docker container.
        
        Args:
            host_dir (str): Host directory for volume mounting
            
        Returns:
            list: Scraped data
        """
        try:
            # Pull the image if it doesn't exist
            try:
                self.docker_client.images.get("web-scraper-ai:latest")
            except docker.errors.ImageNotFound:
                logger.info("Building Docker image for scraper")
                
                # Get the absolute path to the current file (agent.py)
                current_file = os.path.abspath(__file__)
                
                # Get the project root directory
                project_root = os.path.dirname(os.path.dirname(current_file))
                
                # Verify Dockerfile exists
                dockerfile_abs_path = os.path.join(project_root, 'docker', 'Dockerfile')
                if not os.path.exists(dockerfile_abs_path):
                    error_msg = f"Dockerfile not found at {dockerfile_abs_path}"
                    logger.error(error_msg)
                    raise FileNotFoundError(error_msg)
                    
                logger.info(f"Verified Dockerfile exists at: {dockerfile_abs_path}")
                
                # For Docker API, the dockerfile parameter should be relative to the path parameter
                # Always use forward slashes for Docker paths, even on Windows
                dockerfile_rel_path = 'docker/Dockerfile'
                
                logger.info(f"Building with project_root={project_root}, dockerfile={dockerfile_rel_path}")
                
                # Build with correct path parameters
                self.docker_client.images.build(
                    path=project_root,  # Use project root as build context
                    dockerfile=dockerfile_rel_path,  # Use relative path with forward slashes
                    tag="web-scraper-ai:latest",
                    rm=True
                )
            
            # Run the container
            container = self.docker_client.containers.run(
                "web-scraper-ai:latest",
                command="python -m scraper.scraper /data/scraper_config.json",
                volumes={host_dir: {'bind': '/data', 'mode': 'rw'}},
                detach=True
            )
            
            # Wait for container to finish
            result = container.wait()
            
            # Get logs
            logs = container.logs().decode('utf-8')
            logger.debug(f"Container logs: {logs}")
            
            # Check exit code
            if result['StatusCode'] != 0:
                logger.error(f"Container exited with code {result['StatusCode']}")
                logger.error(f"Container logs: {logs}")
                raise Exception(f"Scraper container failed with exit code {result['StatusCode']}")
            
            # Read scraped data from the file
            scraped_data_path = os.path.join(host_dir, 'scraped_data.json')
            
            if os.path.exists(scraped_data_path):
                with open(scraped_data_path, 'r') as f:
                    scraped_data = json.load(f)
            else:
                logger.warning("No scraped data file found")
                scraped_data = []
            
            # Clean up container
            container.remove()
            
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error running scraper container: {str(e)}")
            raise
    
    def process_feedback(self, rating, feedback, url, data_description):
        """
        Process user feedback to improve selector generation.
        
        Args:
            rating (str): User rating of the results (1-10)
            feedback (str): User feedback text
            url (str): The URL that was scraped
            data_description (str): Description of the data that was scraped
        """
        task_id = generate_hash(f"{url}_{data_description}")
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 10:
                logger.warning(f"Invalid rating value: {rating}")
                rating = None
        except ValueError:
            logger.warning(f"Could not parse rating as integer: {rating}")
            rating = None
        
        # Store feedback for future model improvements
        self.feedback_handler.store_feedback(
            task_id=task_id,
            url=url,
            data_description=data_description,
            rating=rating,
            feedback=feedback
        )
        
        # If rating is low, consider regenerating selectors
        if rating is not None and rating < 5:
            logger.info(f"Low rating ({rating}) received, regenerating selectors")
            
            # Get existing selectors
            existing_selectors = self.selector_storage.get_selector(task_id)
            
            # Generate improved selectors based on feedback
            improved_selectors = self.selector_generator.refine_selectors(
                url, 
                data_description, 
                existing_selectors, 
                feedback
            )
            
            # Save the improved selectors
            self.selector_storage.save_selector(task_id, improved_selectors)
            logger.info(f"Improved selectors saved for task {task_id}")