"""
Retrieval module for document search and similarity matching.
"""

from .retrieval_service import RetrievalService
from .retrieval_interface import RetrievalInterface
from .models import SearchQuery, SearchResult, DocumentMatch

__all__ = [
    'RetrievalService',
    'RetrievalInterface', 
    'SearchQuery',
    'SearchResult',
    'DocumentMatch'
] 