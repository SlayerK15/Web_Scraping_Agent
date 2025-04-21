#!/usr/bin/env python
"""
Example script showing how to use custom data processing with the agent
"""
import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the agent and processor
from agent import WebScraperAgent
from data_processor import DataProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CustomProcessingExample")

class CustomDataProcessor(DataProcessor):
    """
    Extended data processor with custom processing logic
    """
    
    def __init__(self, config=None):
        """Initialize with parent class"""
        super().__init__(config)
    
    def process(self, raw_data, schema=None):
        """
        Override the process method with custom logic
        """
        # First use the parent class processing
        processed_data = super().process(raw_data, schema)
        
        # Then apply custom processing
        return self.apply_custom_processing(processed_data)
    
    def apply_custom_processing(self, data):
        """
        Apply custom processing to the data
        
        Examples:
        - Calculate discounts
        - Apply sentiment analysis
        - Add geolocation data
        - Categorize products
        """
        logger.info("Applying custom data processing")
        
        for item in data:
            # Example 1: Calculate discount percentage if both price and original price exist
            if 'price' in item and 'original_price' in item and item['price'] and item['original_price']:
                try:
                    current_price = float(item['price'])
                    original_price = float(item['original_price'])
                    
                    if original_price > 0 and current_price < original_price:
                        discount_pct = (original_price - current_price) / original_price * 100
                        item['discount_percentage'] = round(discount_pct, 1)
                        
                        # Add discount category
                        if discount_pct >= 50:
                            item['discount_category'] = 'High'
                        elif discount_pct >= 20:
                            item['discount_category'] = 'Medium'
                        else:
                            item['discount_category'] = 'Low'
                except (ValueError, TypeError):
                    pass
            
            # Example 2: Add product category based on keywords in title or description
            if 'product_name' in item:
                product_name = item['product_name'].lower()
                
                if any(keyword in product_name for keyword in ['phone', 'smartphone', 'iphone', 'android']):
                    item['product_category'] = 'Smartphones'
                elif any(keyword in product_name for keyword in ['laptop', 'notebook', 'macbook']):
                    item['product_category'] = 'Laptops'
                elif any(keyword in product_name for keyword in ['tv', 'television', 'smart tv']):
                    item['product_category'] = 'TVs'
                else:
                    item['product_category'] = 'Other'
            
            # Example 3: Add a field for product name length (could be useful for filtering)
            if 'product_name' in item and item['product_name']:
                item['name_length'] = len(item['product_name'])
        
        return data

def main():
    """Example of using custom data processing with the agent"""
    
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
    job_name = f"CustomProcessing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create a scraping job
    logger.info(f"Creating scraping job for URL: {target_url}")
    job_id = agent.create_scraping_job(
        url=target_url,
        selectors=selectors,
        job_name=job_name
    )
    
    logger.info(f"Created job with ID: {job_id}")
    
    # Execute the job to get raw data
    logger.info(f"Executing job to get raw data: {job_id}")
    agent.execute_job(job_id)
    
    # Get job info to find raw data location
    job_info = agent.get_job_status(job_id)
    
    # Load raw data
    raw_data_file = os.path.join("data", f"{job_id}_raw.json")
    with open(raw_data_file, 'r') as f:
        raw_data = json.load(f)
    
    logger.info(f"Loaded raw data: {len(raw_data)} items")
    
    # Create custom processor
    custom_processor = CustomDataProcessor()
    
    # Process the data with custom processor
    processed_data = custom_processor.process(raw_data)
    
    logger.info(f"Custom processing completed: {len(processed_data)} items")
    
    # Save to Excel with custom name
    output_file = os.path.join("output", f"{job_name}_custom.xlsx")
    
    # Use pandas to save to Excel
    df = pd.DataFrame(processed_data)
    df.to_excel(output_file, index=False)
    
    logger.info(f"Custom processed data saved to: {output_file}")
    
    # Example of adding analytics
    if len(processed_data) > 0:
        # Count items by category
        categories = {}
        for item in processed_data:
            category = item.get('product_category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
        
        logger.info("Product categories breakdown:")
        for category, count in categories.items():
            logger.info(f"  - {category}: {count} items")
        
        # Calculate average discount if available
        if any('discount_percentage' in item for item in processed_data):
            discounts = [item['discount_percentage'] for item in processed_data 
                        if 'discount_percentage' in item and item['discount_percentage']]
            if discounts:
                avg_discount = sum(discounts) / len(discounts)
                logger.info(f"Average discount: {avg_discount:.1f}%")

if __name__ == "__main__":
    main()