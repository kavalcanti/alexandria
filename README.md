# Alexandria

A sophisticated terminal-based chat interface for interacting with Large Language Models, featuring conversation persistence and thought process visualization.

## Features

- 🖥️ Terminal User Interface with split-pane design
- 🤖 Integration with Hugging Face transformers for LLM functionality
- 💭 Visualization of LLM reasoning/thought process
- 💾 Persistent conversation storage using PostgreSQL
- 🔍 Vector embedding support for future semantic search capabilities
- 📜 Configurable conversation history with sliding context window
- 💻 Local model caching for improved performance

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
./alexandria.sh
```

## Documentation

Our documentation is organized in the `docs` folder:

- [User Guide](docs/UserGuide.md) - Detailed usage instructions and keyboard shortcuts
- [Contributing Guide](docs/CONTRIBUTING.md) - Guidelines for contributors
- [License](docs/LICENSE.md) - MIT License
- [TODOs](docs/TODOs.md) - Current development status and planned features

## Project Structure

```
alexandria/
├── src/
│   ├── userland.py       # TUI implementation
│   ├── conversation.py   # LLM interaction handling
│   ├── db_models.py      # Database schema and models
│   ├── llm_db_loggers.py # Database operations
│   └── logger.py         # Logging utilities
├── docs/                # Documentation
│   ├── UserGuide.md     # User manual
│   ├── CONTRIBUTING.md  # Contribution guidelines
│   ├── LICENSE.md      # MIT License
│   └── TODOs.md        # Development roadmap
├── main.py             # Application entry point
├── alexandria.sh       # Launch script
└── requirements.txt    # Project dependencies
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
