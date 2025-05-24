#!/usr/bin/env python3
"""Test script to verify keyboard interrupt handling in document ingestor."""

import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.ingestion.document_ingestor import DocumentIngestor, IngestionConfig


def test_interrupt_handling():
    """Test that keyboard interrupts are properly handled."""
    print("Testing keyboard interrupt handling...")
    print("The script will start processing a large file.")
    print("Press Ctrl+C to test interrupt handling.")
    print("=" * 50)
    
    # Create a configuration that processes slowly to give time for interrupt
    config = IngestionConfig(
        max_workers=1,  # Use single worker to make it easier to interrupt
        batch_size=1    # Process one file at a time
    )
    
    try:
        with DocumentIngestor(config) as ingestor:
            print("Starting ingestion of large file...")
            result = ingestor.ingest_file('datasets/output.txt')
            print(f"Completed! Processed: {result.processed_files}, Chunks: {result.total_chunks}")
            
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("✓ KeyboardInterrupt caught successfully!")
        print("✓ Workers should be properly shut down.")
        print("✓ Cleanup should have been performed.")
        print("=" * 50)
        return True
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False
    
    print("✓ Processing completed without interruption")
    return True


if __name__ == "__main__":
    success = test_interrupt_handling()
    sys.exit(0 if success else 1) 