#!/usr/bin/env python3
"""Debug script to trace large file processing."""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.ingestion.document_ingestor import DocumentIngestor, IngestionConfig


def debug_large_file_processing():
    """Debug the large file processing step by step."""
    file_path = Path('datasets/output.txt')
    
    print("=" * 60)
    print("DEBUG: Large File Processing")
    print("=" * 60)
    
    # Create ingestor
    config = IngestionConfig(max_workers=1, batch_size=1)
    ingestor = DocumentIngestor(config)
    
    print(f"1. File: {file_path}")
    print(f"   Size: {file_path.stat().st_size / 1024 / 1024:.1f}MB")
    
    # Check file chunker
    print(f"2. File chunker enabled: {ingestor.file_chunker is not None}")
    if ingestor.file_chunker:
        should_chunk = ingestor.file_chunker.should_chunk_file(file_path)
        print(f"   Should chunk: {should_chunk}")
    
    # Get metadata
    print("3. Getting file metadata...")
    file_metadata = ingestor.document_processor.get_file_metadata(file_path)
    print(f"   Content type: {file_metadata['content_type']}")
    print(f"   File hash: {file_metadata['file_hash'][:12]}...")
    
    # Check if exists
    print("4. Checking if file exists in database...")
    existing = ingestor._get_existing_document(file_metadata['file_hash'])
    print(f"   Exists: {existing is not None}")
    
    # Determine processing path
    print("5. Determining processing path...")
    if (ingestor.file_chunker is not None and 
        ingestor.file_chunker.should_chunk_file(file_path)):
        print("   -> Will use LARGE FILE processing")
        
        # Test file chunking
        print("6. Creating file chunks...")
        file_chunks = ingestor.file_chunker.chunk_file(file_path)
        print(f"   Created {len(file_chunks)} chunks")
        
        if file_chunks:
            print(f"   First chunk: {file_chunks[0].temp_file_path}")
            print(f"   First chunk size: {file_chunks[0].size_bytes / 1024 / 1024:.1f}MB")
            
            # Test processing first chunk only
            print("7. Testing first chunk processing...")
            try:
                chunk_text = ingestor.document_processor.extract_text_content(file_chunks[0].temp_file_path)
                print(f"   Extracted {len(chunk_text)} characters")
                
                # Test text chunking
                text_chunks = ingestor.text_chunker.chunk_text(chunk_text, file_metadata['content_type'])
                print(f"   Created {len(text_chunks)} text chunks from first file chunk")
                
            except Exception as e:
                print(f"   ERROR: {e}")
        
        # Cleanup
        ingestor.file_chunker.cleanup_temp_files()
        
    else:
        print("   -> Will use REGULAR FILE processing")
        print("   WARNING: This will load entire file into memory!")
    
    print("=" * 60)


if __name__ == "__main__":
    debug_large_file_processing() 