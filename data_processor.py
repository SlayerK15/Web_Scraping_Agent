#!/usr/bin/env python
"""
AI Web Scraping Agent - Data Processing Module
This module handles the transformation of raw scraped data into useful information.
"""

import re
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("processor.log"), logging.StreamHandler()]
)
logger = logging.getLogger("DataProcessor")

class DataProcessor:
    """
    Processes raw scraped data into a more useful format.
    """
    
    def __init__(self, config=None):
        """
        Initialize the data processor.
        
        Args:
            config: Optional configuration for processing
        """
        self.config = config or {}
    
    def process(self, raw_data: List[Dict], schema: Optional[Dict] = None) -> List[Dict]:
        """
        Process raw data according to schema or intelligent detection.
        
        Args:
            raw_data: List of dictionaries containing raw scraped data
            schema: Optional schema that defines how to process each field
            
        Returns:
            List of dictionaries with processed data
        """
        if not raw_data:
            logger.warning("No data to process")
            return []
        
        logger.info(f"Processing {len(raw_data)} items")
        
        # If no schema provided, try to detect field types automatically
        if not schema:
            schema = self._detect_schema(raw_data)
            logger.info(f"Auto-detected schema: {schema}")
        
        processed_data = []
        
        for item in raw_data:
            processed_item = {}
            
            # Process each field according to schema
            for field_name, field_value in item.items():
                # Skip processing if the field is not in the schema
                if field_name not in schema:
                    processed_item[field_name] = field_value
                    continue
                
                # Get field type and processing options
                field_type = schema[field_name].get("type", "string")
                options = schema[field_name].get("options", {})
                
                # Process based on field type
                if field_type == "string":
                    processed_item[field_name] = self._process_string(field_value, options)
                
                elif field_type == "number" or field_type == "float":
                    processed_item[field_name] = self._process_number(field_value, options)
                
                elif field_type == "integer":
                    processed_item[field_name] = self._process_integer(field_value, options)
                
                elif field_type == "boolean":
                    processed_item[field_name] = self._process_boolean(field_value, options)
                
                elif field_type == "date":
                    processed_item[field_name] = self._process_date(field_value, options)
                
                elif field_type == "price":
                    processed_item[field_name] = self._process_price(field_value, options)
                
                elif field_type == "url":
                    processed_item[field_name] = self._process_url(field_value, options)
                
                else:
                    # Default to string for unknown types
                    processed_item[field_name] = self._process_string(field_value, options)
            
            # Add additional derived fields
            if self.config.get("add_derived_fields", True):
                processed_item = self._add_derived_fields(processed_item, schema)
            
            processed_data.append(processed_item)
        
        # Additional post-processing steps
        if self.config.get("remove_duplicates", True):
            processed_data = self._remove_duplicates(processed_data)
        
        if self.config.get("fill_missing_values", True):
            processed_data = self._fill_missing_values(processed_data)
        
        logger.info(f"Processed {len(processed_data)} items")
        return processed_data
    
    def _detect_schema(self, data: List[Dict]) -> Dict:
        """
        Automatically detect the schema based on data values.
        
        Args:
            data: List of dictionaries containing raw data
            
        Returns:
            Schema dictionary mapping field names to types and options
        """
        if not data:
            return {}
        
        # Combine all keys from all items
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        
        schema = {}
        
        # Examine a sample of the data to determine types
        sample_size = min(100, len(data))
        sample = data[:sample_size]
        
        for key in all_keys:
            # Collect non-empty values for this key
            values = [item.get(key) for item in sample if key in item and item[key]]
            
            if not values:
                # No values to determine type
                schema[key] = {"type": "string"}
                continue
            
            # Check if all values look like numbers
            if all(self._is_numeric(v) for v in values if v):
                if all(isinstance(v, int) or (isinstance(v, str) and v.isdigit()) for v in values if v):
                    schema[key] = {"type": "integer"}
                else:
                    # Check if it might be a price
                    if any(self._looks_like_price(v) for v in values if v):
                        schema[key] = {"type": "price"}
                    else:
                        schema[key] = {"type": "float"}
            
            # Check if all values look like dates
            elif all(self._looks_like_date(v) for v in values if v):
                schema[key] = {"type": "date"}
            
            # Check if all values look like URLs
            elif all(self._looks_like_url(v) for v in values if v):
                schema[key] = {"type": "url"}
            
            # Check if all values look like booleans
            elif all(self._looks_like_boolean(v) for v in values if v):
                schema[key] = {"type": "boolean"}
            
            # Default to string
            else:
                schema[key] = {"type": "string"}
        
        return schema
    
    def _is_numeric(self, value) -> bool:
        """Check if a value is numeric"""
        if isinstance(value, (int, float)):
            return True
        
        if not isinstance(value, str):
            return False
        
        # Remove common numeric formatting characters
        value = re.sub(r'[,$%\s]', '', value)
        
        # Check if it can be converted to float
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _looks_like_price(self, value) -> bool:
        """Check if a value looks like a price"""
        if not isinstance(value, str):
            return False
        
        # Look for currency symbols or common price patterns
        return bool(re.search(r'[$€£¥]|USD|EUR|GBP|JPY', value)) or \
               bool(re.search(r'\d+\.\d{2}', value))
    
    def _looks_like_date(self, value) -> bool:
        """Check if a value looks like a date"""
        if not isinstance(value, str):
            return False
        
        # Common date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY or DD-MM-YYYY
            r'\d{1,2}\s+[A-Za-z]+\s+\d{4}'  # DD Month YYYY
        ]
        
        return any(re.search(pattern, value) for pattern in date_patterns)
    
    def _looks_like_url(self, value) -> bool:
        """Check if a value looks like a URL"""
        if not isinstance(value, str):
            return False
        
        # Simple URL pattern
        url_pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        return bool(re.search(url_pattern, value))
    
    def _looks_like_boolean(self, value) -> bool:
        """Check if a value looks like a boolean"""
        if isinstance(value, bool):
            return True
        
        if not isinstance(value, str):
            return False
        
        # Common boolean string representations
        bool_values = ['true', 'false', 'yes', 'no', 'y', 'n', 'on', 'off', '1', '0']
        return value.lower() in bool_values
    
    def _process_string(self, value, options=None) -> str:
        """Process a string value"""
        options = options or {}
        
        if value is None:
            return ""
        
        if not isinstance(value, str):
            value = str(value)
        
        # Apply string cleaning options
        if options.get("strip", True):
            value = value.strip()
        
        if options.get("lowercase", False):
            value = value.lower()
        
        if options.get("uppercase", False):
            value = value.upper()
        
        if options.get("capitalize", False):
            value = value.capitalize()
        
        if options.get("max_length"):
            value = value[:options["max_length"]]
        
        # Replace specific patterns if specified
        if options.get("replace_patterns"):
            for pattern, replacement in options["replace_patterns"].items():
                value = re.sub(pattern, replacement, value)
        
        return value
    
    def _process_number(self, value, options=None) -> Optional[float]:
        """Process a numeric value to a float"""
        options = options or {}
        
        if value is None:
            return None
        
        # If already a number, just return it
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            value = str(value)
        
        # Remove non-numeric characters except decimal point
        value = re.sub(r'[^\d.-]', '', value)
        
        # Handle multiple decimal points (keep only the last one)
        if value.count('.') > 1:
            parts = value.split('.')
            value = ''.join(parts[:-1]) + '.' + parts[-1]
        
        try:
            result = float(value)
            
            # Apply rounding if specified
            if options.get("round") is not None:
                result = round(result, options["round"])
            
            return result
        except (ValueError, TypeError):
            return None
    
    def _process_integer(self, value, options=None) -> Optional[int]:
        """Process a numeric value to an integer"""
        options = options or {}
        
        # First process as float
        number = self._process_number(value, options)
        
        if number is None:
            return None
        
        try:
            return int(number)
        except (ValueError, TypeError):
            return None
    
    def _process_boolean(self, value, options=None) -> Optional[bool]:
        """Process a value to a boolean"""
        options = options or {}
        
        if value is None:
            return None
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        if not isinstance(value, str):
            value = str(value)
        
        # Common boolean string representations
        true_values = options.get("true_values", ["true", "yes", "y", "on", "1"])
        false_values = options.get("false_values", ["false", "no", "n", "off", "0"])
        
        value_lower = value.lower().strip()
        
        if value_lower in true_values:
            return True
        elif value_lower in false_values:
            return False
        else:
            return None
    
    def _process_date(self, value, options=None) -> Optional[str]:
        """Process a date value to ISO format"""
        options = options or {}
        
        if value is None:
            return None
        
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        # Define date formats to try
        date_formats = options.get("date_formats", [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%B %d, %Y",
            "%d %B %Y",
            "%Y-%m-%d %H:%M:%S"
        ])
        
        # Try each format
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(value, fmt)
                return parsed_date.isoformat()
            except ValueError:
                continue
        
        # If no format works, try to extract a date using regex
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY or DD-MM-YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, value)
            if match:
                extracted_date = match.group(1)
                # Try parsing the extracted date again
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(extracted_date, fmt)
                        return parsed_date.isoformat()
                    except ValueError:
                        continue
        
        # If all else fails, return the original value
        return value
    
    def _process_price(self, value, options=None) -> Optional[float]:
        """Process a price value"""
        options = options or {}
        
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            value = str(value)
        
        # Remove currency symbols and any non-numeric characters except decimal points
        price_str = re.sub(r'[^\d.-]', '', value)
        
        # Process as number
        price = self._process_number(price_str, options)
        
        # Round to 2 decimal places by default for prices
        if price is not None and options.get("round", 2) is not None:
            price = round(price, options.get("round", 2))
        
        return price
    
    def _process_url(self, value, options=None) -> Optional[str]:
        """Process a URL value"""
        options = options or {}
        
        if value is None:
            return None
        
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        # Add http prefix if missing
        if options.get("add_http", True) and value and not value.startswith(('http://', 'https://')):
            value = 'http://' + value
        
        # Validate URL format if required
        if options.get("validate", False):
            url_pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
            if not re.match(url_pattern, value):
                return None
        
        return value
    
    def _add_derived_fields(self, item: Dict, schema: Dict) -> Dict:
        """
        Add derived fields based on existing fields.
        
        Args:
            item: Dictionary containing processed item data
            schema: Schema dictionary
            
        Returns:
            Dictionary with added derived fields
        """
        # Example: Add a full_name field from first_name and last_name
        if 'first_name' in item and 'last_name' in item:
            item['full_name'] = f"{item['first_name']} {item['last_name']}".strip()
        
        # Example: Add a domain field from a URL
        if 'url' in item and item['url']:
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(item['url'])
                item['domain'] = parsed_url.netloc
            except:
                pass
        
        # Example: Add price category
        if 'price' in item and item['price'] is not None:
            price = float(item['price'])
            if price < 10:
                item['price_category'] = 'Budget'
            elif price < 50:
                item['price_category'] = 'Economy'
            elif price < 100:
                item['price_category'] = 'Mid-range'
            else:
                item['price_category'] = 'Premium'
        
        return item
    
    def _remove_duplicates(self, data: List[Dict]) -> List[Dict]:
        """
        Remove duplicate items from the data.
        
        Args:
            data: List of dictionaries with processed data
            
        Returns:
            Deduplicated list of dictionaries
        """
        if not data:
            return []
        
        # Convert to DataFrame for easier deduplication
        df = pd.DataFrame(data)
        
        # Remove exact duplicates
        df = df.drop_duplicates()
        
        # Return as list of dictionaries
        return df.to_dict('records')
    
    def _fill_missing_values(self, data: List[Dict]) -> List[Dict]:
        """
        Fill missing values in the data.
        
        Args:
            data: List of dictionaries with processed data
            
        Returns:
            List of dictionaries with filled missing values
        """
        if not data:
            return []
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data)
        
        # Fill numeric columns with mean or 0
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].fillna(df[col].mean() if not df[col].isna().all() else 0)
        
        # Fill string columns with empty string
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            df[col] = df[col].fillna('')
        
        # Return as list of dictionaries
        return df.to_dict('records')


# Standalone execution for testing
if __name__ == "__main__":
    # Example data
    test_data = [
        {"name": "Product 1", "price": "$19.99", "available": "yes", "date_added": "2023-04-15"},
        {"name": "Product 2", "price": "€29.50", "available": "no", "date_added": "05/21/2023"},
        {"name": "Product 3", "price": "15", "available": "true", "date_added": "January 10, 2023"}
    ]
    
    # Create processor and process data
    processor = DataProcessor()
    result = processor.process(test_data)
    
    # Print results
    import json
    print(json.dumps(result, indent=2))