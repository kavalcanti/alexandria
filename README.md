# Alexandria

A terminal-based chat interface for interacting with Large Language Models, featuring conversation persistence, thought process visualization, and document ingestion and retrieval capabilities for Retrieval-Augmented Generation (RAG).

## Overview

Alexandria is a terminal application for interacting with Hugging Face language models. It integrates database technologies with local model deployment for development and experimentation. Alexandria supports Retrieval-Augmented Generation (RAG) by ingesting documents from various sources to provide context-aware responses based on a document corpus.

## Key Features

- **Terminal User Interface**: Split-pane design with chat history and response windows, real-time thought process visualization, keyboard navigation
- **Model Integration**: Hugging Face Transformers support, default configuration for Qwen3-0.6B, local model caching, flexible model selection
- **Document Ingestion & RAG Pipeline**: Multi-format document support (PDF, DOCX, TXT, Markdown, code files), text chunking strategies, large file handling, vector embeddings using sentence-transformers
- **Advanced Retrieval System**: Vector similarity search, contextual search, filtering by document type and date range, multiple search interfaces
- **Data Management**: PostgreSQL-based conversation persistence, unique conversation IDs, conversation resumption, automated conversation titling
- **Context Management**: Configurable sliding context window, system prompt integration, token usage optimization

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

## Usage

Launch Alexandria:
```bash
# Start a new conversation
./alexandria.sh

# Continue an existing conversation
./alexandria.sh -c CONVERSATION_ID
# or
./alexandria.sh --conversation CONVERSATION_ID
```

Basic controls:
- `Ctrl+O`: Start new conversation
- `Ctrl+Q`: Exit application
- `Ctrl+Space`: Send message
- `Ctrl+Up/Down`: Navigate chat history
- `Shift+Up/Down`: Navigate thought process

## Document Ingestion

Ingest documents for RAG capabilities:

```bash
# Ingest a single file
python -m src.core.ingestion.cli ingest-file document.pdf

# Ingest all files in a directory
python -m src.core.ingestion.cli ingest-dir /path/to/documents

# Custom chunk size and strategy
python -m src.core.ingestion.cli ingest-dir docs/ \
    --chunk-strategy markdown_based \
    --chunk-size 1500 \
    --overlap-size 100
```

## Document Retrieval

Search ingested documents:

```bash
# Basic document search
python -m src.core.retrieval.cli search "machine learning algorithms"

# Search with max results
python -m src.core.retrieval.cli search "neural networks" --max-results 20

# Search in specific documents
python -m src.core.retrieval.cli search-docs "data analysis" --document-ids 1,2,3
```

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

## Contributing

Contributions are welcome. Please refer to the [Contributing Guide](docs/CONTRIBUTING.md) for development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](docs/LICENSE.md) file for details.