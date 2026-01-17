"""Query suggestions and related questions generation."""

import re
from typing import List, Dict, Optional
from collections import Counter

from loguru import logger


class SuggestionGenerator:
    """Generate query suggestions based on documents and history."""
    
    @staticmethod
    def generate_suggestions_from_documents(documents: List[Dict]) -> List[str]:
        """Generate query suggestions based on uploaded documents.
        
        Args:
            documents: List of document metadata dictionaries
            
        Returns:
            List of suggested query strings
        """
        suggestions = []
        
        if not documents:
            suggestions.extend([
                "What documents do you have?",
                "Summarize the uploaded documents",
                "What topics are covered?",
            ])
            return suggestions
        
        # Extract common words from filenames
        filenames = [doc.get("filename", "") for doc in documents]
        words = []
        for filename in filenames:
            # Remove extensions and split by common separators
            name = filename.rsplit(".", 1)[0]
            words.extend(re.findall(r'\b[A-Z][a-z]+\b', name))  # Capitalized words
            words.extend(re.findall(r'\b[a-z]{4,}\b', name.lower()))  # Longer words
        
        if words:
            common_words = Counter(words).most_common(3)
            for word, _ in common_words:
                suggestions.append(f"Tell me about {word}")
        
        # Add generic suggestions based on document count
        suggestions.extend([
            "What is the main topic of the documents?",
            "Summarize the key points",
            "What are the important details?",
            "List all the topics covered",
        ])
        
        return suggestions[:8]  # Limit to 8 suggestions
    
    @staticmethod
    def generate_related_questions(question: str, context: Optional[str] = None) -> List[str]:
        """Generate related questions based on current question.
        
        Args:
            question: The current question
            context: Optional context from previous answer
            
        Returns:
            List of related question strings
        """
        question_lower = question.lower()
        related = []
        
        # Extract key terms from question
        key_terms = [w for w in re.findall(r'\b[a-z]{4,}\b', question_lower) if w not in ['what', 'when', 'where', 'which', 'whose', 'about', 'from', 'this', 'that', 'these', 'those']]
        
        if key_terms:
            main_term = key_terms[0] if key_terms else "it"
            related.extend([
                f"Can you provide more details about {main_term}?",
                f"What else is related to {main_term}?",
                f"How does {main_term} work?",
                f"Why is {main_term} important?",
            ])
        
        # Add common follow-up questions
        related.extend([
            "Can you explain this in more detail?",
            "What are the implications?",
            "Are there any examples?",
            "What should I know about this?",
        ])
        
        return related[:6]  # Limit to 6 related questions
    
    @staticmethod
    def get_query_templates() -> List[Dict[str, str]]:
        """Get query templates for common question types.
        
        Returns:
            List of template dictionaries with name and template
        """
        return [
            {
                "name": "Summarize",
                "template": "Summarize {topic}",
                "icon": "📝",
            },
            {
                "name": "Compare",
                "template": "Compare {topic1} and {topic2}",
                "icon": "⚖️",
            },
            {
                "name": "Explain",
                "template": "Explain {topic} in detail",
                "icon": "💡",
            },
            {
                "name": "List",
                "template": "List all {topic}",
                "icon": "📋",
            },
            {
                "name": "Find",
                "template": "Find all mentions of {topic}",
                "icon": "🔍",
            },
            {
                "name": "Define",
                "template": "What is {topic}?",
                "icon": "📖",
            },
        ]


# Global suggestion generator instance
suggestion_generator = SuggestionGenerator()

