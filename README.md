# MorphCards

**Spaced Spatial Repetition (SSR) software with AI-generated sentence variations for language learning.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![PyPI version](https://badge.fury.io/py/morphcards.svg)](https://badge.fury.io/py/morphcards)

For developer documentation (including containerization and contributing), see [DEVELOPERS.md](https://github.com/felipepenha/morphcards/blob/main/DEVELOPERS.md).

## 🎯 Overview

Traditional SSR software often repeats the exact same sentence cards, leading users to memorize the front of cards rather than truly learning the language. MorphCards solves this by generating new, contextually appropriate sentences each time a card is reviewed, ensuring learners can identify and understand words in different contexts.

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
```

### Basic Usage

```python
from morphcards import Card, Scheduler, VocabularyDatabase
from morphcards.ai import AIServiceFactory
from datetime import datetime

# Initialize components
db = VocabularyDatabase()
scheduler = Scheduler()
ai_service = AIServiceFactory.create_service("gemini", model_name="gemini-2.5-flash") # Example with model_name

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
morphcards review --ai-service gemini --model-name gemini-2.5-flash

# Show statistics
morphcards stats

# Optimize parameters
morphcards optimize
```

## 📊 Demo Interface

Start the interactive demo:

```bash
# Run demo locally (after installing with [demo] extras)
morphcards demo
```

The demo provides:
- **Add Cards**: Create new learning cards
- **Review Cards**: Interactive review process with AI sentence generation
- **Statistics**: View learning progress and vocabulary stats
- **Optimization**: Optimize FSRS parameters

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

## 🔍 API Reference

### Core Classes

#### `Card`
- `id`: Unique identifier
- `word`: Word to learn
- `sentence`: Current sentence
- `original_sentence`: Original sentence when created
- `stability`: FSRS stability parameter (nullable)
- `difficulty`: FSRS difficulty parameter (nullable)
- `due_date`: Next review date
- `state`: FSRS state (New, Learning, Review, Relearning)

#### `Scheduler`
- `review_card()`: Process card review and generate new sentence
- `_fsrs`: Internal FSRS scheduler instance (manages parameters internally)

#### `VocabularyDatabase`
- `add_card()`: Add new card
- `get_due_cards()`: Get cards ready for review
- `get_learned_vocabulary()`: Get all learned words
- `add_review_log()`: Record review completion (now stores UUID for review logs)

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