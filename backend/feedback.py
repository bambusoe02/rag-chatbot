"""User feedback handling."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger


class FeedbackHandler:
    """Handle user feedback on responses."""
    
    def __init__(self, feedback_dir: str = "./data/feedback"):
        """Initialize feedback handler.
        
        Args:
            feedback_dir: Directory to store feedback data
        """
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.feedback_dir / "feedback.jsonl"
    
    def save_feedback(
        self,
        question: str,
        answer: str,
        is_positive: bool,
        comment: Optional[str] = None,
    ):
        """Save user feedback.
        
        Args:
            question: The question that was rated
            answer: The answer that was rated
            is_positive: True for thumbs up, False for thumbs down
            comment: Optional comment from user
        """
        try:
            feedback_entry = {
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "answer": answer[:500],  # Truncate long answers
                "is_positive": is_positive,
                "comment": comment,
            }
            
            with open(self.feedback_file, "a") as f:
                f.write(json.dumps(feedback_entry) + "\n")
            
            logger.info(f"Feedback saved: {'positive' if is_positive else 'negative'}")
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
    
    def get_feedback_stats(self) -> Dict[str, int]:
        """Get feedback statistics.
        
        Returns:
            Dictionary with feedback counts
        """
        try:
            if not self.feedback_file.exists():
                return {"positive": 0, "negative": 0, "total": 0}
            
            positive = 0
            negative = 0
            
            with open(self.feedback_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("is_positive"):
                            positive += 1
                        else:
                            negative += 1
                    except:
                        pass
            
            return {
                "positive": positive,
                "negative": negative,
                "total": positive + negative,
            }
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {"positive": 0, "negative": 0, "total": 0}
    
    def get_recent_feedback(self, limit: int = 20) -> List[Dict]:
        """Get recent feedback entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of feedback dictionaries
        """
        try:
            if not self.feedback_file.exists():
                return []
            
            feedback_entries = []
            with open(self.feedback_file, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        feedback_entries.append(json.loads(line.strip()))
                    except:
                        pass
            
            return list(reversed(feedback_entries))  # Most recent first
        except Exception as e:
            logger.error(f"Error getting recent feedback: {e}")
            return []


# Global feedback handler instance
feedback_handler = FeedbackHandler()

