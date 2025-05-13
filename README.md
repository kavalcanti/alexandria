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

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/alexandria.git
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

4. Set up PostgreSQL:
   - Install PostgreSQL
   - Install pgvector extension:
     ```sql
     CREATE EXTENSION vector;
     ```
   - Create a database for Alexandria

5. Configure environment variables:
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

## Usage

1. Start the application:
```bash
./alexandria.sh
```

2. Key Controls:
   - `Ctrl+Space`: Send message
   - `Ctrl+Q`: Quit application
   - `Ctrl+Up/Down`: Scroll chat history
   - `Shift+Up/Down`: Scroll thinking window
   - `Ctrl+O`: Reset conversation handler

## Project Structure

```
alexandria/
├── src/
│   ├── userland.py       # TUI implementation
│   ├── conversation.py   # LLM interaction handling
│   ├── db_models.py      # Database schema and models
│   ├── llm_db_loggers.py # Database operations
│   └── logger.py         # Logging utilities
├── main.py              # Application entry point
├── alexandria.sh        # Launch script
├── requirements.txt     # Project dependencies
└── README.md           # This file
```

## Technical Details

- **LLM Integration**: Uses Hugging Face transformers, defaulting to Qwen3-0.6B model
- **Database**: PostgreSQL with pgvector for vector embeddings
- **UI Framework**: Built with prompt_toolkit for terminal interface
- **Context Management**: Configurable sliding window for conversation history
- **Model Caching**: Local storage of downloaded models for improved performance

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your chosen license here]

## Acknowledgments

- [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for the terminal interface
- [Hugging Face](https://huggingface.co/) for transformer models
- [pgvector](https://github.com/pgvector/pgvector) for vector similarity search capabilities
