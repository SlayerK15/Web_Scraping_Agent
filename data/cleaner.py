"""
Data Cleaner Module
Handles cleaning and standardization of scraped data.
"""

import logging
import re
import unicodedata
from typing import List, Dict, Any, Optional, Union, Set
import html
import json

logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self):
        """Initialize the data cleaner."""
        logger.info("Data cleaner initialized")

    def clean(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean a list of data items.
        
        Args:
            data (list): List of data items to clean
            
        Returns:
            list: Cleaned data items
        """
        if not data:
            logger.warning("No data to clean")
            return []
            
        logger.info(f"Cleaning {len(data)} data items")
        
        try:
            # Apply cleaning to each item
            cleaned_data = [self._clean_item(item) for item in data]
            
            # Remove any items that became empty after cleaning
            cleaned_data = [item for item in cleaned_data if item]
            
            # Check if the cleaning process removed all items
            if not cleaned_data:
                logger.warning("All items were removed during cleaning")
                return []
                
            # Standardize field names across all items
            cleaned_data = self._standardize_fields(cleaned_data)
            
            logger.info(f"Cleaning completed, {len(cleaned_data)} items remain")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error cleaning data: {str(e)}")
            return data  # Return original data on error

    def _clean_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean a single data item.
        
        Args:
            item (dict): Data item to clean
            
        Returns:
            dict: Cleaned data item
        """
        cleaned_item = {}
        
        try:
            for key, value in item.items():
                # Skip metadata fields
                if key.startswith('_'):
                    cleaned_item[key] = value
                    continue
                
                # Clean based on value type
                if isinstance(value, str):
                    cleaned_value = self._clean_string(value)
                    # Skip empty strings
                    if cleaned_value:
                        cleaned_item[key] = cleaned_value
                elif isinstance(value, list):
                    cleaned_list = self._clean_list(value)
                    # Skip empty lists
                    if cleaned_list:
                        cleaned_item[key] = cleaned_list
                elif isinstance(value, dict):
                    cleaned_dict = self._clean_item(value)
                    # Skip empty dicts
                    if cleaned_dict:
                        cleaned_item[key] = cleaned_dict
                else:
                    # Keep other types as is
                    cleaned_item[key] = value
                    
            return cleaned_item
            
        except Exception as e:
            logger.error(f"Error cleaning item: {str(e)}")
            return item  # Return original item on error

    def _clean_string(self, value: str) -> str:
        """
        Clean a string value.
        
        Args:
            value (str): String to clean
            
        Returns:
            str: Cleaned string
        """
        if not value:
            return ""
            
        try:
            # Unescape HTML entities
            text = html.unescape(value)
            
            # Strip HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            
            # Normalize unicode characters
            text = unicodedata.normalize('NFKC', text)
            
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Strip leading/trailing whitespace
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.error(f"Error cleaning string: {str(e)}")
            return value

    def _clean_list(self, value_list: List[Any]) -> List[Any]:
        """
        Clean a list of values.
        
        Args:
            value_list (list): List to clean
            
        Returns:
            list: Cleaned list
        """
        if not value_list:
            return []
            
        cleaned_list = []
        
        try:
            for item in value_list:
                if isinstance(item, str):
                    cleaned_item = self._clean_string(item)
                    if cleaned_item:  # Skip empty strings
                        cleaned_list.append(cleaned_item)
                elif isinstance(item, dict):
                    cleaned_item = self._clean_item(item)
                    if cleaned_item:  # Skip empty dicts
                        cleaned_list.append(cleaned_item)
                elif isinstance(item, list):
                    cleaned_item = self._clean_list(item)
                    if cleaned_item:  # Skip empty lists
                        cleaned_list.append(cleaned_item)
                else:
                    # Keep other types as is
                    cleaned_list.append(item)
                    
            return cleaned_list
            
        except Exception as e:
            logger.error(f"Error cleaning list: {str(e)}")
            return value_list

    def _standardize_fields(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Standardize field names across all items.
        
        Args:
            data (list): List of data items
            
        Returns:
            list: Data items with standardized field names
        """
        if not data:
            return []
            
        # Find all unique field names
        all_fields = set()
        for item in data:
            all_fields.update(item.keys())
            
        # Create field name mapping
        field_mapping = self._create_field_mapping(all_fields)
        
        # Apply mapping to all items
        standardized_data = []
        
        for item in data:
            standardized_item = {}
            
            for old_field, value in item.items():
                new_field = field_mapping.get(old_field, old_field)
                standardized_item[new_field] = value
                
            standardized_data.append(standardized_item)
            
        return standardized_data

    def _create_field_mapping(self, fields: Set[str]) -> Dict[str, str]:
        """
        Create a mapping of field names to standardized names.
        
        Args:
            fields (set): Set of field names to standardize
            
        Returns:
            dict: Mapping of original field names to standardized names
        """
        # Common field name variants
        common_variants = {
            'title': ['name', 'heading', 'product_title', 'product_name', 'item_title', 'item_name'],
            'description': ['desc', 'content', 'product_description', 'item_description', 'details', 'summary'],
            'price': ['cost', 'amount', 'product_price', 'item_price', 'value'],
            'url': ['link', 'href', 'product_url', 'item_url', 'page'],
            'image': ['img', 'picture', 'photo', 'thumbnail', 'product_image', 'item_image'],
            'rating': ['rate', 'stars', 'score', 'product_rating', 'item_rating', 'review'],
            'category': ['cat', 'group', 'type', 'product_category', 'item_category'],
            'brand': ['make', 'manufacturer', 'company', 'product_brand', 'item_brand'],
            'sku': ['id', 'product_id', 'item_id', 'identifier', 'product_code', 'item_code']
        }
        
        # Create mapping
        mapping = {}
        
        for standard_name, variants in common_variants.items():
            for variant in variants:
                # Find fields that match this variant (case insensitive)
                matches = [field for field in fields if field.lower() == variant.lower()]
                
                # If standard_name exists in fields, don't map to it
                if standard_name in fields and matches:
                    continue
                    
                # Add mapping for matching fields
                for match in matches:
                    mapping[match] = standard_name
        
        return mapping

    def remove_empty_fields(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove empty fields from all items.
        
        Args:
            data (list): List of data items
            
        Returns:
            list: Data items with empty fields removed
        """
        if not data:
            return []
            
        cleaned_data = []
        
        for item in data:
            cleaned_item = {}
            
            for key, value in item.items():
                # Skip empty values
                if value is None:
                    continue
                    
                if isinstance(value, str) and not value.strip():
                    continue
                    
                if isinstance(value, (list, dict)) and not value:
                    continue
                    
                cleaned_item[key] = value
                
            # Only add items that still have fields after cleaning
            if cleaned_item:
                cleaned_data.append(cleaned_item)
                
        return cleaned_data

    def normalize_text_case(self, data: List[Dict[str, Any]], fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Normalize text case for specified fields.
        
        Args:
            data (list): List of data items
            fields (list, optional): Fields to normalize. Defaults to title and name fields.
            
        Returns:
            list: Data with normalized text case
        """
        if not data:
            return []
            
        # Default fields if none provided
        if not fields:
            fields = ['title', 'name', 'product_title', 'product_name', 'item_title', 'item_name']
            
        normalized_data = []
        
        for item in data:
            normalized_item = dict(item)  # Make a copy
            
            for field in fields:
                if field in item and isinstance(item[field], str):
                    # Title case for these fields
                    normalized_item[field] = self._title_case(item[field])
                    
            normalized_data.append(normalized_item)
            
        return normalized_data

    def _title_case(self, text: str) -> str:
        """
        Convert text to title case while preserving certain words.
        
        Args:
            text (str): Text to convert
            
        Returns:
            str: Title cased text
        """
        if not text:
            return ""
            
        # Words to keep lowercase
        lowercase_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at',
                          'to', 'from', 'by', 'of', 'in', 'with', 'as'}
        
        # Split the text
        words = text.split()
        
        if not words:
            return ""
            
        # Capitalize first and last word always
        result = [words[0].capitalize()]
        
        # Process middle words
        for word in words[1:-1]:
            if word.lower() in lowercase_words and not word.isupper():
                result.append(word.lower())
            else:
                # Keep abbreviations in uppercase
                if word.isupper() and len(word) <= 5:
                    result.append(word)
                else:
                    result.append(word.capitalize())
        
        # Add last word if it exists
        if len(words) > 1:
            result.append(words[-1].capitalize())
            
        return ' '.join(result)

    def clean_prices(self, data: List[Dict[str, Any]], price_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Clean and standardize price fields.
        
        Args:
            data (list): List of data items
            price_fields (list, optional): Fields containing prices. Defaults to None.
            
        Returns:
            list: Data with cleaned prices
        """
        if not data:
            return []
            
        # Default price fields if none provided
        if not price_fields:
            price_fields = ['price', 'cost', 'amount', 'product_price', 'item_price', 'value']
            
        cleaned_data = []
        
        for item in data:
            cleaned_item = dict(item)  # Make a copy
            
            for field in price_fields:
                if field in item:
                    value = item[field]
                    
                    if isinstance(value, (int, float)):
                        # Format as 2 decimal places
                        cleaned_item[field] = round(float(value), 2)
                    elif isinstance(value, str):
                        # Extract numeric part from string
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
                            
                            cleaned_item[field] = round(float(price_str), 2)
                        except (ValueError, AttributeError):
                            # Keep original if parsing fails
                            pass
                    
            cleaned_data.append(cleaned_item)
            
        return cleaned_data

    def clean_urls(self, data: List[Dict[str, Any]], url_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Clean and standardize URL fields.
        
        Args:
            data (list): List of data items
            url_fields (list, optional): Fields containing URLs. Defaults to None.
            
        Returns:
            list: Data with cleaned URLs
        """
        if not data:
            return []
            
        # Default URL fields if none provided
        if not url_fields:
            url_fields = ['url', 'link', 'href', 'product_url', 'item_url', 'image_url', 'thumbnail_url']
            
        cleaned_data = []
        
        for item in data:
            cleaned_item = dict(item)  # Make a copy
            
            for field in url_fields:
                if field in item and isinstance(item[field], str):
                    url = item[field].strip()
                    
                    # Ensure URL has a scheme
                    if url and not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                        
                    # Encode spaces if present
                    if ' ' in url:
                        url = url.replace(' ', '%20')
                        
                    cleaned_item[field] = url
                    
            cleaned_data.append(cleaned_item)
            
        return cleaned_data

    def clean_html_content(self, data: List[Dict[str, Any]], html_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Clean HTML content in specified fields.
        
        Args:
            data (list): List of data items
            html_fields (list, optional): Fields containing HTML. Defaults to None.
            
        Returns:
            list: Data with cleaned HTML content
        """
        if not data:
            return []
            
        # Default HTML fields if none provided
        if not html_fields:
            html_fields = ['description', 'content', 'product_description', 'item_description', 'details', 'summary']
            
        cleaned_data = []
        
        for item in data:
            cleaned_item = dict(item)  # Make a copy
            
            for field in html_fields:
                if field in item and isinstance(item[field], str):
                    html_content = item[field]
                    
                    # Strip HTML tags
                    text = re.sub(r'<[^>]+>', '', html_content)
                    
                    # Unescape HTML entities
                    text = html.unescape(text)
                    
                    # Normalize whitespace
                    text = re.sub(r'\s+', ' ', text)
                    
                    # Strip leading/trailing whitespace
                    text = text.strip()
                    
                    cleaned_item[field] = text
                    
            cleaned_data.append(cleaned_item)
            
        return cleaned_data