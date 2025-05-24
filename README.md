# Alexandria

A terminal-based chat interface for interacting with Large Language Models, featuring conversation persistence, thought process visualization, and document ingestion and retrieval capabilities for Retrieval-Augmented Generation (RAG).

## Overview

Alexandria is a terminal application for interacting with Hugging Face language models. It integrates database technologies with local model deployment for development and experimentation. Alexandria supports Retrieval-Augmented Generation (RAG) by ingesting documents from various sources to provide context-aware responses based on a document corpus.

## Key Features

- Terminal User Interface
  - Split-pane design: chat history and response windows
  - Real-time thought process visualization
  - Keyboard navigation
- Model Integration
  - Hugging Face Transformers support
  - Default configuration for Qwen3-0.6B
  - Local model caching
  - Flexible model selection
- Thought Process Visualization
  - Real-time model reasoning display
  - Independently scrollable thinking history
- Document Ingestion & RAG Pipeline
  - Multi-format document support: PDF, DOCX, TXT, Markdown, code files
  - Text chunking strategies: sentence-based, paragraph-based, semantic-based
  - Large file handling: automatic file-level chunking for files >100MB
  - Deduplication: using file hashes
  - Vector embeddings: using sentence-transformers
  - PostgreSQL + pgvector: for similarity search
  - Command-line tools: for batch document processing
- Advanced Retrieval System
  - Vector similarity search: L2 distance
  - Contextual search: surrounding chunk retrieval
  - Filtering: by document type, date range, content type
  - Multiple search interfaces: programmatic and CLI
  - Real-time embedding generation: for query processing
- Data Management
  - PostgreSQL-based conversation persistence
  - Unique conversation IDs
  - Conversation resumption
  - Automated conversation titling
  - Document metadata tracking and status management
- Context Management
  - Configurable sliding context window
  - System prompt integration
  - Token usage optimization
  - Document-aware context: for RAG responses
- Advanced Features
  - Vector-based similarity search for semantic search on conversation titles (not fully implemented)
  - Local model caching
  - Conversation history management
  - Vector similarity search
  - CLI tools: for document management and search

## Technical Requirements

- Python 3.12+
- PostgreSQL with pgvector extension
- Conda (for environment management)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/kavalcanti/alexandria.git
cd alexandria
```

2. Create and activate a conda environment:
```bash
conda create -p ./.conda python=3.12
conda activate ./.conda
```

3. Install dependencies using uv (recommended for faster installation):
```bash
pip install uv
uv pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```
DB_USER=your_db_user
DB_HOST=your_db_host
DB_PASS=your_db_password
DATABASE=your_database_name
HF_MODEL=Qwen/Qwen3-0.6B
EMBD_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

5. Launch Alexandria:

```bash
# Start a new conversation
./alexandria.sh

# Continue an existing conversation
./alexandria.sh -c CONVERSATION_ID
# or
./alexandria.sh --conversation CONVERSATION_ID
```

## Usage

- `Ctrl+O`: Start new conversation
- `Ctrl+Q`: Exit application
- `Ctrl+Space`: Send message
- `Ctrl+Up/Down`: Navigate chat history
- `Shift+Up/Down`: Navigate thought process

## Documentation

Comprehensive documentation is available in the `docs` directory:

- [User Guide](docs/UserGuide.md) - Detailed usage instructions
- [Contributing Guide](docs/CONTRIBUTING.md) - Development guidelines
- [License](docs/LICENSE.md) - MIT License
- [TODOs](docs/TODOs.md) - Development roadmap

**Ingestion & Retrieval Documentation:**
- [Document Ingestion Guide](src/core/ingestion/README.md) - Detailed ingestion documentation
- [Document Retrieval Guide](src/core/retrieval/README.md) - Comprehensive retrieval documentation

## Architecture

```
alexandria/
├── ai_models/          # Model storage and cache
├── conf/              # Configuration files
├── datasets/          # Dataset storage
├── docs/              # Documentation
├── logs/              # Application logs
├── src/               # Source code
│   ├── core/         # Core business logic
│   │   ├── embedding/    # Vector embedding generation
│   │   ├── ingestion/    # Document ingestion pipeline
│   │   ├── managers/     # Service managers
│   │   ├── memory/       # Conversation persistence
│   │   ├── retrieval/    # Document retrieval system
│   │   ├── services/     # Core services
│   │   └── tools/        # LLM Tools
│   ├── infrastructure/ # Database operations, file system, etc.
│   ├── ui/           # User interface
│   ├── utils/          # Utility functions and classes
│   ├── logger.py       # Logging configuration
│   └── userland.py     # User-facing scripts and CLI entry points
├── main.py           # Application entry point
├── alexandria.sh     # Launch script
├── pyproject.toml    # Project configuration
└── requirements.txt  # Dependencies
```

## Technical Stack

- **Language Models**: Hugging Face transformers
- **Database**: PostgreSQL with pgvector
- **Interface**: prompt_toolkit
- **Vector Operations**: pgvector
- **Embeddings**: sentence-transformers
- **Document Processing**: PyPDF2, python-docx, custom text processors
- **Vector Search**: L2 distance with automatic similarity scoring

## RAG Pipeline Details

### Chunking Strategies

1. **Sentence-Based**: Intelligent sentence boundary detection
2. **Paragraph-Based**: Natural paragraph breaks
3. **Semantic-Based**: Content-aware chunking
4. **Code-Based**: Programming language syntax awareness
5. **Markdown-Based**: Header and section preservation
6. **Fixed-Size**: Simple character-based chunking

### Vector Embeddings

- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Generation**: Automatic embedding creation during ingestion
- **Storage**: PostgreSQL with pgvector extension
- **Search**: L2 distance with similarity score conversion

### Large File Handling

- **Automatic detection** of files >100MB
- **File-level chunking** before text processing
- **Memory-efficient** streaming processing
- **Temporary file management** with automatic cleanup

## Contributing

Contributions are welcome. Please refer to the [Contributing Guide](docs/CONTRIBUTING.md) for development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](docs/LICENSE.md) file for details.

## Dependencies

- [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) - Terminal interface framework
- [Hugging Face](https://huggingface.co/) - Transformer models
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search
- [sentence-transformers](https://www.sbert.net/) - Text embedding generation
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF Processing
- [python-docx](https://python-docx.readthedocs.io/) - DOCX processing