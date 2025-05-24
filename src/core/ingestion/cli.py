"""Command-line interface for document ingestion."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from src.logger import get_module_logger
from src.core.ingestion.document_ingestor import DocumentIngestor, IngestionConfig
from src.core.ingestion.text_chunker import ChunkConfig, ChunkStrategy

load_dotenv()

logger = get_module_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Alexandria Document Ingestion Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a single file
  python -m src.core.ingestion.cli ingest-file /path/to/document.pdf
  
  # Ingest all files in a directory
  python -m src.core.ingestion.cli ingest-dir /path/to/documents
  
  # Ingest with custom chunk size
  python -m src.core.ingestion.cli ingest-dir /path/to/docs --chunk-size 1500
  
  # Show ingestion statistics
  python -m src.core.ingestion.cli stats
  
  # List supported file types
  python -m src.core.ingestion.cli supported-types
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ingest file command
    file_parser = subparsers.add_parser('ingest-file', help='Ingest a single file')
    file_parser.add_argument('file_path', type=str, help='Path to the file to ingest')
    add_common_args(file_parser)
    
    # Ingest directory command
    dir_parser = subparsers.add_parser('ingest-dir', help='Ingest all files in a directory')
    dir_parser.add_argument('directory_path', type=str, help='Path to the directory to ingest')
    dir_parser.add_argument('--recursive', action='store_true', default=True, 
                           help='Recursively search subdirectories (default: True)')
    dir_parser.add_argument('--no-recursive', action='store_false', dest='recursive',
                           help='Do not search subdirectories recursively')
    add_common_args(dir_parser)
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show ingestion statistics')
    
    # Supported types command
    types_parser = subparsers.add_parser('supported-types', help='List supported file types')
    
    # Delete document command
    delete_parser = subparsers.add_parser('delete', help='Delete a document by file hash')
    delete_parser.add_argument('file_hash', type=str, help='SHA-256 hash of the file to delete')
    
    return parser


def add_common_args(parser: argparse.ArgumentParser):
    """Add common arguments to a parser."""
    # Chunking options
    parser.add_argument('--chunk-strategy', type=str, 
                       choices=['fixed_size', 'sentence_based', 'paragraph_based', 'code_based', 'markdown_based'],
                       default='sentence_based',
                       help='Text chunking strategy (default: sentence_based)')
    parser.add_argument('--chunk-size', type=int, default=1000,
                       help='Maximum chunk size in characters (default: 1000)')
    parser.add_argument('--min-chunk-size', type=int, default=100,
                       help='Minimum chunk size in characters (default: 100)')
    parser.add_argument('--overlap-size', type=int, default=100,
                       help='Overlap size between chunks in characters (default: 100)')
    
    # Processing options
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Number of files to process in each batch (default: 50)')
    parser.add_argument('--max-workers', type=int, default=4,
                       help='Maximum number of worker threads (default: 4)')
    parser.add_argument('--update-existing', action='store_true',
                       help='Update existing documents if they have changed')
    parser.add_argument('--force', action='store_true',
                       help='Force reprocessing of all files, even if unchanged')
    
    # Logging options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress non-error output')


def create_chunk_config(args) -> ChunkConfig:
    """Create a ChunkConfig from command-line arguments."""
    strategy_map = {
        'fixed_size': ChunkStrategy.FIXED_SIZE,
        'sentence_based': ChunkStrategy.SENTENCE_BASED,
        'paragraph_based': ChunkStrategy.PARAGRAPH_BASED,
        'code_based': ChunkStrategy.CODE_BASED,
        'markdown_based': ChunkStrategy.MARKDOWN_BASED,
    }
    
    return ChunkConfig(
        strategy=strategy_map.get(args.chunk_strategy, ChunkStrategy.SENTENCE_BASED),
        max_chunk_size=args.chunk_size,
        min_chunk_size=args.min_chunk_size,
        overlap_size=args.overlap_size,
        respect_boundaries=True,
        preserve_headers=True
    )


def create_ingestion_config(args) -> IngestionConfig:
    """Create an IngestionConfig from command-line arguments."""
    chunk_config = create_chunk_config(args)
    
    return IngestionConfig(
        chunk_config=chunk_config,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        skip_existing=not args.force,
        update_existing=args.update_existing
    )


def handle_ingest_file(args) -> int:
    """Handle the ingest-file command."""
    try:
        file_path = Path(args.file_path)
        
        if not file_path.exists():
            print(f"Error: File does not exist: {file_path}")
            return 1
        
        config = create_ingestion_config(args)
        ingestor = DocumentIngestor(config)
        
        print(f"Ingesting file: {file_path}")
        result = ingestor.ingest_file(file_path)
        
        # Print results
        if result.processed_files > 0:
            print(f"✓ Successfully processed {result.processed_files} file")
            print(f"  Created {result.total_chunks} chunks")
        elif result.skipped_files > 0:
            print(f"⚠ Skipped {result.skipped_files} file (already processed)")
        else:
            print(f"✗ Failed to process file")
            for error in result.errors:
                print(f"  Error: {error}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in ingest-file: {str(e)}")
        return 1


def handle_ingest_dir(args) -> int:
    """Handle the ingest-dir command."""
    try:
        directory_path = Path(args.directory_path)
        
        if not directory_path.exists():
            print(f"Error: Directory does not exist: {directory_path}")
            return 1
        
        if not directory_path.is_dir():
            print(f"Error: Path is not a directory: {directory_path}")
            return 1
        
        config = create_ingestion_config(args)
        ingestor = DocumentIngestor(config)
        
        print(f"Ingesting directory: {directory_path}")
        print(f"Recursive: {args.recursive}")
        print(f"Chunk strategy: {args.chunk_strategy}")
        print(f"Chunk size: {args.chunk_size} characters")
        print()
        
        result = ingestor.ingest_directory(directory_path, recursive=args.recursive)
        
        # Print results
        print("Ingestion Results:")
        print(f"  Total files found: {result.total_files}")
        print(f"  Successfully processed: {result.processed_files}")
        print(f"  Skipped (existing): {result.skipped_files}")
        print(f"  Failed: {result.failed_files}")
        print(f"  Total chunks created: {result.total_chunks}")
        
        if result.errors and not args.quiet:
            print("\nErrors:")
            for error in result.errors[:10]:  # Show first 10 errors
                print(f"  {error}")
            if len(result.errors) > 10:
                print(f"  ... and {len(result.errors) - 10} more errors")
        
        return 0 if result.failed_files == 0 else 1
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in ingest-dir: {str(e)}")
        return 1


def handle_stats(args) -> int:
    """Handle the stats command."""
    try:
        ingestor = DocumentIngestor()
        stats = ingestor.get_ingestion_stats()
        
        if 'error' in stats:
            print(f"Error retrieving stats: {stats['error']}")
            return 1
        
        print("Ingestion Statistics:")
        print(f"  Total chunks: {stats['total_chunks']}")
        print()
        
        print("Documents by status:")
        for status, count in stats['document_stats'].items():
            print(f"  {status}: {count}")
        print()
        
        print("Documents by content type:")
        for content_type, count in stats['content_type_stats'].items():
            print(f"  {content_type}: {count}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in stats: {str(e)}")
        return 1


def handle_supported_types(args) -> int:
    """Handle the supported-types command."""
    try:
        from src.core.ingestion.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        print("Supported file types:")
        print()
        
        print("Text files:")
        for ext in sorted(processor.SUPPORTED_TEXT_EXTENSIONS):
            print(f"  {ext}")
        print()
        
        print("Document files:")
        for ext in sorted(processor.SUPPORTED_DOCUMENT_EXTENSIONS):
            print(f"  {ext}")
        print()
        
        print("Notes:")
        print("  - PDF files require PyPDF2 or pdfplumber library")
        print("  - DOCX files require python-docx library")
        print("  - Text encoding is auto-detected (UTF-8, UTF-16, Latin-1, CP1252)")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in supported-types: {str(e)}")
        return 1


def handle_delete(args) -> int:
    """Handle the delete command."""
    try:
        ingestor = DocumentIngestor()
        
        print(f"Deleting document with hash: {args.file_hash}")
        success = ingestor.delete_document(args.file_hash)
        
        if success:
            print("✓ Document deleted successfully")
            return 0
        else:
            print("✗ Document not found or could not be deleted")
            return 1
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI error in delete: {str(e)}")
        return 1


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Configure logging based on verbosity
    if hasattr(args, 'verbose') and args.verbose:
        import logging
        logging.getLogger('src').setLevel(logging.DEBUG)
    elif hasattr(args, 'quiet') and args.quiet:
        import logging
        logging.getLogger('src').setLevel(logging.ERROR)
    
    # Dispatch to appropriate handler
    if args.command == 'ingest-file':
        return handle_ingest_file(args)
    elif args.command == 'ingest-dir':
        return handle_ingest_dir(args)
    elif args.command == 'stats':
        return handle_stats(args)
    elif args.command == 'supported-types':
        return handle_supported_types(args)
    elif args.command == 'delete':
        return handle_delete(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main()) 