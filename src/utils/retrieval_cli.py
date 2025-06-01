"""Command-line interface for document retrieval."""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from dotenv import load_dotenv

from src.logger import get_module_logger
from src.core.retrieval import RetrievalInterface, SearchQuery

load_dotenv()

logger = get_module_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Alexandria Document Retrieval Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic document search
  python -m src.utils.retrieval_cli search "machine learning algorithms"
  
  # Search with similarity threshold
  python -m src.utils.retrieval_cli search "neural networks" --min-similarity 0.7
  
  # Search in specific documents
  python -m src.utils.retrieval_cli search-docs "data analysis" --document-ids 1,2,3
  
  # Search by content type
  python -m src.utils.retrieval_cli search-type "python programming" --content-types pdf,text
  
  # Search recent documents
  python -m src.utils.retrieval_cli search-recent "database design" --days-back 7
  
  # Get document content
  python -m src.utils.retrieval_cli get-content 1
  
  # Find related content
  python -m src.utils.retrieval_cli find-related 123
  
  # Search with context
  python -m src.utils.retrieval_cli search-context "artificial intelligence" --context-size 2
  
  # Get retrieval statistics
  python -m src.utils.retrieval_cli stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Basic search command
    search_parser = subparsers.add_parser('search', help='Search documents with text query')
    search_parser.add_argument('query', type=str, help='Text to search for')
    add_search_args(search_parser)
    
    # Search in specific documents
    search_docs_parser = subparsers.add_parser('search-docs', help='Search within specific documents')
    search_docs_parser.add_argument('query', type=str, help='Text to search for')
    search_docs_parser.add_argument('--document-ids', type=str, required=True,
                                   help='Comma-separated list of document IDs')
    add_search_args(search_docs_parser)
    
    # Search by content type
    search_type_parser = subparsers.add_parser('search-type', help='Search documents by content type')
    search_type_parser.add_argument('query', type=str, help='Text to search for')
    search_type_parser.add_argument('--content-types', type=str, required=True,
                                   help='Comma-separated list of content types (e.g., pdf,text,markdown)')
    add_search_args(search_type_parser)
    
    # Search recent documents
    search_recent_parser = subparsers.add_parser('search-recent', help='Search recent documents')
    search_recent_parser.add_argument('query', type=str, help='Text to search for')
    search_recent_parser.add_argument('--days-back', type=int, default=30,
                                     help='Number of days to look back (default: 30)')
    add_search_args(search_recent_parser)
    
    # Get document content
    content_parser = subparsers.add_parser('get-content', help='Get all chunks from a document')
    content_parser.add_argument('document_id', type=int, help='Document ID')
    content_parser.add_argument('--max-chunks', type=int, help='Maximum number of chunks to return')
    add_output_args(content_parser)
    
    # Find related content
    related_parser = subparsers.add_parser('find-related', help='Find content similar to a chunk')
    related_parser.add_argument('chunk_id', type=int, help='Reference chunk ID')
    related_parser.add_argument('--max-results', type=int, default=5,
                               help='Maximum number of results (default: 5)')
    add_output_args(related_parser)
    
    # Search with context
    context_parser = subparsers.add_parser('search-context', help='Search with surrounding context')
    context_parser.add_argument('query', type=str, help='Text to search for')
    context_parser.add_argument('--context-size', type=int, default=1,
                               help='Number of chunks before/after to include (default: 1)')
    add_search_args(context_parser)
    
    # Best matches command
    best_parser = subparsers.add_parser('best-matches', help='Get top N best matches')
    best_parser.add_argument('query', type=str, help='Text to search for')
    best_parser.add_argument('--top-n', type=int, default=3,
                            help='Number of top matches to return (default: 3)')
    add_output_args(best_parser)
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show retrieval system statistics')
    
    # Test embedding command
    test_parser = subparsers.add_parser('test-embedding', help='Test embedding generation')
    test_parser.add_argument('text', type=str, help='Text to generate embedding for')
    
    return parser


def add_search_args(parser: argparse.ArgumentParser):
    """Add common search arguments to a parser."""
    parser.add_argument('--max-results', type=int, default=10,
                       help='Maximum number of results to return (default: 10)')
    add_output_args(parser)


def add_output_args(parser: argparse.ArgumentParser):
    """Add common output arguments to a parser."""
    parser.add_argument('--format', type=str, choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress non-essential output')


def parse_ids(ids_str: str) -> List[int]:
    """Parse comma-separated list of IDs."""
    try:
        return [int(id_str.strip()) for id_str in ids_str.split(',')]
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid ID list format: {ids_str}")


def parse_types(types_str: str) -> List[str]:
    """Parse comma-separated list of content types."""
    return [type_str.strip() for type_str in types_str.split(',')]


def format_results(results, format_type: str, verbose: bool = False) -> str:
    """Format results for output."""
    if format_type == 'json':
        if hasattr(results, '__dict__'):
            # Handle dataclass objects
            return json.dumps(results, default=str, indent=2)
        elif isinstance(results, list):
            # Handle list of objects
            return json.dumps([
                {**item.__dict__} if hasattr(item, '__dict__') else item 
                for item in results
            ], default=str, indent=2)
        else:
            return json.dumps(results, default=str, indent=2)
    
    # Text format
    if hasattr(results, 'matches'):
        # SearchResult object
        output = []
        output.append(f"Found {results.total_matches} matches in {results.search_time_ms:.2f}ms")
        if verbose:
            output.append(f"Embedding generation: {results.embedding_time_ms:.2f}ms")
        output.append("")
        
        for i, match in enumerate(results.matches, 1):
            output.append(f"{i}. [{match.filename}] Score: {match.similarity_score:.3f}")
            if verbose:
                output.append(f"   Document ID: {match.document_id}, Chunk: {match.chunk_index}")
                output.append(f"   Created: {match.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Limit content preview
            content_preview = match.content[:200] + "..." if len(match.content) > 200 else match.content
            output.append(f"   Content: {content_preview}")
            output.append("")
        
        return "\n".join(output)
    
    elif isinstance(results, list):
        # List of DocumentMatch objects
        output = []
        output.append(f"Found {len(results)} items")
        output.append("")
        
        for i, item in enumerate(results, 1):
            if hasattr(item, 'filename'):
                # DocumentMatch
                output.append(f"{i}. [{item.filename}] Score: {item.similarity_score:.3f}")
                if verbose:
                    output.append(f"   Document ID: {item.document_id}, Chunk: {item.chunk_index}")
                content_preview = item.content[:200] + "..." if len(item.content) > 200 else item.content
                output.append(f"   Content: {content_preview}")
                output.append("")
            else:
                # Handle other types
                output.append(f"{i}. {str(item)}")
        
        return "\n".join(output)
    
    else:
        return str(results)


def handle_search(args) -> int:
    """Handle the basic search command."""
    try:
        retrieval = RetrievalInterface()
        
        if not args.quiet:
            print(f"Searching for: '{args.query}'")
            print(f"Max results: {args.max_results}")
            print()
        
        result = retrieval.search_documents(
            query=args.query,
            max_results=args.max_results
        )
        
        print(format_results(result, args.format, args.verbose))
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in search: {str(e)}")
        return 1


def handle_search_docs(args) -> int:
    """Handle the search-docs command."""
    try:
        retrieval = RetrievalInterface()
        document_ids = parse_ids(args.document_ids)
        
        if not args.quiet:
            print(f"Searching in documents {document_ids} for: '{args.query}'")
            print()
        
        result = retrieval.search_in_documents(
            query=args.query,
            document_ids=document_ids,
            max_results=args.max_results
        )
        
        print(format_results(result, args.format, args.verbose))
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in search-docs: {str(e)}")
        return 1


def handle_search_type(args) -> int:
    """Handle the search-type command."""
    try:
        retrieval = RetrievalInterface()
        content_types = parse_types(args.content_types)
        
        if not args.quiet:
            print(f"Searching {content_types} documents for: '{args.query}'")
            print()
        
        result = retrieval.search_by_content_type(
            query=args.query,
            content_types=content_types,
            max_results=args.max_results
        )
        
        print(format_results(result, args.format, args.verbose))
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in search-type: {str(e)}")
        return 1


def handle_search_recent(args) -> int:
    """Handle the search-recent command."""
    try:
        retrieval = RetrievalInterface()
        
        if not args.quiet:
            print(f"Searching documents from last {args.days_back} days for: '{args.query}'")
            print()
        
        result = retrieval.search_recent_documents(
            query=args.query,
            days_back=args.days_back,
            max_results=args.max_results
        )
        
        print(format_results(result, args.format, args.verbose))
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in search-recent: {str(e)}")
        return 1


def handle_get_content(args) -> int:
    """Handle the get-content command."""
    try:
        retrieval = RetrievalInterface()
        
        if not args.quiet:
            print(f"Retrieving content for document {args.document_id}")
            if args.max_chunks:
                print(f"Max chunks: {args.max_chunks}")
            print()
        
        chunks = retrieval.get_document_content(
            document_id=args.document_id,
            max_chunks=args.max_chunks
        )
        
        print(format_results(chunks, args.format, args.verbose))
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in get-content: {str(e)}")
        return 1


def handle_find_related(args) -> int:
    """Handle the find-related command."""
    try:
        retrieval = RetrievalInterface()
        
        if not args.quiet:
            print(f"Finding content related to chunk {args.chunk_id}")
            print(f"Max results: {args.max_results}")
            print()
        
        related = retrieval.find_related_content(
            chunk_id=args.chunk_id,
            max_results=args.max_results
        )
        
        print(format_results(related, args.format, args.verbose))
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in find-related: {str(e)}")
        return 1


def handle_search_context(args) -> int:
    """Handle the search-context command."""
    try:
        retrieval = RetrievalInterface()
        
        if not args.quiet:
            print(f"Searching with context for: '{args.query}'")
            print(f"Context size: {args.context_size} chunks")
            print()
        
        contextual_results = retrieval.search_with_context(
            query=args.query,
            context_size=args.context_size,
            max_results=args.max_results
        )
        
        if args.format == 'json':
            print(json.dumps(contextual_results, default=str, indent=2))
        else:
            print(f"Found {len(contextual_results)} results with context:")
            print()
            
            for i, result in enumerate(contextual_results, 1):
                main_match = result['main_match']
                context_chunks = result['context_chunks']
                
                print(f"{i}. [{main_match.filename}] Score: {main_match.similarity_score:.3f}")
                print(f"   Main match (chunk {main_match.chunk_index}):")
                content_preview = main_match.content[:150] + "..." if len(main_match.content) > 150 else main_match.content
                print(f"   {content_preview}")
                
                if args.verbose:
                    print(f"   Context ({len(context_chunks)} chunks):")
                    for j, chunk in enumerate(context_chunks):
                        marker = ">>> " if chunk.chunk_id == main_match.chunk_id else "    "
                        chunk_preview = chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
                        print(f"   {marker}[{j+1}] {chunk_preview}")
                else:
                    print(f"   Context: {len(context_chunks)} surrounding chunks")
                
                print()
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in search-context: {str(e)}")
        return 1


def handle_best_matches(args) -> int:
    """Handle the best-matches command."""
    try:
        retrieval = RetrievalInterface()
        
        if not args.quiet:
            print(f"Getting top {args.top_n} matches for: '{args.query}'")
            print()
        
        matches = retrieval.get_best_matches(
            query=args.query,
            top_n=args.top_n
        )
        
        print(format_results(matches, args.format, args.verbose))
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in best-matches: {str(e)}")
        return 1


def handle_stats(args) -> int:
    """Handle the stats command."""
    try:
        from src.infrastructure.db_connector import DatabaseStorage
        
        db_storage = DatabaseStorage()
        
        with db_storage.get_connection() as conn:
            # Get document statistics
            doc_stats = conn.execute("SELECT COUNT(*) as total_docs FROM documents").fetchone()
            chunk_stats = conn.execute("SELECT COUNT(*) as total_chunks FROM document_chunks").fetchone()
            embedded_chunks = conn.execute("SELECT COUNT(*) as embedded_chunks FROM document_chunks WHERE embedding IS NOT NULL").fetchone()
            
            # Get content type distribution
            content_types = conn.execute("""
                SELECT content_type, COUNT(*) as count 
                FROM documents 
                GROUP BY content_type 
                ORDER BY count DESC
            """).fetchall()
            
            # Get recent activity
            recent_docs = conn.execute("""
                SELECT COUNT(*) as recent_count 
                FROM documents 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """).fetchone()
        
        print("Retrieval System Statistics:")
        print(f"  Total documents: {doc_stats.total_docs}")
        print(f"  Total chunks: {chunk_stats.total_chunks}")
        print(f"  Embedded chunks: {embedded_chunks.embedded_chunks}")
        print(f"  Recent documents (7 days): {recent_docs.recent_count}")
        print()
        
        print("Documents by content type:")
        for row in content_types:
            print(f"  {row.content_type or 'unknown'}: {row.count}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in stats: {str(e)}")
        return 1


def handle_test_embedding(args) -> int:
    """Handle the test-embedding command."""
    try:
        from src.infrastructure.embedder import Embedder
        import time
        
        embedder = Embedder()
        
        print(f"Generating embedding for: '{args.text}'")
        
        start_time = time.time()
        embedding = embedder.embed(args.text)
        end_time = time.time()
        
        print(f"Embedding generated in {(end_time - start_time) * 1000:.2f}ms")
        print(f"Embedding dimensions: {len(embedding)}")
        print(f"Embedding type: {type(embedding)}")
        print(f"First 10 values: {embedding[:10].tolist()}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in test-embedding: {str(e)}")
        return 1


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Configure logging based on verbosity using environment variables
    if hasattr(args, 'verbose') and args.verbose:
        import os
        os.environ['MODULE_LOG_LEVEL'] = 'DEBUG'
        os.environ['LOG_LEVEL'] = 'DEBUG'
    elif hasattr(args, 'quiet') and args.quiet:
        import os
        os.environ['MODULE_LOG_LEVEL'] = 'ERROR'
        os.environ['LOG_LEVEL'] = 'ERROR'
    
    # Dispatch to appropriate handler
    if args.command == 'search':
        return handle_search(args)
    elif args.command == 'search-docs':
        return handle_search_docs(args)
    elif args.command == 'search-type':
        return handle_search_type(args)
    elif args.command == 'search-recent':
        return handle_search_recent(args)
    elif args.command == 'get-content':
        return handle_get_content(args)
    elif args.command == 'find-related':
        return handle_find_related(args)
    elif args.command == 'search-context':
        return handle_search_context(args)
    elif args.command == 'best-matches':
        return handle_best_matches(args)
    elif args.command == 'stats':
        return handle_stats(args)
    elif args.command == 'test-embedding':
        return handle_test_embedding(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main()) 