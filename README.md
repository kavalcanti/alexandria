# Alexandria

A terminal-based chat interface for interacting with Large Language Models, featuring conversation persistence and thought process visualization.

## Overview

Alexandria is a sophisticated terminal application that provides a robust interface for interacting with huggingface language models. It combines modern database technologies with efficient local model deployment to create a seamless development and experimentation environment.

## Key Features

- Terminal User Interface
  - Split-pane design with chat history and response windows
  - Real-time thought process visualization
  - Keyboard navigation
- Model Integration
  - Hugging Face Transformers support
  - Default configuration for Qwen3-0.6B
  - Local model caching system
  - Flexible model selection options
- Thought Process Visualization
  - Real-time model reasoning display
  - Independent scrollable thinking history
- Data Management
  - PostgreSQL-based conversation persistence
  - Unique conversation identification system
  - Conversation resumption capabilities
  - Automated conversation titling
- Context Management
  - Configurable sliding context window
  - System prompt integration
  - Token usage optimization
- Advanced Features
  - Vector based similarity search support for semantic search on conversation titles (not fully implemented)
  - Local model caching system
  - Conversation history management
  - Vector similarity search capabilities

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
LOGFILE=alexandria.log
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

## Architecture

```
alexandria/
├── ai_models/          # Model storage and cache
├── conf/              # Configuration files
├── datasets/          # Dataset storage
├── docs/              # Documentation
├── logs/              # Application logs
├── src/               # Source code
│   ├── db/           # Database operations
│   ├── llm/          # LLM integration
│   └── ui/           # User interface
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

## Contributing

Contributions are welcome. Please refer to the [Contributing Guide](docs/CONTRIBUTING.md) for development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](docs/LICENSE.md) file for details.

## Dependencies

- [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) - Terminal interface framework
- [Hugging Face](https://huggingface.co/) - Transformer models
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search