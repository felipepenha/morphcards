# MorphCards

**Spaced Spatial Repetition (SSR) software with AI-generated sentence variations for language learning.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/morphcards.svg)](https://badge.fury.io/py/morphcards)

## 🎯 Overview

Traditional SSR software often repeats the exact same sentence cards, leading users to memorize the front of cards rather than truly learning the language. MorphCards solves this by generating new, contextually appropriate sentences each time a card is reviewed, ensuring learners can identify and understand words in different contexts.

## 📚 Documentation

- **[Architecture Documentation](docs/architecture.md)** - System design, data flow, and component diagrams
- **[API Reference](#-api-reference)** - Detailed class and method documentation
- **[Examples](#-examples)** - Usage examples and tutorials

## 🔑 Environment Variables

**This documentation assumes Gemini is being used by default.** All examples assume you have a `.env` file with your API keys.

**Create a `.env` file in your project root:**
```bash
# .env file
GEMINI_API_KEY=your-gemini-api-key-here
# OPENAI_API_KEY=your-openai-api-key-here  # Uncomment for OpenAI
```

**For OpenAI users**: Replace `GEMINI_API_KEY` with `OPENAI_API_KEY` in your `.env` file.

## ✨ Features

- **FSRS-based Spaced Repetition**: Uses the Free Spaced Repetition Scheduler for optimal learning intervals
- **AI-Generated Sentence Variations**: Creates new sentences using OpenAI or Google Gemini APIs
- **Vocabulary-Aware Generation**: Ensures new sentences only use previously learned vocabulary
- **In-Memory Database**: Fast DuckDB-based storage for cards and review history
- **Parameter Optimization**: Automatically optimizes FSRS parameters based on your learning patterns
- **Multiple AI Services**: Support for both OpenAI and Google Gemini APIs
- **CLI Interface**: Command-line tool for daily use
- **Web Demo**: Interactive Gradio interface for testing and demonstration

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install morphcards

# Install with demo dependencies
pip install morphcards[demo]

# Install with development dependencies
pip install morphcards[dev]
```

### 🎯 Quick Demo (One Command)

```bash
# Run demo immediately with Podman
podman run --rm -p 7860:7860 \
  --env-file .env \
  docker.io/library/python:3.11-slim \
  bash -c "pip install morphcards[demo] && python -m morphcards.demo"
```

Then open http://localhost:7860 in your browser!

**Note**: The first run may take a few minutes as it downloads and installs dependencies.

**Environment Variables**: This documentation assumes Gemini is being used. For OpenAI users, replace `GEMINI_API_KEY` with `OPENAI_API_KEY` in all commands.

**Pro Tip**: Use `make all` to run everything at once! See the [Makefile section](#-quick-start-with-makefile) for details.

### Container Setup (Recommended)

```bash
# Using Podman (recommended)
podman build -t morphcards .
podman run -p 7860:7860 morphcards

# One-shot demo with Podman (no build required)
podman run --rm -p 7860:7860 --env-file .env docker.io/library/python:3.11-slim bash -c "
  pip install morphcards[demo] &&
  python -m morphcards.demo
"

# Using Docker
docker build -t morphcards .
docker run -p 7860:7860 morphcards
```

### Basic Usage

```python
from morphcards import Card, Scheduler, VocabularyDatabase
from morphcards.ai import AIServiceFactory
from datetime import datetime

# Initialize components
db = VocabularyDatabase()
scheduler = Scheduler()
ai_service = AIServiceFactory.create_service("openai")

# Create a card
card = Card(
    id="hello_1",
    word="hello",
    sentence="Hello, how are you?",
    original_sentence="Hello, how are you?",
    due_date=datetime.now()
)

# Add to database
db.add_card(card)

# Review the card
updated_card, review_log = scheduler.review_card(
    card=card,
    rating=3,  # Good
    now=datetime.now(),
    ai_api_key="your-api-key",
    vocabulary_database=db,
    ai_service=ai_service
)

print(f"New sentence: {updated_card.sentence}")
```

### Command Line Interface

```bash
# Add a new card
morphcards add "bonjour" "Bonjour, comment allez-vous?" --language French

# Review due cards (uses .env file)
morphcards review --ai-service gemini

# Show statistics
morphcards stats

# Optimize parameters
morphcards optimize
```

## 🏗️ Architecture

For detailed architecture diagrams and system design, see [Architecture Documentation](docs/architecture.md).

### Core Components

- **`Card`**: Represents a flashcard with word, sentence, and FSRS parameters
- **`Scheduler`**: Manages spaced repetition scheduling using FSRS algorithm
- **`Optimizer`**: Optimizes FSRS parameters based on review history
- **`VocabularyDatabase`**: Stores cards, reviews, and vocabulary using DuckDB
- **`AIService`**: Abstract interface for AI sentence generation
- **`OpenAIService`**: OpenAI API integration
- **`GeminiService`**: Google Gemini API integration

### Data Flow

1. **Card Creation**: User creates a card with word and sentence
2. **Review Process**: User reviews card and rates their recall
3. **AI Generation**: System generates new sentence using learned vocabulary
4. **FSRS Update**: Card parameters updated based on rating
5. **Database Storage**: Updated card and review log saved

## 🔧 Configuration

### Environment Variables

```bash
# Google Gemini API (recommended)
export GEMINI_API_KEY="your-gemini-key"

# OpenAI API (alternative)
export OPENAI_API_KEY="your-openai-key"
```

### API Service Selection

```python
# Choose AI service (Gemini recommended)
ai_service = AIServiceFactory.create_service("gemini")  # or "openai"

# Custom Gemini model
gemini_service = GeminiService(model="gemini-pro")

# Custom OpenAI model
openai_service = OpenAIService(model="gpt-4")
```

## 🐳 Containerization

### Using Podman (Recommended)

```bash
# Build and run with Podman
podman build -t morphcards .
podman run -p 7860:7860 --env-file .env morphcards

# Using Podman Compose (uses .env file)
podman-compose up -d
```

### Using Docker (Alternative)

```bash
# Build and run with Docker
docker build -t morphcards .
docker run -p 7860:7860 --env-file .env morphcards

# Using Docker Compose (uses .env file)
docker-compose up -d
```

## 🚀 Quick Start with Makefile

```bash
# Run everything at once (recommended)
make all

# Or use individual commands
make build      # Build container
make demo       # Run demo in container (one-shot)
make demo-local # Run demo locally (requires install)
make demo-quick # Quick local demo (auto-install)
make run        # Build and run
make clean      # Clean up
make help       # Show all commands
```

**Note**: The Makefile assumes podman is being used. For docker users, replace `podman` with `docker` in the Makefile or use the container commands directly.

**Local Development**: For development and testing, use `make demo-quick` which installs dependencies locally and runs the demo without containers.

**Note**: If you encounter pip version issues, the container-based demo (`make demo`) is recommended as it uses a fresh Python environment.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=morphcards

# Run specific test categories
pytest -m unit
pytest -m integration
```

## 📊 Demo Interface

Start the interactive demo:

```bash
# Run demo locally
python -m morphcards.demo

# Or use the CLI
morphcards demo
```

### 🐳 Quick Demo with Podman (One-shot)

```bash
# Run demo directly with Podman (no build required)
podman run --rm -p 7860:7860 \
  --env-file .env \
  docker.io/library/python:3.11-slim \
  bash -c "pip install morphcards[demo] && python -m morphcards.demo"

# Alternative: Run with specific version
podman run --rm -p 7860:7860 \
  --env-file .env \
  docker.io/library/python:3.11-slim \
  bash -c "pip install 'morphcards[demo]>=0.1.0' && python -m morphcards.demo"
```

### 🚀 Demo Features

The demo provides:
- **Add Cards**: Create new learning cards
- **Review Cards**: Interactive review process with AI sentence generation
- **Statistics**: View learning progress and vocabulary stats
- **Optimization**: Optimize FSRS parameters

## 🔍 API Reference

### Core Classes

#### `Card`
- `id`: Unique identifier
- `word`: Word to learn
- `sentence`: Current sentence
- `original_sentence`: Original sentence when created
- `stability`: FSRS stability parameter
- `difficulty`: FSRS difficulty parameter
- `due_date`: Next review date

#### `Scheduler`
- `review_card()`: Process card review and generate new sentence
- `parameters`: FSRS algorithm parameters

#### `VocabularyDatabase`
- `add_card()`: Add new card
- `get_due_cards()`: Get cards ready for review
- `get_learned_vocabulary()`: Get all learned words
- `add_review_log()`: Record review completion

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone https://github.com/felipepenha/morphcards.git
cd morphcards

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run linting
black src/ tests/
mypy src/
ruff check src/ tests/

# Run with Podman (recommended)
podman build -t morphcards-dev .
podman run -it --rm -p 7860:7860 --env-file .env morphcards-dev

# Or with Docker
docker build -t morphcards-dev .
docker run -it --rm -p 7860:7860 --env-file .env morphcards-dev
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FSRS](https://github.com/ishiko732/FSRS4Anki) - Free Spaced Repetition Scheduler
- [DuckDB](https://duckdb.org/) - In-process analytical database
- [OpenAI](https://openai.com/) - AI language models
- [Google Gemini](https://ai.google.dev/) - AI language models

## 📞 Support

- **Author**: Felipe Campos Penha
- **Email**: felipe.penha@alumni.usp.br
- **GitHub**: [@felipepenha](https://github.com/felipepenha)
- **Issues**: [GitHub Issues](https://github.com/felipepenha/morphcards/issues)

## 🔧 Troubleshooting

### Demo Issues

**Demo won't start**: Make sure port 7860 is available. Use a different port with `-p 8080:7860` if needed.

**API key errors**: Ensure your `.env` file contains the correct API key. For Gemini users: `GEMINI_API_KEY=your-key`. For OpenAI users: `OPENAI_API_KEY=your-key`.

**Slow first run**: The one-shot demo downloads dependencies on first run. Subsequent runs will be faster.

**Permission denied**: On some systems, you may need to run podman with `sudo` or configure user namespaces.

### Common Commands

```bash
# Check if port is in use
lsof -i :7860

# Kill process using port
kill -9 $(lsof -t -i:7860)

# Run on different port
podman run --rm -p 8080:7860 --env-file .env \
  docker.io/library/python:3.11-slim \
  bash -c "pip install morphcards[demo] && python -m morphcards.demo"

# Note: Your .env file should contain either GEMINI_API_KEY or OPENAI_API_KEY
```

---

**MorphCards** - Making language learning more effective through intelligent spaced repetition.
