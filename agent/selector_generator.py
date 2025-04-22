"""
Selector Generator Module
This module uses Generative AI to create CSS selectors for web scraping based on
natural language descriptions of the data to be extracted.
"""

import os
import logging
import json
import requests
from typing import Dict, List, Any, Optional
import time
import random

from config.settings import load_config

logger = logging.getLogger(__name__)

class SelectorGenerator:
    def __init__(self):
        """Initialize the selector generator with configuration."""
        self.config = load_config().get('ai', {})
        self.api_provider = self.config.get('provider', 'anthropic')
        self.api_key = os.environ.get(f"{self.api_provider.upper()}_API_KEY")
        
        if not self.api_key:
            logger.warning(f"No API key found for {self.api_provider}. "
                          f"Set {self.api_provider.upper()}_API_KEY environment variable.")
        
        logger.info(f"Selector generator initialized with {self.api_provider} API")

    def generate_selectors(self, url: str, data_description: str) -> Dict[str, Any]:
        """
        Generate CSS selectors using generative AI.
        
        Args:
            url (str): The URL to generate selectors for
            data_description (str): Description of data to extract
            
        Returns:
            dict: Dictionary of generated selectors and metadata
        """
        logger.info(f"Generating selectors for URL: {url}")
        logger.info(f"Data description: {data_description}")
        
        if self.api_provider == 'anthropic':
            selectors = self._generate_with_anthropic(url, data_description)
        elif self.api_provider == 'openai':
            selectors = self._generate_with_openai(url, data_description)
        else:
            raise ValueError(f"Unsupported AI provider: {self.api_provider}")
        
        logger.info(f"Generated {len(selectors.get('selectors', []))} selectors")
        
        # Add metadata to the selectors
        selectors['metadata'] = {
            'generated_at': time.time(),
            'url': url,
            'data_description': data_description,
            'provider': self.api_provider
        }
        
        return selectors

    def refine_selectors(self, url: str, data_description: str, 
                         existing_selectors: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Refine existing selectors based on feedback.
        
        Args:
            url (str): The URL the selectors were used on
            data_description (str): Original data description
            existing_selectors (dict): Previously generated selectors
            feedback (str): User feedback or error message
            
        Returns:
            dict: Dictionary of refined selectors and metadata
        """
        logger.info(f"Refining selectors based on feedback: {feedback}")
        
        if self.api_provider == 'anthropic':
            refined_selectors = self._refine_with_anthropic(
                url, data_description, existing_selectors, feedback
            )
        elif self.api_provider == 'openai':
            refined_selectors = self._refine_with_openai(
                url, data_description, existing_selectors, feedback
            )
        else:
            raise ValueError(f"Unsupported AI provider: {self.api_provider}")
        
        # Update metadata
        refined_selectors['metadata'] = {
            'generated_at': time.time(),
            'url': url,
            'data_description': data_description,
            'provider': self.api_provider,
            'refined': True,
            'original_selectors': existing_selectors.get('selectors', []),
            'feedback': feedback
        }
        
        logger.info(f"Generated {len(refined_selectors.get('selectors', []))} refined selectors")
        return refined_selectors

    def _generate_with_anthropic(self, url: str, data_description: str) -> Dict[str, Any]:
        """
        Generate selectors using Anthropic Claude API.
        
        Args:
            url (str): URL to generate selectors for
            data_description (str): Description of data to extract
            
        Returns:
            dict: Dictionary with generated selectors
        """
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        logger.info("Generating selectors using Anthropic API")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            # Create the prompt for Claude
            prompt = f"""
            I need to scrape data from the website: {url}
            
            The data I want to extract is: {data_description}
            
            Please generate CSS selectors that would efficiently extract this data from the webpage.
            For each type of data, provide:
            1. A descriptive name for the data element
            2. The CSS selector to extract it
            3. The type of data (text, attribute, etc.)
            4. Any post-processing needed
            
            Format your response as valid JSON that I can directly use in my scraper, following this structure:
            {{
                "selectors": [
                    {{
                        "name": "data_element_name",
                        "selector": "css_selector",
                        "type": "text|attribute|href|etc",
                        "attribute": "attribute_name_if_applicable",
                        "multiple": true|false,
                        "post_processing": "any_regex_or_transformation_needed"
                    }}
                ],
                "pagination": {{
                    "selector": "selector_for_next_page_button",
                    "type": "link|button|etc"
                }}
            }}
            
            Return ONLY the JSON with no additional text.
            """
            
            data = {
                "model": "claude-3-opus-20240229",
                "max_tokens": 1000,
                "temperature": 0.2,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                raise Exception(f"Anthropic API error: {response.status_code}")
            
            response_json = response.json()
            content = response_json.get('content', [{}])[0].get('text', '{}')
            
            # Extract JSON from the response - sometimes Claude adds backticks or explanations
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                # Try to find just a JSON object if no code block
                json_match = re.search(r'({.*})', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            
            selectors = json.loads(content)
            return selectors
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Anthropic response: {e}")
            logger.debug(f"Raw response: {content}")
            # Return a basic structure if parsing failed
            return {
                "selectors": [],
                "pagination": {"selector": "", "type": "link"}
            }
            
        except Exception as e:
            logger.error(f"Error generating selectors with Anthropic: {str(e)}")
            # Return a basic structure on error
            return {
                "selectors": [],
                "pagination": {"selector": "", "type": "link"}
            }

    def _generate_with_openai(self, url: str, data_description: str) -> Dict[str, Any]:
        """
        Generate selectors using OpenAI API.
        
        Args:
            url (str): URL to generate selectors for
            data_description (str): Description of data to extract
            
        Returns:
            dict: Dictionary with generated selectors
        """
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        logger.info("Generating selectors using OpenAI API")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Create the prompt for GPT
            prompt = f"""
            I need to scrape data from the website: {url}
            
            The data I want to extract is: {data_description}
            
            Please generate CSS selectors that would efficiently extract this data from the webpage.
            For each type of data, provide:
            1. A descriptive name for the data element
            2. The CSS selector to extract it
            3. The type of data (text, attribute, etc.)
            4. Any post-processing needed
            
            Format your response as valid JSON that I can directly use in my scraper, following this structure:
            {{
                "selectors": [
                    {{
                        "name": "data_element_name",
                        "selector": "css_selector",
                        "type": "text|attribute|href|etc",
                        "attribute": "attribute_name_if_applicable",
                        "multiple": true|false,
                        "post_processing": "any_regex_or_transformation_needed"
                    }}
                ],
                "pagination": {{
                    "selector": "selector_for_next_page_button",
                    "type": "link|button|etc"
                }}
            }}
            
            Return ONLY the JSON with no additional text.
            """
            
            data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a CSS selector generation assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1000
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise Exception(f"OpenAI API error: {response.status_code}")
            
            response_json = response.json()
            content = response_json.get('choices', [{}])[0].get('message', {}).get('content', '{}')
            
            # Extract JSON from the response - sometimes GPT adds backticks or explanations
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                # Try to find just a JSON object if no code block
                json_match = re.search(r'({.*})', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            
            selectors = json.loads(content)
            return selectors
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}")
            logger.debug(f"Raw response: {content}")
            # Return a basic structure if parsing failed
            return {
                "selectors": [],
                "pagination": {"selector": "", "type": "link"}
            }
            
        except Exception as e:
            logger.error(f"Error generating selectors with OpenAI: {str(e)}")
            # Return a basic structure on error
            return {
                "selectors": [],
                "pagination": {"selector": "", "type": "link"}
            }

    def _refine_with_anthropic(self, url: str, data_description: str, 
                              existing_selectors: Dict[str, Any], 
                              feedback: str) -> Dict[str, Any]:
        """
        Refine selectors using Anthropic Claude API.
        
        Args:
            url (str): URL the selectors were used on
            data_description (str): Original data description
            existing_selectors (dict): Previously generated selectors
            feedback (str): User feedback or error message
            
        Returns:
            dict: Dictionary with refined selectors
        """
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        logger.info("Refining selectors using Anthropic API")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            # Create the prompt for Claude
            prompt = f"""
            I need to improve my CSS selectors for scraping data from: {url}
            
            The data I want to extract is: {data_description}
            
            These are my current selectors:
            {json.dumps(existing_selectors.get('selectors', []), indent=2)}
            
            Pagination selector:
            {json.dumps(existing_selectors.get('pagination', {}), indent=2)}
            
            The problem/feedback I received is:
            {feedback}
            
            Please provide improved CSS selectors that address these issues. Format your response as valid JSON:
            {{
                "selectors": [
                    {{
                        "name": "data_element_name",
                        "selector": "css_selector",
                        "type": "text|attribute|href|etc",
                        "attribute": "attribute_name_if_applicable",
                        "multiple": true|false,
                        "post_processing": "any_regex_or_transformation_needed"
                    }}
                ],
                "pagination": {{
                    "selector": "selector_for_next_page_button",
                    "type": "link|button|etc"
                }}
            }}
            
            Return ONLY the JSON with no additional text.
            """
            
            data = {
                "model": "claude-3-opus-20240229",
                "max_tokens": 1000,
                "temperature": 0.2,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                raise Exception(f"Anthropic API error: {response.status_code}")
            
            response_json = response.json()
            content = response_json.get('content', [{}])[0].get('text', '{}')
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                # Try to find just a JSON object if no code block
                json_match = re.search(r'({.*})', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            
            refined_selectors = json.loads(content)
            return refined_selectors
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Anthropic response: {e}")
            logger.debug(f"Raw response: {content}")
            # Return the existing selectors if parsing failed
            return existing_selectors
            
        except Exception as e:
            logger.error(f"Error refining selectors with Anthropic: {str(e)}")
            # Return the existing selectors on error
            return existing_selectors

    def _refine_with_openai(self, url: str, data_description: str, 
                           existing_selectors: Dict[str, Any], 
                           feedback: str) -> Dict[str, Any]:
        """
        Refine selectors using OpenAI API.
        
        Args:
            url (str): URL the selectors were used on
            data_description (str): Original data description
            existing_selectors (dict): Previously generated selectors
            feedback (str): User feedback or error message
            
        Returns:
            dict: Dictionary with refined selectors
        """
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        logger.info("Refining selectors using OpenAI API")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Create the prompt for GPT
            prompt = f"""
            I need to improve my CSS selectors for scraping data from: {url}
            
            The data I want to extract is: {data_description}
            
            These are my current selectors:
            {json.dumps(existing_selectors.get('selectors', []), indent=2)}
            
            Pagination selector:
            {json.dumps(existing_selectors.get('pagination', {}), indent=2)}
            
            The problem/feedback I received is:
            {feedback}
            
            Please provide improved CSS selectors that address these issues. Format your response as valid JSON:
            {{
                "selectors": [
                    {{
                        "name": "data_element_name",
                        "selector": "css_selector",
                        "type": "text|attribute|href|etc",
                        "attribute": "attribute_name_if_applicable",
                        "multiple": true|false,
                        "post_processing": "any_regex_or_transformation_needed"
                    }}
                ],
                "pagination": {{
                    "selector": "selector_for_next_page_button",
                    "type": "link|button|etc"
                }}
            }}
            
            Return ONLY the JSON with no additional text.
            """
            
            data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a CSS selector improvement assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1000
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise Exception(f"OpenAI API error: {response.status_code}")
            
            response_json = response.json()
            content = response_json.get('choices', [{}])[0].get('message', {}).get('content', '{}')
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                # Try to find just a JSON object if no code block
                json_match = re.search(r'({.*})', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            
            refined_selectors = json.loads(content)
            return refined_selectors
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}")
            logger.debug(f"Raw response: {content}")
            # Return the existing selectors if parsing failed
            return existing_selectors
            
        except Exception as e:
            logger.error(f"Error refining selectors with OpenAI: {str(e)}")
            # Return the existing selectors on error
            return existing_selectors