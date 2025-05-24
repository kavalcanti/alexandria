"""
High-level interface for document retrieval operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.logger import get_module_logger
from .retrieval_service import RetrievalService
from .models import SearchQuery, SearchResult, DocumentMatch

logger = get_module_logger(__name__)


class RetrievalInterface:
    """
    High-level interface for document retrieval with simplified methods.
    """
    
    def __init__(self, retrieval_service: Optional[RetrievalService] = None):
        """
        Initialize the retrieval interface.
        
        Args:
            retrieval_service: RetrievalService instance (creates new if None)
        """
        self.service = retrieval_service if retrieval_service else RetrievalService()
        logger.info("RetrievalInterface initialized")

    def search_documents(
        self, 
        query: str, 
        max_results: int = 10
    ) -> SearchResult:
        """
        Simple document search with text query.
        
        Args:
            query: Text to search for
            max_results: Maximum number of results to return
            
        Returns:
            SearchResult with matching documents
        """
        search_query = SearchQuery(
            query_text=query,
            max_results=max_results
        )
        
        logger.debug(f"Searching documents for: '{query[:50]}...'")
        return self.service.search(search_query)

    def search_in_documents(
        self, 
        query: str, 
        document_ids: List[int],
        max_results: int = 10
    ) -> SearchResult:
        """
        Search within specific documents only.
        
        Args:
            query: Text to search for
            document_ids: List of document IDs to search within
            max_results: Maximum number of results to return
            
        Returns:
            SearchResult with matching chunks from specified documents
        """
        search_query = SearchQuery(
            query_text=query,
            max_results=max_results,
            document_ids=document_ids
        )
        
        logger.debug(f"Searching in {len(document_ids)} documents for: '{query[:50]}...'")
        return self.service.search(search_query)

    def search_by_content_type(
        self, 
        query: str, 
        content_types: List[str],
        max_results: int = 10
    ) -> SearchResult:
        """
        Search documents of specific content types.
        
        Args:
            query: Text to search for
            content_types: List of content types (e.g., ['pdf', 'text', 'markdown'])
            max_results: Maximum number of results to return
            
        Returns:
            SearchResult with matching documents of specified types
        """
        search_query = SearchQuery(
            query_text=query,
            max_results=max_results,
            content_types=content_types
        )
        
        logger.debug(f"Searching {content_types} documents for: '{query[:50]}...'")
        return self.service.search(search_query)

    def search_recent_documents(
        self, 
        query: str, 
        days_back: int = 30,
        max_results: int = 10
    ) -> SearchResult:
        """
        Search documents created within the last N days.
        
        Args:
            query: Text to search for
            days_back: Number of days to look back
            max_results: Maximum number of results to return
            
        Returns:
            SearchResult with matching recent documents
        """
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        search_query = SearchQuery(
            query_text=query,
            max_results=max_results,
            date_range=(start_date, end_date)
        )
        
        logger.debug(f"Searching documents from last {days_back} days for: '{query[:50]}...'")
        return self.service.search(search_query)

    def get_document_content(self, document_id: int, max_chunks: Optional[int] = None) -> List[DocumentMatch]:
        """
        Get all content chunks for a specific document.
        
        Args:
            document_id: ID of the document
            max_chunks: Maximum number of chunks to return
            
        Returns:
            List of DocumentMatch objects with document content
        """
        logger.debug(f"Retrieving content for document {document_id}")
        return self.service.get_document_chunks(document_id, max_chunks)

    def find_related_content(
        self, 
        chunk_id: int, 
        max_results: int = 5
    ) -> List[DocumentMatch]:
        """
        Find content similar to a specific chunk.
        
        Args:
            chunk_id: ID of the reference chunk
            max_results: Maximum number of similar chunks to return
            
        Returns:
            List of similar DocumentMatch objects
        """
        logger.debug(f"Finding content related to chunk {chunk_id}")
        return self.service.find_similar_chunks(chunk_id, max_results)

    def get_best_matches(self, query: str, top_n: int = 3) -> List[DocumentMatch]:
        """
        Get the top N best matching chunks for a query.
        
        Args:
            query: Text to search for
            top_n: Number of top matches to return
            
        Returns:
            List of top DocumentMatch objects
        """
        result = self.search_documents(query, max_results=top_n)
        return result.matches

    def search_with_context(self, query: str, context_size: int = 1, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search and include surrounding chunks for context.
        
        Args:
            query: Text to search for
            context_size: Number of chunks before/after to include
            max_results: Maximum number of base results
            
        Returns:
            List of dictionaries with main chunk and context chunks
        """
        # Get initial matches
        result = self.search_documents(query, max_results=max_results)
        
        contextual_results = []
        for match in result.matches:
            # Get surrounding chunks
            all_chunks = self.get_document_content(match.document_id)
            
            # Find the position of our match
            match_idx = next((i for i, chunk in enumerate(all_chunks) if chunk.chunk_id == match.chunk_id), -1)
            
            if match_idx >= 0:
                # Get context chunks
                start_idx = max(0, match_idx - context_size)
                end_idx = min(len(all_chunks), match_idx + context_size + 1)
                
                context_chunks = all_chunks[start_idx:end_idx]
                
                contextual_result = {
                    'main_match': match,
                    'context_chunks': context_chunks,
                    'context_start_index': start_idx,
                    'total_chunks_in_document': len(all_chunks)
                }
                contextual_results.append(contextual_result)
        
        logger.debug(f"Retrieved {len(contextual_results)} results with context")
        return contextual_results 