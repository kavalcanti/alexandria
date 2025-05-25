# Alexandria CLI Tests

Simple test suite for the Alexandria CLI utilities in `src/utils/`.

## Running Tests

### Run all tests:
```bash
# From project root
python tests/run_tests.py

# Or using module syntax
python -m tests.run_tests
```

### Run specific test file:
```bash
python -m unittest tests.test_cli_utils
```

### Run specific test class:
```bash
python -m unittest tests.test_cli_utils.TestRetrievalCLI
```

### Run specific test method:
```bash
python -m unittest tests.test_cli_utils.TestRetrievalCLI.test_parse_ids_valid
```

## What's Tested

The test suite covers:

- **Retrieval CLI** (`retrieval_cli.py`):
  - Argument parsing for all commands
  - ID and type parsing functions
  - Result formatting (JSON/text)
  - Command-line option validation

- **RAG CLI** (`rag_cli.py`):
  - Argument parsing for ask/interactive/search commands
  - RAG configuration creation from arguments
  - Output formatting options

- **Ingestion CLI** (`ingestion_cli.py`):
  - File and directory ingestion argument parsing
  - Chunk configuration creation
  - File chunk configuration
  - Ingestion configuration assembly

- **File Utils** (`file_utils.py`):
  - LLM output saving functionality
  - File path generation
  - Content formatting

## Test Strategy

These tests focus on:
- **Argument parsing**: Ensuring CLI parsers work correctly
- **Configuration creation**: Testing that arguments are properly converted to config objects
- **Input validation**: Checking error handling for invalid inputs
- **Basic functionality**: Unit tests for utility functions

The tests use Python's built-in `unittest` module and minimal mocking to avoid external dependencies, keeping it simple for a hobby project.

## Notes

- Tests use mocking to avoid dependencies on databases, AI models, or file systems
- Focus is on the CLI interface logic rather than end-to-end functionality
- Designed to be fast and reliable for development workflow 