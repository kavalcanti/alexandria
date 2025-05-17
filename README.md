# Alexandria

A sophisticated terminal-based chat interface for interacting with Large Language Models, featuring conversation persistence and thought process visualization.

## Features

- 🖥️ Terminal User Interface with split-pane design
- 🤖 Integration with Hugging Face transformers for LLM functionality
- 💭 Visualization of LLM reasoning/thought process
- 💾 Persistent conversation storage using PostgreSQL
- 🔄 Automatic conversation management with unique IDs
- 🔍 Vector embedding support for future semantic search capabilities
- 📜 Configurable conversation history with sliding context window
- 💻 Local model caching for improved performance
- 🔄 Resume previous conversations using conversation IDs

## Prerequisites

- Python 3.12+
- PostgreSQL with pgvector extension
- Conda (for environment setup)

## Quick Start Guide

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

5. Start Alexandria:

```bash
# Start a new conversation (default behavior)
./alexandria.sh

# Continue an existing conversation
./alexandria.sh -c CONVERSATION_ID
# or
./alexandria.sh --conversation CONVERSATION_ID
```

During use:
- Press `Ctrl+O` to start a new conversation at any time
- Press `Ctrl+Q` to exit the application
- Press `Ctrl+Space` to send a message
- Use `Ctrl+Up/Down` to scroll chat history
- Use `Shift+Up/Down` to scroll thought process

## Documentation

Our documentation is organized in the `docs` folder:

- [User Guide](docs/UserGuide.md) - Detailed usage instructions and keyboard shortcuts
- [Contributing Guide](docs/CONTRIBUTING.md) - Guidelines for contributors
- [License](docs/LICENSE.md) - MIT License
- [TODOs](docs/TODOs.md) - Current development status and planned features

## Project Structure

```
alexandria/
├── ai_models/          # AI model storage and cache
├── conf/              # Configuration files
├── datasets/          # Dataset storage
├── docs/              # Documentation
│   ├── UserGuide.md   # User manual
│   ├── CONTRIBUTING.md# Contribution guidelines
│   ├── LICENSE.md     # MIT License
│   └── TODOs.md       # Development roadmap
├── logs/              # Application logs
├── src/               # Source code
│   ├── db/           # Database operations and models
│   ├── llm/          # LLM integration and processing
│   ├── ui/           # User interface components
│   ├── logger.py     # Logging setup
│   └── userland.py   # Core application logic
├── .conda/            # Conda environment directory
├── .venv/             # Virtual environment directory
├── main.py           # Application entry point
├── alexandria.sh     # Launch script
├── pyproject.toml    # Project metadata and configuration
├── requirements.txt  # Project dependencies
└── uv.lock          # Dependency lock file
```

## Technical Stack

- **LLM**: Hugging Face transformers (default: Qwen3-0.6B)
- **Database**: PostgreSQL with pgvector
- **UI**: prompt_toolkit
- **Vector Search**: pgvector

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](docs/LICENSE.md) file for details.

## Acknowledgments

- [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for the terminal interface
- [Hugging Face](https://huggingface.co/) for transformer models
- [pgvector](https://github.com/pgvector/pgvector) for vector similarity search capabilities