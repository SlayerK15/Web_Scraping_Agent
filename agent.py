#!/usr/bin/env python
"""
AI Web Scraping Agent - Main Agent Class
This agent acts as an independent entity that:
1. Takes URLs and scraping requirements from the user
2. Creates a scraping container to fetch the data
3. Processes the data into useful information
4. Stores the results in Excel sheets
"""

import os
import json
import logging
import time
import random
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("agent.log"), logging.StreamHandler()]
)
logger = logging.getLogger("WebScraperAgent")

class WebScraperAgent:
    """
    Autonomous web scraping agent that manages the entire process
    from data collection to processing and storage.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the agent with configuration.
        
        Args:
            config_path: Path to a JSON configuration file (optional)
        """
        self.agent_id = str(uuid.uuid4())[:8]
        self.config = self._load_config(config_path)
        
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("output", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("containers", exist_ok=True)
        
        logger.info(f"Agent {self.agent_id} initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to a JSON configuration file
            
        Returns:
            Dict containing configuration
        """
        default_config = {
            "max_retries": 3,
            "delay_between_requests": [1, 5],  # Random delay range in seconds
            "use_proxy": False,
            "proxy_api_key": None,
            "user_agents": [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
            ],
            "output_format": "xlsx"
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Update default config with user-provided values
                    default_config.update(user_config)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration from {config_path}: {str(e)}")
        
        return default_config
    
    def create_scraping_job(self, 
                          url: str, 
                          selectors: Dict, 
                          job_name: Optional[str] = None) -> str:
        """
        Create a new scraping job.
        
        Args:
            url: Target URL to scrape
            selectors: Dictionary containing selector information
            job_name: Optional name for the job
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())[:8]
        job_name = job_name or f"job_{job_id}"
        
        job_info = {
            "job_id": job_id,
            "job_name": job_name,
            "url": url,
            "selectors": selectors,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        # Save job information
        job_file = os.path.join("containers", f"{job_id}.json")
        with open(job_file, 'w') as f:
            json.dump(job_info, f, indent=2)
        
        logger.info(f"Created scraping job {job_id} for URL: {url}")
        return job_id
    
    def execute_job(self, job_id: str) -> bool:
        """
        Execute a scraping job.
        
        Args:
            job_id: ID of the job to execute
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Executing job {job_id}")
        
        # Load job information
        job_file = os.path.join("containers", f"{job_id}.json")
        try:
            with open(job_file, 'r') as f:
                job_info = json.load(f)
        except Exception as e:
            logger.error(f"Error loading job {job_id}: {str(e)}")
            return False
        
        # Update job status
        job_info["status"] = "running"
        job_info["last_updated"] = datetime.now().isoformat()
        
        with open(job_file, 'w') as f:
            json.dump(job_info, f, indent=2)
        
        # Import the container module dynamically
        from scraper_container import ScraperContainer
        
        # Create scraper container
        container = ScraperContainer(
            job_id=job_id,
            url=job_info["url"],
            selectors=job_info["selectors"],
            config=self.config
        )
        
        try:
            # Execute the scraping
            raw_data = container.scrape()
            
            if not raw_data:
                logger.error(f"Job {job_id} failed: No data retrieved")
                job_info["status"] = "failed"
                job_info["error"] = "No data retrieved"
                job_info["last_updated"] = datetime.now().isoformat()
                
                with open(job_file, 'w') as f:
                    json.dump(job_info, f, indent=2)
                return False
            
            # Save raw data
            data_file = os.path.join("data", f"{job_id}_raw.json")
            with open(data_file, 'w') as f:
                json.dump(raw_data, f, indent=2)
            
            logger.info(f"Job {job_id} completed: Retrieved {len(raw_data)} items")
            
            # Process the data
            processed_data = self.process_data(raw_data, job_info["selectors"])
            
            # Save processed data to Excel
            output_file = os.path.join("output", f"{job_info['job_name']}.xlsx")
            self.save_to_excel(processed_data, output_file)
            
            # Update job status
            job_info["status"] = "completed"
            job_info["items_count"] = len(processed_data)
            job_info["output_file"] = output_file
            job_info["last_updated"] = datetime.now().isoformat()
            
            with open(job_file, 'w') as f:
                json.dump(job_info, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing job {job_id}: {str(e)}")
            
            # Update job status
            job_info["status"] = "failed"
            job_info["error"] = str(e)
            job_info["last_updated"] = datetime.now().isoformat()
            
            with open(job_file, 'w') as f:
                json.dump(job_info, f, indent=2)
            
            return False
    
    def process_data(self, 
                    raw_data: List[Dict], 
                    selectors: Dict) -> List[Dict]:
        """
        Process the raw scraped data into a more useful format.
        
        Args:
            raw_data: List of dictionaries containing raw scraped data
            selectors: The selector configuration used for scraping
            
        Returns:
            List of dictionaries with processed data
        """
        logger.info(f"Processing {len(raw_data)} items of raw data")
        
        processed_data = []
        
        try:
            # Extract field names from selector configuration
            field_names = list(selectors.get("extract", {}).keys())
            
            for item in raw_data:
                processed_item = {}
                
                # Apply custom processing for each field
                for field in field_names:
                    if field in item:
                        value = item[field]
                        
                        # Apply type conversions and cleaning
                        if field.endswith("_price") or field == "price":
                            # Try to convert price strings to float
                            processed_item[field] = self._convert_price(value)
                        elif field.endswith("_date") or field == "date":
                            # Try to parse dates
                            processed_item[field] = self._parse_date(value)
                        else:
                            # Basic string cleaning
                            processed_item[field] = self._clean_text(value)
                    else:
                        processed_item[field] = None
                
                # Add metadata
                processed_item["processed_at"] = datetime.now().isoformat()
                
                processed_data.append(processed_item)
            
            logger.info(f"Processed {len(processed_data)} items")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            # Return raw data as fallback
            return raw_data
    
    def _clean_text(self, text: str) -> str:
        """Clean up text by removing extra whitespace"""
        if not text or not isinstance(text, str):
            return text
        return " ".join(text.split())
    
    def _convert_price(self, price_str: str) -> Optional[float]:
        """Convert price string to float"""
        if not price_str or not isinstance(price_str, str):
            return None
        
        try:
            # Remove currency symbols and other non-numeric characters
            digits_only = ''.join(c for c in price_str 
                               if c.isdigit() or c == '.' or c == ',')
            
            # Replace comma with period for decimal point
            normalized = digits_only.replace(',', '.')
            
            # Handle multiple periods (take the last one as decimal point)
            if normalized.count('.') > 1:
                parts = normalized.split('.')
                normalized = ''.join(parts[:-1]) + '.' + parts[-1]
            
            return float(normalized)
        except Exception:
            return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string into ISO format"""
        if not date_str or not isinstance(date_str, str):
            return None
        
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%B %d, %Y",
            "%d %B %Y",
            "%Y-%m-%d %H:%M:%S"
        ]
        
        cleaned_date = self._clean_text(date_str)
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(cleaned_date, fmt)
                return parsed_date.isoformat()
            except ValueError:
                continue
        
        return cleaned_date  # Return original if parsing fails
    
    def save_to_excel(self, data: List[Dict], filename: str) -> bool:
        """
        Save processed data to an Excel file.
        
        Args:
            data: List of dictionaries containing processed data
            filename: Path to the output Excel file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import pandas as pd
            
            if not data:
                logger.warning(f"No data to save to {filename}")
                return False
            
            # Create DataFrame from data
            df = pd.DataFrame(data)
            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Save to Excel
            df.to_excel(filename, index=False, engine='openpyxl')
            logger.info(f"Data saved to Excel: {filename}")
            
            # Also save as CSV for backup
            csv_filename = filename.replace('.xlsx', '.csv')
            df.to_csv(csv_filename, index=False)
            logger.info(f"Data backup saved to CSV: {csv_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving data to Excel: {str(e)}")
            
            # Try to save as JSON as a fallback
            try:
                json_filename = filename.replace('.xlsx', '.json')
                with open(json_filename, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Data saved as JSON fallback: {json_filename}")
            except Exception as json_err:
                logger.error(f"Error saving JSON fallback: {str(json_err)}")
            
            return False
    
    def get_job_status(self, job_id: str) -> Dict:
        """
        Get the status of a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dictionary with job status information
        """
        job_file = os.path.join("containers", f"{job_id}.json")
        
        try:
            with open(job_file, 'r') as f:
                job_info = json.load(f)
            return job_info
        except Exception as e:
            logger.error(f"Error getting status for job {job_id}: {str(e)}")
            return {"job_id": job_id, "status": "unknown", "error": str(e)}
    
    def list_jobs(self) -> List[Dict]:
        """
        List all jobs.
        
        Returns:
            List of dictionaries with job information
        """
        jobs = []
        
        try:
            for filename in os.listdir("containers"):
                if filename.endswith(".json"):
                    with open(os.path.join("containers", filename), 'r') as f:
                        job_info = json.load(f)
                    jobs.append(job_info)
        except Exception as e:
            logger.error(f"Error listing jobs: {str(e)}")
        
        return jobs

# Example of how to use the agent
def main():
    # Create an agent
    agent = WebScraperAgent()
    
    # Example selector configuration
    selector_config = {
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
            },
            "description": {
                "type": "text",
                "selector": ".product-description"
            }
        }
    }
    
    # Create a scraping job
    job_id = agent.create_scraping_job(
        url="https://example.com/products",
        selectors=selector_config,
        job_name="Example Products"
    )
    
    # Execute the job
    success = agent.execute_job(job_id)
    
    if success:
        print(f"Job {job_id} completed successfully!")
    else:
        print(f"Job {job_id} failed!")

if __name__ == "__main__":
    main()