"""Analytics engine for tracking search queries and performance."""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from .database import Base

logger = logging.getLogger(__name__)


class QueryLog(Base):
    """Log of all user queries"""
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_id = Column(String(255), index=True)
    
    # Query details
    query_text = Column(Text, nullable=False)
    query_hash = Column(String(64), index=True)  # For deduplication
    language = Column(String(10))  # en, pl, etc.
    
    # Search details
    search_mode = Column(String(50))  # hybrid, semantic, keyword
    top_k = Column(Integer)
    
    # Results
    answer_length = Column(Integer)
    sources_count = Column(Integer)
    sources_data = Column(JSON)
    
    # Performance
    response_time_ms = Column(Float)
    embedding_time_ms = Column(Float)
    search_time_ms = Column(Float)
    llm_time_ms = Column(Float)
    
    # User feedback
    user_rating = Column(Integer, default=0)  # -1 (thumbs down), 0 (none), 1 (thumbs up)
    feedback_text = Column(Text)
    
    # Metadata
    has_results = Column(Integer, default=1)  # 1 if found results, 0 if not
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Classification
    query_type = Column(String(50))  # question, command, statement
    query_intent = Column(String(50))  # search, summarize, compare, etc.


class SearchPattern(Base):
    """Aggregated search patterns"""
    __tablename__ = "search_patterns"
    
    id = Column(Integer, primary_key=True)
    pattern = Column(String(255), unique=True, index=True)
    frequency = Column(Integer, default=1)
    last_seen = Column(DateTime, default=datetime.utcnow)
    avg_response_time = Column(Float)
    avg_sources = Column(Float)
    avg_rating = Column(Float)


class FailedQuery(Base):
    """Queries that returned no results"""
    __tablename__ = "failed_queries"
    
    id = Column(Integer, primary_key=True)
    query_text = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    reason = Column(String(255))  # no_documents, no_match, error


class AnalyticsEngine:
    """Analytics engine for search insights"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_query(
        self,
        user_id: int,
        session_id: str,
        query_text: str,
        search_mode: str,
        answer: str,
        sources: List[Dict],
        performance_metrics: Dict[str, float],
        top_k: int = 5
    ) -> QueryLog:
        """Log a query with all metadata"""
        
        import hashlib
        query_hash = hashlib.md5(query_text.encode()).hexdigest()
        
        # Detect language
        language = self._detect_language(query_text)
        
        # Classify query
        query_type, query_intent = self._classify_query(query_text)
        
        log_entry = QueryLog(
            user_id=user_id,
            session_id=session_id,
            query_text=query_text,
            query_hash=query_hash,
            language=language,
            search_mode=search_mode,
            top_k=top_k,
            answer_length=len(answer),
            sources_count=len(sources),
            sources_data=sources,
            response_time_ms=performance_metrics.get('total', 0),
            embedding_time_ms=performance_metrics.get('embedding', 0),
            search_time_ms=performance_metrics.get('search', 0),
            llm_time_ms=performance_metrics.get('llm', 0),
            has_results=1 if sources else 0,
            query_type=query_type,
            query_intent=query_intent
        )
        
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        
        # Update patterns
        self._update_search_patterns(query_text, performance_metrics, sources)
        
        # Track failed query if no results
        if not sources:
            self._track_failed_query(user_id, query_text, "no_match")
        
        return log_entry
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        # Polish characters
        polish_chars = set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')
        if any(char in polish_chars for char in text):
            return 'pl'
        return 'en'
    
    def _classify_query(self, text: str) -> tuple:
        """Classify query type and intent"""
        text_lower = text.lower()
        
        # Query type
        if '?' in text:
            query_type = 'question'
        elif any(cmd in text_lower for cmd in ['show', 'list', 'find', 'get']):
            query_type = 'command'
        else:
            query_type = 'statement'
        
        # Intent
        if any(word in text_lower for word in ['what', 'who', 'where', 'when', 'why', 'how']):
            intent = 'search'
        elif any(word in text_lower for word in ['summarize', 'summary', 'tldr']):
            intent = 'summarize'
        elif any(word in text_lower for word in ['compare', 'difference', 'vs']):
            intent = 'compare'
        elif any(word in text_lower for word in ['explain', 'describe']):
            intent = 'explain'
        elif any(word in text_lower for word in ['list', 'all', 'every']):
            intent = 'list'
        else:
            intent = 'general'
        
        return query_type, intent
    
    def _update_search_patterns(
        self,
        query: str,
        performance: Dict,
        sources: List
    ):
        """Update aggregated search patterns"""
        # Extract key terms (simple approach)
        terms = query.lower().split()
        key_terms = [t for t in terms if len(t) > 3][:3]  # Top 3 meaningful words
        
        if not key_terms:
            return
        
        pattern = ' '.join(sorted(key_terms))
        
        # Get or create pattern
        existing = self.db.query(SearchPattern).filter(
            SearchPattern.pattern == pattern
        ).first()
        
        if existing:
            existing.frequency += 1
            existing.last_seen = datetime.utcnow()
            # Update averages
            n = existing.frequency
            existing.avg_response_time = (
                (existing.avg_response_time * (n-1) + performance.get('total', 0)) / n
            )
            existing.avg_sources = (
                (existing.avg_sources * (n-1) + len(sources)) / n
            )
        else:
            new_pattern = SearchPattern(
                pattern=pattern,
                frequency=1,
                avg_response_time=performance.get('total', 0),
                avg_sources=len(sources),
                avg_rating=0.0
            )
            self.db.add(new_pattern)
        
        self.db.commit()
    
    def _track_failed_query(self, user_id: int, query: str, reason: str):
        """Track queries that returned no results"""
        failed = FailedQuery(
            user_id=user_id,
            query_text=query,
            reason=reason
        )
        self.db.add(failed)
        self.db.commit()
    
    def record_feedback(self, query_id: int, rating: int, feedback_text: str = None):
        """Record user feedback on query result"""
        log = self.db.query(QueryLog).filter(QueryLog.id == query_id).first()
        
        if log:
            log.user_rating = rating
            log.feedback_text = feedback_text
            self.db.commit()
            
            logger.info(f"Feedback recorded for query {query_id}: {rating}")
            return True
        
        return False
    
    # Analytics queries
    
    def get_popular_queries(self, limit: int = 10, days: int = 7) -> List[Dict]:
        """Get most popular queries"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        results = self.db.query(
            QueryLog.query_text,
            QueryLog.query_hash,
            func.count(QueryLog.id).label('count'),
            func.avg(QueryLog.user_rating).label('avg_rating')
        ).filter(
            QueryLog.timestamp >= cutoff
        ).group_by(
            QueryLog.query_hash,
            QueryLog.query_text
        ).order_by(
            func.count(QueryLog.id).desc()
        ).limit(limit).all()
        
        return [
            {
                'query': r.query_text,
                'count': r.count,
                'avg_rating': round(float(r.avg_rating or 0), 2)
            }
            for r in results
        ]
    
    def get_failed_queries(self, limit: int = 20) -> List[Dict]:
        """Get queries that returned no results"""
        results = self.db.query(
            FailedQuery.query_text,
            func.count(FailedQuery.id).label('count')
        ).group_by(
            FailedQuery.query_text
        ).order_by(
            func.count(FailedQuery.id).desc()
        ).limit(limit).all()
        
        return [
            {'query': r.query_text, 'count': r.count}
            for r in results
        ]
    
    def get_performance_stats(self, days: int = 7) -> Dict:
        """Get performance statistics"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        stats = self.db.query(
            func.avg(QueryLog.response_time_ms).label('avg_time'),
            func.min(QueryLog.response_time_ms).label('min_time'),
            func.max(QueryLog.response_time_ms).label('max_time'),
            func.avg(QueryLog.sources_count).label('avg_sources'),
            func.count(QueryLog.id).label('total_queries')
        ).filter(
            QueryLog.timestamp >= cutoff
        ).first()
        
        return {
            'avg_response_time_ms': round(float(stats.avg_time or 0), 2),
            'min_response_time_ms': round(float(stats.min_time or 0), 2),
            'max_response_time_ms': round(float(stats.max_time or 0), 2),
            'avg_sources': round(float(stats.avg_sources or 0), 2),
            'total_queries': stats.total_queries or 0
        }
    
    def get_user_satisfaction(self, days: int = 7) -> Dict:
        """Calculate user satisfaction metrics"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        ratings = self.db.query(QueryLog.user_rating).filter(
            QueryLog.timestamp >= cutoff,
            QueryLog.user_rating != 0
        ).all()
        
        if not ratings:
            return {
                'satisfaction_score': 0,
                'thumbs_up': 0,
                'thumbs_down': 0,
                'total_rated': 0
            }
        
        ratings_list = [r.user_rating for r in ratings]
        thumbs_up = sum(1 for r in ratings_list if r == 1)
        thumbs_down = sum(1 for r in ratings_list if r == -1)
        
        # Satisfaction score (0-100)
        total_rated = thumbs_up + thumbs_down
        score = (thumbs_up / total_rated * 100) if total_rated > 0 else 0
        
        return {
            'satisfaction_score': round(score, 1),
            'thumbs_up': thumbs_up,
            'thumbs_down': thumbs_down,
            'total_rated': total_rated
        }
    
    def get_query_trends(self, days: int = 30) -> List[Dict]:
        """Get query volume trends over time"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Group by day
        results = self.db.query(
            func.date(QueryLog.timestamp).label('date'),
            func.count(QueryLog.id).label('count')
        ).filter(
            QueryLog.timestamp >= cutoff
        ).group_by(
            func.date(QueryLog.timestamp)
        ).order_by(
            func.date(QueryLog.timestamp)
        ).all()
        
        return [
            {'date': str(r.date), 'count': r.count}
            for r in results
        ]
    
    def get_search_mode_distribution(self, days: int = 7) -> Dict:
        """Get distribution of search modes used"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        results = self.db.query(
            QueryLog.search_mode,
            func.count(QueryLog.id).label('count')
        ).filter(
            QueryLog.timestamp >= cutoff
        ).group_by(
            QueryLog.search_mode
        ).all()
        
        total = sum(r.count for r in results)
        
        return {
            r.search_mode: {
                'count': r.count,
                'percentage': round(r.count / total * 100, 1) if total > 0 else 0
            }
            for r in results
        }
    
    def get_query_intent_distribution(self, days: int = 7) -> Dict:
        """Get distribution of query intents"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        results = self.db.query(
            QueryLog.query_intent,
            func.count(QueryLog.id).label('count')
        ).filter(
            QueryLog.timestamp >= cutoff
        ).group_by(
            QueryLog.query_intent
        ).all()
        
        return {
            r.query_intent: r.count
            for r in results
        }
    
    def get_language_distribution(self, days: int = 7) -> Dict:
        """Get language distribution of queries"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        results = self.db.query(
            QueryLog.language,
            func.count(QueryLog.id).label('count')
        ).filter(
            QueryLog.timestamp >= cutoff
        ).group_by(
            QueryLog.language
        ).all()
        
        return {
            r.language: r.count
            for r in results
        }
    
    def generate_insights(self) -> List[str]:
        """Generate actionable insights from analytics"""
        insights = []
        
        # Check for common failed queries
        failed = self.get_failed_queries(limit=5)
        if failed:
            insights.append(
                f"⚠️ {len(failed)} common queries return no results. "
                f"Consider adding more documents on: {', '.join([f['query'][:30] for f in failed[:3]])}"
            )
        
        # Check performance
        perf = self.get_performance_stats(days=7)
        if perf['avg_response_time_ms'] > 5000:
            insights.append(
                f"🐌 Average response time is {perf['avg_response_time_ms']/1000:.1f}s. "
                "Consider optimizing search or adding caching."
            )
        
        # Check satisfaction
        satisfaction = self.get_user_satisfaction(days=7)
        if satisfaction['satisfaction_score'] < 70 and satisfaction['total_rated'] > 0:
            insights.append(
                f"😐 User satisfaction is {satisfaction['satisfaction_score']}%. "
                "Review low-rated queries to improve results."
            )
        elif satisfaction['satisfaction_score'] > 90 and satisfaction['total_rated'] > 0:
            insights.append(
                f"🎉 Excellent! User satisfaction is {satisfaction['satisfaction_score']}%"
            )
        
        # Check search mode usage
        modes = self.get_search_mode_distribution(days=7)
        if 'hybrid' in modes and modes['hybrid']['percentage'] < 50:
            insights.append(
                "💡 Consider promoting hybrid search mode for better results"
            )
        
        return insights

