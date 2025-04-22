"""
Feedback Handler Module
This module stores and processes user feedback to improve
selector generation over time.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)

class FeedbackHandler:
    def __init__(self, feedback_dir: Optional[str] = None):
        """
        Initialize the feedback handler.
        
        Args:
            feedback_dir (str, optional): Directory to store feedback. Defaults to None.
        """
        if feedback_dir is None:
            # Default to /storage/feedback in project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            feedback_dir = os.path.join(base_dir, 'storage', 'feedback')
        
        self.feedback_dir = feedback_dir
        
        # Ensure feedback directory exists
        os.makedirs(self.feedback_dir, exist_ok=True)
        
        logger.info(f"Feedback handler initialized in {self.feedback_dir}")

    def store_feedback(self, task_id: str, url: str, data_description: str, 
                      rating: Optional[int] = None, feedback: Optional[str] = None) -> bool:
        """
        Store user feedback for a scraping task.
        
        Args:
            task_id (str): Unique identifier for the task
            url (str): URL that was scraped
            data_description (str): Description of data that was scraped
            rating (int, optional): Numerical rating (1-10). Defaults to None.
            feedback (str, optional): Text feedback. Defaults to None.
            
        Returns:
            bool: True if feedback was stored successfully, False otherwise
        """
        try:
            # Create feedback data structure
            feedback_data = {
                "task_id": task_id,
                "url": url,
                "data_description": data_description,
                "rating": rating,
                "feedback": feedback,
                "timestamp": time.time()
            }
            
            # Generate a unique filename for this feedback
            timestamp_str = int(time.time())
            safe_task_id = "".join(c if c.isalnum() else "_" for c in task_id)
            file_name = f"{safe_task_id}_{timestamp_str}.json"
            file_path = os.path.join(self.feedback_dir, file_name)
            
            # Write feedback to file
            with open(file_path, 'w') as f:
                json.dump(feedback_data, f, indent=2)
                
            logger.info(f"Stored feedback for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store feedback for task {task_id}: {str(e)}")
            return False

    def get_feedback_for_task(self, task_id: str) -> list:
        """
        Retrieve all feedback for a specific task.
        
        Args:
            task_id (str): Unique identifier for the task
            
        Returns:
            list: List of feedback entries for the task
        """
        feedback_list = []
        
        try:
            safe_task_id = "".join(c if c.isalnum() else "_" for c in task_id)
            
            for file_name in os.listdir(self.feedback_dir):
                if file_name.startswith(f"{safe_task_id}_") and file_name.endswith('.json'):
                    file_path = os.path.join(self.feedback_dir, file_name)
                    
                    with open(file_path, 'r') as f:
                        feedback_data = json.load(f)
                        feedback_list.append(feedback_data)
            
            # Sort by timestamp (newest first)
            feedback_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            return feedback_list
            
        except Exception as e:
            logger.error(f"Error retrieving feedback for task {task_id}: {str(e)}")
            return []

    def get_domain_feedback(self, domain: str) -> list:
        """
        Retrieve all feedback for a specific domain.
        
        Args:
            domain (str): Domain to get feedback for
            
        Returns:
            list: List of feedback entries for the domain
        """
        feedback_list = []
        
        try:
            for file_name in os.listdir(self.feedback_dir):
                if not file_name.endswith('.json'):
                    continue
                    
                file_path = os.path.join(self.feedback_dir, file_name)
                
                with open(file_path, 'r') as f:
                    feedback_data = json.load(f)
                    
                url = feedback_data.get('url', '')
                if domain in url:
                    feedback_list.append(feedback_data)
            
            # Sort by timestamp (newest first)
            feedback_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            return feedback_list
            
        except Exception as e:
            logger.error(f"Error retrieving feedback for domain {domain}: {str(e)}")
            return []

    def get_average_rating(self, task_id: Optional[str] = None, 
                          domain: Optional[str] = None) -> float:
        """
        Get average rating for a task or domain.
        
        Args:
            task_id (str, optional): Task ID to get average for. Defaults to None.
            domain (str, optional): Domain to get average for. Defaults to None.
            
        Returns:
            float: Average rating or 0 if no ratings found
        """
        ratings = []
        
        try:
            if task_id:
                feedback_list = self.get_feedback_for_task(task_id)
            elif domain:
                feedback_list = self.get_domain_feedback(domain)
            else:
                # Get all feedback
                feedback_list = []
                for file_name in os.listdir(self.feedback_dir):
                    if not file_name.endswith('.json'):
                        continue
                        
                    file_path = os.path.join(self.feedback_dir, file_name)
                    
                    with open(file_path, 'r') as f:
                        feedback_data = json.load(f)
                        feedback_list.append(feedback_data)
            
            # Extract ratings
            for feedback in feedback_list:
                rating = feedback.get('rating')
                if rating is not None:
                    ratings.append(rating)
            
            if ratings:
                return sum(ratings) / len(ratings)
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Error calculating average rating: {str(e)}")
            return 0

    def get_recent_feedback(self, limit: int = 10) -> list:
        """
        Get most recent feedback entries.
        
        Args:
            limit (int, optional): Maximum number of entries to return. Defaults to 10.
            
        Returns:
            list: List of recent feedback entries
        """
        feedback_list = []
        
        try:
            for file_name in os.listdir(self.feedback_dir):
                if not file_name.endswith('.json'):
                    continue
                    
                file_path = os.path.join(self.feedback_dir, file_name)
                
                with open(file_path, 'r') as f:
                    feedback_data = json.load(f)
                    feedback_list.append(feedback_data)
            
            # Sort by timestamp (newest first)
            feedback_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            return feedback_list[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving recent feedback: {str(e)}")
            return []

    def analyze_common_issues(self) -> Dict[str, int]:
        """
        Analyze feedback to identify common issues.
        
        Returns:
            dict: Dictionary of common issues and their frequencies
        """
        issues = {}
        
        try:
            for file_name in os.listdir(self.feedback_dir):
                if not file_name.endswith('.json'):
                    continue
                    
                file_path = os.path.join(self.feedback_dir, file_name)
                
                with open(file_path, 'r') as f:
                    feedback_data = json.load(f)
                
                feedback_text = feedback_data.get('feedback', '')
                if not feedback_text:
                    continue
                
                # Simple keyword detection for common issues
                keywords = [
                    "missing data", "wrong data", "incomplete", "error", 
                    "slow", "timeout", "blocked", "captcha", "wrong format",
                    "duplicate", "empty", "not working"
                ]
                
                for keyword in keywords:
                    if keyword.lower() in feedback_text.lower():
                        issues[keyword] = issues.get(keyword, 0) + 1
            
            return issues
            
        except Exception as e:
            logger.error(f"Error analyzing common issues: {str(e)}")
            return {}