"""Analytics tracking and statistics generation."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import Counter, defaultdict

from loguru import logger

from backend.config import settings


class AnalyticsTracker:
    """Track usage analytics and generate statistics."""
    
    def __init__(self, analytics_dir: str = "./data/analytics"):
        """Initialize analytics tracker.
        
        Args:
            analytics_dir: Directory to store analytics data
        """
        self.analytics_dir = Path(analytics_dir)
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file = self.analytics_dir / "stats.json"
        self.queries_file = self.analytics_dir / "queries.jsonl"
        
        # Initialize stats if not exists
        if not self.stats_file.exists():
            self._init_stats()
    
    def _init_stats(self):
        """Initialize statistics file."""
        initial_stats = {
            "total_queries": 0,
            "total_documents": 0,
            "total_chunks": 0,
            "average_response_time": 0.0,
            "total_feedback_positive": 0,
            "total_feedback_negative": 0,
            "queries_by_date": {},
            "top_queries": [],
            "documents_usage": {},
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }
        self._save_stats(initial_stats)
    
    def _load_stats(self) -> Dict[str, Any]:
        """Load statistics from file."""
        try:
            with open(self.stats_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
            self._init_stats()
            return self._load_stats()
    
    def _save_stats(self, stats: Dict[str, Any]):
        """Save statistics to file."""
        try:
            stats["last_updated"] = datetime.now().isoformat()
            with open(self.stats_file, "w") as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def track_query(
        self,
        question: str,
        response_time: float,
        sources_count: int = 0,
        documents_used: Optional[List[str]] = None,
    ):
        """Track a query.
        
        Args:
            question: User question
            response_time: Response time in seconds
            sources_count: Number of sources used
            documents_used: List of document names used
        """
        try:
            stats = self._load_stats()
            
            # Update totals
            stats["total_queries"] = stats.get("total_queries", 0) + 1
            
            # Update average response time
            current_avg = stats.get("average_response_time", 0.0)
            total_queries = stats["total_queries"]
            stats["average_response_time"] = (
                (current_avg * (total_queries - 1) + response_time) / total_queries
            )
            
            # Update queries by date
            today = datetime.now().strftime("%Y-%m-%d")
            stats["queries_by_date"][today] = stats["queries_by_date"].get(today, 0) + 1
            
            # Update top queries
            top_queries = stats.get("top_queries", [])
            top_queries.append({"question": question, "timestamp": datetime.now().isoformat()})
            # Keep last 100 queries
            if len(top_queries) > 100:
                top_queries = top_queries[-100:]
            stats["top_queries"] = top_queries
            
            # Update documents usage
            if documents_used:
                doc_usage = stats.get("documents_usage", {})
                for doc in documents_used:
                    doc_usage[doc] = doc_usage.get(doc, 0) + 1
                stats["documents_usage"] = doc_usage
            
            self._save_stats(stats)
            
            # Also log query to JSONL file
            query_log = {
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "response_time": response_time,
                "sources_count": sources_count,
                "documents_used": documents_used or [],
            }
            with open(self.queries_file, "a") as f:
                f.write(json.dumps(query_log) + "\n")
                
        except Exception as e:
            logger.error(f"Error tracking query: {e}")
    
    def track_feedback(self, question: str, is_positive: bool):
        """Track user feedback.
        
        Args:
            question: The question that was rated
            is_positive: True for thumbs up, False for thumbs down
        """
        try:
            stats = self._load_stats()
            if is_positive:
                stats["total_feedback_positive"] = stats.get("total_feedback_positive", 0) + 1
            else:
                stats["total_feedback_negative"] = stats.get("total_feedback_negative", 0) + 1
            self._save_stats(stats)
        except Exception as e:
            logger.error(f"Error tracking feedback: {e}")
    
    def update_document_stats(self, total_documents: int, total_chunks: int):
        """Update document statistics.
        
        Args:
            total_documents: Total number of documents
            total_chunks: Total number of chunks
        """
        try:
            stats = self._load_stats()
            stats["total_documents"] = total_documents
            stats["total_chunks"] = total_chunks
            self._save_stats(stats)
        except Exception as e:
            logger.error(f"Error updating document stats: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics.
        
        Returns:
            Dictionary with all statistics
        """
        stats = self._load_stats()
        
        # Calculate additional stats
        queries_by_date = stats.get("queries_by_date", {})
        if queries_by_date:
            stats["queries_today"] = queries_by_date.get(datetime.now().strftime("%Y-%m-%d"), 0)
            stats["queries_this_week"] = sum(
                count for date, count in queries_by_date.items()
                if (datetime.now() - datetime.fromisoformat(date + "T00:00:00")).days < 7
            )
        
        # Calculate success rate
        positive = stats.get("total_feedback_positive", 0)
        negative = stats.get("total_feedback_negative", 0)
        total_feedback = positive + negative
        if total_feedback > 0:
            stats["success_rate"] = (positive / total_feedback) * 100
        else:
            stats["success_rate"] = 0.0
        
        # Get top documents
        doc_usage = stats.get("documents_usage", {})
        stats["top_documents"] = sorted(
            doc_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return stats
    
    def get_query_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get query history.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of query dictionaries
        """
        try:
            if not self.queries_file.exists():
                return []
            
            queries = []
            with open(self.queries_file, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        queries.append(json.loads(line.strip()))
                    except:
                        pass
            
            return list(reversed(queries))  # Most recent first
        except Exception as e:
            logger.error(f"Error getting query history: {e}")
            return []
    
    def get_common_questions(self, limit: int = 10) -> List[str]:
        """Get most common questions.
        
        Args:
            limit: Maximum number of questions to return
            
        Returns:
            List of question strings
        """
        try:
            queries = self.get_query_history(limit=1000)
            questions = [q["question"] for q in queries]
            
            # Count occurrences
            question_counter = Counter(questions)
            
            return [q for q, _ in question_counter.most_common(limit)]
        except Exception as e:
            logger.error(f"Error getting common questions: {e}")
            return []


# Global analytics tracker instance
analytics_tracker = AnalyticsTracker()

