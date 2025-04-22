"""
Data Processor Module
Handles post-processing of scraped data before export.
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional, Union
import concurrent.futures
from datetime import datetime

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        """Initialize the data processor."""
        logger.info("Data processor initialized")

    def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process scraped data with various transformations.
        
        Args:
            data (list): List of scraped data items
            
        Returns:
            list: Processed data items
        """
        if not data:
            logger.warning("No data to process")
            return []
            
        logger.info(f"Processing {len(data)} data items")
        
        try:
            # Process data in parallel for large datasets
            if len(data) > 100:
                return self._parallel_process(data)
            else:
                return [self._process_item(item) for item in data]
                
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            return data  # Return original data on error

    def _parallel_process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process data items in parallel.
        
        Args:
            data (list): List of data items to process
            
        Returns:
            list: Processed data items
        """
        processed_data = []
        
        # Use ProcessPoolExecutor for CPU-bound tasks
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Submit all processing tasks
            future_to_item = {executor.submit(self._process_item, item): item for item in data}
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_item):
                try:
                    processed_item = future.result()
                    processed_data.append(processed_item)
                except Exception as e:
                    item = future_to_item[future]
                    logger.error(f"Error processing item {item}: {str(e)}")
                    # Add the original item if processing failed
                    processed_data.append(item)
        
        return processed_data

    def _process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single data item with transformations.
        
        Args:
            item (dict): Data item to process
            
        Returns:
            dict: Processed data item
        """
        processed_item = {}
        
        # Process each field
        for key, value in item.items():
            processed_value = self._process_field(key, value)
            processed_item[key] = processed_value
            
        # Add metadata
        processed_item['_metadata'] = {
            'processed_at': datetime.now().isoformat(),
            'processor_version': '1.0.0'
        }
        
        return processed_item

    def _process_field(self, field_name: str, value: Any) -> Any:
        """
        Process a field value based on common field types.
        
        Args:
            field_name (str): Name of the field
            value (any): Value to process
            
        Returns:
            any: Processed value
        """
        if value is None:
            return None
            
        # Process based on common field names
        
        # Price fields
        if 'price' in field_name.lower():
            return self._process_price(value)
            
        # Date fields
        elif any(date_term in field_name.lower() for date_term in ['date', 'time', 'published', 'created']):
            return self._process_date(value)
            
        # Text content
        elif any(text_term in field_name.lower() for text_term in ['description', 'content', 'text', 'body']):
            return self._process_text(value)
            
        # URLs
        elif any(url_term in field_name.lower() for url_term in ['url', 'link', 'href']):
            return self._process_url(value)
            
        # Ratings
        elif 'rating' in field_name.lower():
            return self._process_rating(value)
            
        # Lists
        elif isinstance(value, list):
            return [self._process_field(f"{field_name}_item", item) for item in value]
            
        # Default - just strip whitespace if it's a string
        elif isinstance(value, str):
            return value.strip()
            
        # Return unchanged for other types
        return value

    def _process_price(self, value: Union[str, float, int]) -> Optional[float]:
        """
        Process a price value.
        
        Args:
            value (str/float/int): Price to process
            
        Returns:
            float: Processed price or None if invalid
        """
        if isinstance(value, (int, float)):
            return float(value)
            
        if not isinstance(value, str):
            return None
            
        try:
            # Remove currency symbols and extra characters
            price_str = re.sub(r'[^\d.,]', '', value)
            
            # Handle different decimal/thousand separators
            if ',' in price_str and '.' in price_str:
                # Determine which is the decimal separator based on position
                if price_str.rindex('.') > price_str.rindex(','):
                    # Period is decimal separator
                    price_str = price_str.replace(',', '')
                else:
                    # Comma is decimal separator
                    price_str = price_str.replace('.', '').replace(',', '.')
            elif ',' in price_str:
                # If only comma is present, it could be a decimal or thousand separator
                # Assume it's a decimal if it's near the end
                if len(price_str) - price_str.rindex(',') <= 3:
                    price_str = price_str.replace(',', '.')
                else:
                    price_str = price_str.replace(',', '')
            
            return float(price_str)
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse price from '{value}': {str(e)}")
            return None

    def _process_date(self, value: str) -> Optional[str]:
        """
        Process a date value into ISO format.
        
        Args:
            value (str): Date string to process
            
        Returns:
            str: Processed date in ISO format or original string if parsing fails
        """
        if not isinstance(value, str):
            return str(value) if value is not None else None
            
        value = value.strip()
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%m-%d-%Y',
            '%b %d, %Y',
            '%B %d, %Y',
            '%d %b %Y',
            '%d %B %Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%fZ',
        ]
        
        # Try each format
        for fmt in date_formats:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        # If all formats fail, try to extract a date using regex
        try:
            # Look for patterns like YYYY-MM-DD
            date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', value)
            if date_match:
                year, month, day = date_match.groups()
                dt = datetime(int(year), int(month), int(day))
                return dt.isoformat()
                
            # Look for patterns like DD-MM-YYYY
            date_match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', value)
            if date_match:
                day, month, year = date_match.groups()
                dt = datetime(int(year), int(month), int(day))
                return dt.isoformat()
        except Exception:
            pass
        
        # Return the original value if all parsing attempts fail
        return value

    def _process_text(self, value: str) -> str:
        """
        Process a text value.
        
        Args:
            value (str): Text to process
            
        Returns:
            str: Processed text
        """
        if not isinstance(value, str):
            return str(value) if value is not None else ""
        
        # Strip whitespace and normalize spacing
        text = re.sub(r'\s+', ' ', value).strip()
        
        # Remove common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&apos;', "'")
        
        # Remove HTML tags if any remain
        text = re.sub(r'<[^>]+>', '', text)
        
        return text

    def _process_url(self, value: str) -> str:
        """
        Process a URL.
        
        Args:
            value (str): URL to process
            
        Returns:
            str: Processed URL
        """
        if not isinstance(value, str):
            return str(value) if value is not None else ""
        
        url = value.strip()
        
        # Ensure URL starts with http/https
        if url and not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url

    def _process_rating(self, value: Union[str, float, int]) -> Optional[float]:
        """
        Process a rating value.
        
        Args:
            value (str/float/int): Rating to process
            
        Returns:
            float: Processed rating or None if invalid
        """
        if isinstance(value, (int, float)):
            return float(value)
            
        if not isinstance(value, str):
            return None
            
        try:
            # Extract numeric part
            rating_str = re.search(r'([\d.]+)', value).group(1)
            rating = float(rating_str)
            
            # Check if the rating is out of 5 or 10 or 100
            if 'out of 5' in value.lower() or '/5' in value or value.lower().endswith('5'):
                # Already out of 5, keep as is
                pass
            elif 'out of 10' in value.lower() or '/10' in value or value.lower().endswith('10'):
                # Convert to out of 5
                rating = rating / 2
            elif 'out of 100' in value.lower() or '/100' in value or value.lower().endswith('100') or '%' in value:
                # Convert to out of 5
                rating = rating / 20
            
            return rating
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse rating from '{value}': {str(e)}")
            return None

    def consolidate_fields(self, data: List[Dict[str, Any]], field_mapping: Optional[Dict[str, List[str]]] = None) -> List[Dict[str, Any]]:
        """
        Consolidate similar fields across items.
        
        Args:
            data (list): List of data items
            field_mapping (dict, optional): Mapping of target fields to source fields
            
        Returns:
            list: Data with consolidated fields
        """
        if not data:
            return []
            
        # Default field mapping if none provided
        if not field_mapping:
            field_mapping = {
                'title': ['title', 'name', 'heading', 'product_title', 'product_name'],
                'description': ['description', 'desc', 'content', 'product_description', 'details'],
                'price': ['price', 'product_price', 'cost', 'amount'],
                'image': ['image', 'img', 'picture', 'photo', 'thumbnail', 'product_image'],
                'url': ['url', 'link', 'href', 'product_url'],
                'rating': ['rating', 'stars', 'score', 'product_rating'],
                'date': ['date', 'published_date', 'published', 'created', 'timestamp']
            }
        
        consolidated_data = []
        
        for item in data:
            new_item = {}
            
            # Check each target field
            for target_field, source_fields in field_mapping.items():
                # Find the first source field that exists in the item
                for source_field in source_fields:
                    if source_field in item and item[source_field] is not None:
                        new_item[target_field] = item[source_field]
                        break
            
            # Add any fields not covered by the mapping
            for field, value in item.items():
                if field not in [f for fields in field_mapping.values() for f in fields]:
                    new_item[field] = value
            
            consolidated_data.append(new_item)
        
        return consolidated_data

    def remove_duplicates(self, data: List[Dict[str, Any]], key_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Remove duplicate items from data.
        
        Args:
            data (list): List of data items
            key_fields (list, optional): Fields to use for duplicate detection
            
        Returns:
            list: Data with duplicates removed
        """
        if not data:
            return []
            
        # Default key fields if none provided
        if not key_fields:
            # Try to guess appropriate key fields based on available data
            sample = data[0]
            if 'url' in sample:
                key_fields = ['url']
            elif 'id' in sample:
                key_fields = ['id']
            elif all(field in sample for field in ['title', 'price']):
                key_fields = ['title', 'price']
            else:
                # Use all fields if we can't determine appropriate key fields
                key_fields = list(sample.keys())
        
        unique_items = {}
        
        for item in data:
            # Create a key based on the specified fields
            key_parts = []
            for field in key_fields:
                value = item.get(field)
                if isinstance(value, (list, dict)):
                    # Convert complex values to a stable string representation
                    value = json.dumps(value, sort_keys=True)
                key_parts.append(str(value))
            
            key = '|'.join(key_parts)
            
            if key not in unique_items:
                unique_items[key] = item
        
        return list(unique_items.values())

    def filter_data(self, data: List[Dict[str, Any]], conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter data based on conditions.
        
        Args:
            data (list): List of data items
            conditions (dict): Filtering conditions
            
        Returns:
            list: Filtered data
        """
        if not data or not conditions:
            return data
        
        filtered_data = []
        
        for item in data:
            matches = True
            
            for field, condition in conditions.items():
                if field not in item:
                    matches = False
                    break
                
                value = item[field]
                
                if isinstance(condition, (str, int, float, bool)):
                    # Simple equality check
                    if value != condition:
                        matches = False
                        break
                elif isinstance(condition, dict):
                    # Complex condition
                    if 'min' in condition and value < condition['min']:
                        matches = False
                        break
                    if 'max' in condition and value > condition['max']:
                        matches = False
                        break
                    if 'contains' in condition and condition['contains'] not in str(value):
                        matches = False
                        break
                    if 'regex' in condition and not re.search(condition['regex'], str(value)):
                        matches = False
                        break
            
            if matches:
                filtered_data.append(item)
        
        return filtered_data

    def sort_data(self, data: List[Dict[str, Any]], sort_by: str, ascending: bool = True) -> List[Dict[str, Any]]:
        """
        Sort data by a field.
        
        Args:
            data (list): List of data items
            sort_by (str): Field to sort by
            ascending (bool, optional): Sort in ascending order. Defaults to True.
            
        Returns:
            list: Sorted data
        """
        if not data or sort_by not in data[0]:
            return data
        
        # Define a key function that handles different types and None values
        def sort_key(item):
            value = item.get(sort_by)
            
            # Handle None values - they should sort at the end
            if value is None:
                return (1, None) if ascending else (0, None)
            
            # Return a tuple with a marker for the type to ensure stable sorting across types
            if isinstance(value, (int, float)):
                return (0, value) if ascending else (1, value)
            elif isinstance(value, str):
                return (0, value.lower()) if ascending else (1, value.lower())
            else:
                return (0, str(value)) if ascending else (1, str(value))
        
        return sorted(data, key=sort_key, reverse=not ascending)