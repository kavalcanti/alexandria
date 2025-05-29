from typing import List, Dict, Any, Optional
from src.configs import RAGToolsConfig
from src.core.context.context_window import ContextWindow
from src.core.retrieval.retrieval_interface import RetrievalInterface
from src.core.retrieval.models import SearchResult
from src.logger import get_module_logger

logger = get_module_logger(__name__)

class RAGTools:
    def __init__(self, context_window: ContextWindow, retrieval_interface: RetrievalInterface, config: RAGToolsConfig):
        self.context_window = context_window
        self.retrieval_interface = retrieval_interface
        self.config = config

    def perform_retrieval(self, query: str) -> Optional[SearchResult]:
        """
        Perform document retrieval for the given query.
        
        Args:
            query: Search query
            
        Returns:
            SearchResult or None if no relevant documents found
        """
        try:
            # Perform retrieval search
            result = self.retrieval_interface.search_documents(
                query=query,
                max_results=self.config.max_retrieval_results
            )

            logger.info(f"Retrieval result: {result}")
            
            # Filter by minimum similarity score
            if result.matches:
                filtered_matches = [
                    match for match in result.matches 
                    if match.similarity_score >= self.config.min_similarity_score
                ]
                result.matches = filtered_matches
                result.total_matches = len(filtered_matches)
            
            logger.debug(f"Retrieved {len(result.matches)} relevant documents for query: '{query[:50]}...'")
            return result if result.matches else None
            
        except Exception as e:
            logger.error(f"Retrieval failed for query '{query[:50]}...': {str(e)}")
            return None

    def _format_retrieval_context(self, retrieval_result: SearchResult) -> str:
        """
        Format retrieval results into a clean context string.
        """
        context_parts = []
        
        for i, match in enumerate(retrieval_result.matches[:self.config.max_retrieval_results]):
            source_info = ""
            if self.config.include_source_metadata:
                source_info = f" (Source: {match.filepath})"
            
            context_parts.append(f"[{i+1}] {match.content.strip()}{source_info}")
        
        return "\n\n".join(context_parts)

    def augment_query_with_context(self, query: str, retrieval_result: SearchResult) -> str:
        """
        Augment the user query with retrieved context.
        
        Args:
            query: Original user query
            retrieval_result: Results from document retrieval
            
        Returns:
            Augmented query with context
        """
        if not retrieval_result.matches:
            return query
        
        # Build context from retrieved documents
        context_text = self._format_retrieval_context(retrieval_result)
        
        # Create augmented prompt
        augmented_query = f"""{query}

Based on the following relevant information from the knowledge base:

{context_text}

Please provide a comprehensive answer using this context where relevant."""
        
        logger.debug(f"Augmented query with {len(retrieval_result.matches)} context documents")
        return augmented_query

    def search_documents(self, query: str, **kwargs) -> SearchResult:
        """
        Direct document search interface.
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            SearchResult with matching documents
        """
        return self.retrieval_interface.search_documents(query, **kwargs)

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the retrieval system.
        
        Returns:
            Dictionary with retrieval statistics
        """
        # This could be expanded to include more detailed stats
        return {
            "config": {
                "enable_retrieval": self.config.enable_retrieval,
                "max_results": self.config.max_retrieval_results,
                "min_similarity": self.config.min_similarity_score,
                "context_size": self.config.context_size,
                "include_metadata": self.config.include_source_metadata
            }
        } 