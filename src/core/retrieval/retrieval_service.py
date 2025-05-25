"""
Core retrieval service for document similarity search.
"""

import time
from typing import List, Optional
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.engine import Connection

from src.infrastructure.db_connector import DatabaseStorage
from src.infrastructure.db.db_models import documents_table, document_chunks_table
from src.infrastructure.embedder import Embedder
from src.logger import get_module_logger
from .models import SearchQuery, SearchResult, DocumentMatch

logger = get_module_logger(__name__)


class RetrievalService:
    """
    Service for retrieving relevant document chunks using vector similarity search.
    """
    
    def __init__(self, db_storage: Optional[DatabaseStorage] = None, embedder: Optional[Embedder] = None):
        """
        Initialize the retrieval service.
        
        Args:
            db_storage: Database storage instance (creates new if None)
            embedder: Embedder instance (creates new if None)
        """
        self.db_storage = db_storage if db_storage else DatabaseStorage()
        self.embedder = embedder if embedder else Embedder()
        logger.info("RetrievalService initialized")

    def search(self, query: SearchQuery) -> SearchResult:
        """
        Search for relevant document chunks using vector similarity.
        
        Args:
            query: Search query parameters
            
        Returns:
            SearchResult with matched documents and metadata
        """
        start_time = time.time()
        
        # Generate embedding for query
        embedding_start = time.time()
        query_embedding = self.embedder.embed(query.query_text)
        embedding_time_ms = (time.time() - embedding_start) * 1000
        
        logger.debug(f"Generated embedding for query: '{query.query_text[:50]}...'")
        
        # Perform similarity search
        with self.db_storage.get_connection() as conn:
            matches = self._similarity_search(conn, query, query_embedding)
        
        total_time_ms = (time.time() - start_time) * 1000
        
        result = SearchResult(
            query=query.query_text,
            matches=matches,
            total_matches=len(matches),
            search_time_ms=total_time_ms,
            embedding_time_ms=embedding_time_ms
        )
        
        logger.info(f"Search completed: {len(matches)} matches in {total_time_ms:.2f}ms")
        return result

    def _similarity_search(self, conn: Connection, query: SearchQuery, query_embedding) -> List[DocumentMatch]:
        """
        Perform vector similarity search in the database using SQLAlchemy core.
        
        Args:
            conn: Database connection
            query: Search query parameters
            query_embedding: Query text embedding vector
            
        Returns:
            List of DocumentMatch objects ordered by similarity
        """
        # Create aliases for tables
        dc = document_chunks_table.alias('dc')
        d = documents_table.alias('d')
        
        # Calculate distance using selected distance method
        if query.distance_method == 'l2':
            distance = dc.c.embedding.l2_distance(query_embedding).label('distance')
        elif query.distance_method == 'cosine':
            distance = dc.c.embedding.cosine_distance(query_embedding).label('distance')
        else:
            raise ValueError(f"Invalid distance method: {query.distance_method}")

        # Convert distance to similarity score (higher = more similar)
        similarity_score = (1.0 / (1.0 + distance)).label('similarity_score')
        
        # Build base query with join
        base_query = select(
            dc.c.id.label('chunk_id'),
            dc.c.document_id,
            dc.c.content,
            dc.c.chunk_index,
            dc.c.metadata.label('chunk_metadata'),
            dc.c.created_at,
            d.c.filename,
            d.c.filepath,
            d.c.content_type,
            distance,
            similarity_score
        ).select_from(
            dc.join(d, dc.c.document_id == d.c.id)
        ).where(
            dc.c.embedding.isnot(None)
        )
        
        # Add document ID filter
        if query.document_ids:
            base_query = base_query.where(dc.c.document_id.in_(query.document_ids))
        
        # Add content type filter
        if query.content_types:
            base_query = base_query.where(d.c.content_type.in_(query.content_types))
        
        # Add date range filter
        if query.date_range:
            start_date, end_date = query.date_range
            base_query = base_query.where(and_(
                d.c.created_at >= start_date,
                d.c.created_at <= end_date
            ))
        
        # Order by distance (ascending - smaller distance = more similar) and limit
        final_query = base_query.order_by(distance).limit(query.max_results)
        
        logger.debug(f"Executing similarity search with L2 distance")
        
        # Execute query
        result = conn.execute(final_query)
        rows = result.fetchall()
        
        # Convert to DocumentMatch objects
        matches = []
        for row in rows:
            match = DocumentMatch(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                content=row.content,
                similarity_score=float(row.similarity_score),
                chunk_index=row.chunk_index,
                filename=row.filename,
                filepath=row.filepath,
                content_type=row.content_type,
                metadata=row.chunk_metadata,
                created_at=row.created_at
            )
            matches.append(match)
        
        return matches

    def get_document_chunks(self, document_id: int, limit: Optional[int] = None) -> List[DocumentMatch]:
        """
        Get all chunks for a specific document using SQLAlchemy core.
        
        Args:
            document_id: ID of the document
            limit: Maximum number of chunks to return
            
        Returns:
            List of DocumentMatch objects for the document
        """
        with self.db_storage.get_connection() as conn:
            # Create aliases for tables
            dc = document_chunks_table.alias('dc')
            d = documents_table.alias('d')
            
            # Build query
            query = select(
                dc.c.id.label('chunk_id'),
                dc.c.document_id,
                dc.c.content,
                dc.c.chunk_index,
                dc.c.metadata.label('chunk_metadata'),
                dc.c.created_at,
                d.c.filename,
                d.c.filepath,
                d.c.content_type,
                func.cast(0.0, func.Float).label('similarity_score')
            ).select_from(
                dc.join(d, dc.c.document_id == d.c.id)
            ).where(
                dc.c.document_id == document_id
            ).order_by(dc.c.chunk_index)
            
            if limit:
                query = query.limit(limit)
            
            result = conn.execute(query)
            rows = result.fetchall()
            
            matches = []
            for row in rows:
                match = DocumentMatch(
                    chunk_id=row.chunk_id,
                    document_id=row.document_id,
                    content=row.content,
                    similarity_score=0.0,  # No similarity calculated for direct retrieval
                    chunk_index=row.chunk_index,
                    filename=row.filename,
                    filepath=row.filepath,
                    content_type=row.content_type,
                    metadata=row.chunk_metadata,
                    created_at=row.created_at
                )
                matches.append(match)
            
            logger.info(f"Retrieved {len(matches)} chunks for document {document_id}")
            return matches

    def find_similar_chunks(self, chunk_id: int, max_results: int = 5) -> List[DocumentMatch]:
        """
        Find chunks similar to a specific chunk using SQLAlchemy core.
        
        Args:
            chunk_id: ID of the reference chunk
            max_results: Maximum number of similar chunks to return
            
        Returns:
            List of similar DocumentMatch objects
        """
        with self.db_storage.get_connection() as conn:
            # First get the embedding of the reference chunk
            ref_query = select(document_chunks_table.c.embedding).where(
                document_chunks_table.c.id == chunk_id
            )
            ref_result = conn.execute(ref_query)
            ref_row = ref_result.fetchone()
            
            if not ref_row or not ref_row.embedding:
                logger.warning(f"No embedding found for chunk {chunk_id}")
                return []
            
            ref_embedding = ref_row.embedding
            
            # Create a pseudo query for similarity search
            pseudo_query = SearchQuery(
                query_text="",  # Empty since we're using direct embedding
                max_results=max_results + 1  # +1 to exclude the reference chunk
            )
            
            matches = self._similarity_search(conn, pseudo_query, ref_embedding)
            
            # Filter out the reference chunk itself
            similar_matches = [match for match in matches if match.chunk_id != chunk_id]
            
            # Return only the requested number of results
            return similar_matches[:max_results] 