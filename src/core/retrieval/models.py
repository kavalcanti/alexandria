"""
Data models for retrieval operations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class SearchQuery:
    """
    Represents a search query for document retrieval.
    """
    query_text: str
    max_results: int = 10
    document_ids: Optional[List[int]] = None
    distance_method: str = 'l2'
    content_types: Optional[List[str]] = None
    date_range: Optional[tuple[datetime, datetime]] = None


@dataclass  
class DocumentMatch:
    """
    Represents a matched document chunk with metadata.
    """
    chunk_id: int
    document_id: int
    content: str
    similarity_score: float
    chunk_index: int
    filename: str
    filepath: str
    content_type: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime


@dataclass
class SearchResult:
    """
    Represents the complete search result with matches and metadata.
    """
    query: str
    matches: List[DocumentMatch]
    total_matches: int
    search_time_ms: float
    embedding_time_ms: float
    
    @property
    def has_results(self) -> bool:
        """Check if search returned any results."""
        return len(self.matches) > 0
    
    @property
    def best_match(self) -> Optional[DocumentMatch]:
        """Get the highest scoring match."""
        return self.matches[0] if self.matches else None 