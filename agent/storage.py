"""
Selector Storage Module
This module handles the persistence and retrieval of generated selectors.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SelectorStorage:
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the selector storage.
        
        Args:
            storage_dir (str, optional): Directory to store selectors. Defaults to None.
        """
        if storage_dir is None:
            # Default to /storage/selectors in project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            storage_dir = os.path.join(base_dir, 'storage', 'selectors')
        
        self.storage_dir = storage_dir
        
        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        
        logger.info(f"Selector storage initialized in {self.storage_dir}")

    def save_selector(self, task_id: str, selector_data: Dict[str, Any]) -> bool:
        """
        Save selector data to disk.
        
        Args:
            task_id (str): Unique identifier for the task
            selector_data (dict): Selector data to save
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Ensure task_id is safe for filenames (alphanumeric and underscores only)
            safe_task_id = "".join(c if c.isalnum() else "_" for c in task_id)
            file_path = os.path.join(self.storage_dir, f"{safe_task_id}.json")
            
            with open(file_path, 'w') as f:
                json.dump(selector_data, f, indent=2)
            
            logger.info(f"Saved selector data for task {task_id} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save selector data for task {task_id}: {str(e)}")
            return False

    def get_selector(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve selector data for a given task.
        
        Args:
            task_id (str): Unique identifier for the task
            
        Returns:
            dict: Selector data if found, None otherwise
        """
        try:
            safe_task_id = "".join(c if c.isalnum() else "_" for c in task_id)
            file_path = os.path.join(self.storage_dir, f"{safe_task_id}.json")
            
            if not os.path.exists(file_path):
                logger.info(f"No selector data found for task {task_id}")
                return None
            
            with open(file_path, 'r') as f:
                selector_data = json.load(f)
            
            logger.info(f"Retrieved selector data for task {task_id}")
            return selector_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve selector data for task {task_id}: {str(e)}")
            return None

    def list_selectors(self) -> Dict[str, str]:
        """
        List all stored selectors with their timestamps.
        
        Returns:
            dict: Dictionary mapping task_ids to timestamps
        """
        selectors = {}
        
        try:
            for file_name in os.listdir(self.storage_dir):
                if not file_name.endswith('.json'):
                    continue
                
                file_path = os.path.join(self.storage_dir, file_name)
                task_id = os.path.splitext(file_name)[0]
                
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        timestamp = data.get('metadata', {}).get('generated_at', 'unknown')
                        selectors[task_id] = timestamp
                except:
                    selectors[task_id] = 'unknown'
            
            return selectors
            
        except Exception as e:
            logger.error(f"Error listing selectors: {str(e)}")
            return {}

    def delete_selector(self, task_id: str) -> bool:
        """
        Delete selector data for a task.
        
        Args:
            task_id (str): Unique identifier for the task
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            safe_task_id = "".join(c if c.isalnum() else "_" for c in task_id)
            file_path = os.path.join(self.storage_dir, f"{safe_task_id}.json")
            
            if not os.path.exists(file_path):
                logger.warning(f"No selector data found for task {task_id}")
                return False
            
            os.remove(file_path)
            logger.info(f"Deleted selector data for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete selector data for task {task_id}: {str(e)}")
            return False

    def find_similar_selector(self, url: str, data_description: str) -> Optional[Dict[str, Any]]:
        """
        Find a selector that might be suitable for a similar task.
        
        Args:
            url (str): URL to look for
            data_description (str): Data description to match
            
        Returns:
            dict: Most similar selector data if found, None otherwise
        """
        url_domain = url.split('//')[-1].split('/')[0]
        
        best_match = None
        highest_similarity = 0
        
        try:
            for file_name in os.listdir(self.storage_dir):
                if not file_name.endswith('.json'):
                    continue
                    
                file_path = os.path.join(self.storage_dir, file_name)
                
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    metadata = data.get('metadata', {})
                    stored_url = metadata.get('url', '')
                    stored_description = metadata.get('data_description', '')
                    
                    # Check if domains match
                    stored_domain = stored_url.split('//')[-1].split('/')[0]
                    domain_match = url_domain == stored_domain
                    
                    if domain_match:
                        # Calculate simple similarity score for description
                        description_words = set(data_description.lower().split())
                        stored_words = set(stored_description.lower().split())
                        
                        if description_words and stored_words:
                            common_words = description_words.intersection(stored_words)
                            similarity = len(common_words) / max(len(description_words), len(stored_words))
                            
                            if similarity > highest_similarity:
                                highest_similarity = similarity
                                best_match = data
                                
                except Exception as e:
                    logger.warning(f"Error processing selector file {file_name}: {str(e)}")
                    continue
            
            if highest_similarity > 0.5:  # Threshold for similarity
                logger.info(f"Found similar selector with similarity score {highest_similarity}")
                return best_match
            else:
                logger.info("No similar selector found")
                return None
                
        except Exception as e:
            logger.error(f"Error finding similar selector: {str(e)}")
            return None