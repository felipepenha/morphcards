# MorphCards Architecture

This document provides a comprehensive overview of the MorphCards system architecture using Mermaid diagrams.

## System Overview

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Interface]
        Demo[Gradio Demo]
        Web[Web Interface]
    end
    
    subgraph "Core Application Layer"
        Scheduler[FSRS Scheduler]
        Optimizer[Parameter Optimizer]
        CardManager[Card Management]
    end
    
    subgraph "AI Services Layer"
        AIService[AI Service Interface]
        OpenAI[OpenAI Service]
        Gemini[Gemini Service]
    end
    
    subgraph "Data Layer"
        Database[(DuckDB Database)]
        Cards[(Cards Table)]
        Reviews[(Review Logs)]
        Vocab[(Vocabulary)]
    end
    
    subgraph "External APIs"
        OpenAI_API[OpenAI API]
        Gemini_API[Gemini API]
    end
    
    CLI --> Scheduler
    Demo --> Scheduler
    Web --> Scheduler
    
    Scheduler --> CardManager
    Scheduler --> AIService
    Optimizer --> Scheduler
    
    CardManager --> Database
    AIService --> OpenAI
    AIService --> Gemini
    
    OpenAI --> OpenAI_API
    Gemini --> Gemini_API
    
    Database --> Cards
    Database --> Reviews
    Database --> Vocab
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Scheduler
    participant AI
    participant Database
    participant API
    
    User->>CLI: Add new card
    CLI->>Database: Store card
    Database-->>CLI: Confirmation
    
    User->>CLI: Review card
    CLI->>Scheduler: Process review
    Scheduler->>Database: Get learned vocabulary
    Database-->>Scheduler: Vocabulary list
    
    alt Vocabulary sufficient
        Scheduler->>AI: Generate new sentence
        AI->>API: API call
        API-->>AI: New sentence
        AI-->>Scheduler: Generated sentence
    else Vocabulary insufficient
        Scheduler->>Scheduler: Use original sentence
    end
    
    Scheduler->>Database: Update card
    Scheduler->>Database: Store review log
    Scheduler-->>CLI: Review results
    CLI-->>User: New sentence & next review date
```

## Database Schema

```mermaid
erDiagram
    CARDS {
        string id PK
        string word
        string sentence
        string original_sentence
        float stability (nullable)
        float difficulty (nullable)
        datetime due_date
        datetime created_at
        datetime last_reviewed
        int review_count
    }
    
    REVIEW_LOGS {
        string id PK
        string card_id FK
        datetime review_time
        int rating
        float interval
        float stability (nullable)
        float difficulty (nullable)
    }
    
    VOCABULARY {
        string word PK
        datetime first_seen
        datetime last_reviewed
        int review_count
        int mastery_level
    }
    
    CARDS ||--o{ REVIEW_LOGS : "has reviews"
    CARDS ||--o| VOCABULARY : "contains word"
```

## Component Architecture

```mermaid
graph LR
    subgraph "Core Module"
        Card[Card Class]
        Rating[Rating Enum]
        ReviewLog[ReviewLog Class]
    end
    
    subgraph "Scheduler Module"
        Scheduler[Scheduler Class]
        Optimizer[Optimizer Class]
    end
    
    subgraph "Database Module"
        VocabDB[VocabularyDatabase]
        DuckDB[(DuckDB)]
    end
    
    subgraph "AI Module"
        AIService[AIService Interface]
        OpenAIService[OpenAI Implementation]
        GeminiService[Gemini Implementation]
    end
    
    subgraph "Interface Module"
        CLI[CLI Interface]
        Demo[Demo Interface]
    end
    
    Card --> Scheduler
    Rating --> Scheduler
    ReviewLog --> Scheduler
    
    Scheduler --> VocabDB
    Scheduler --> AIService
    
    VocabDB --> DuckDB
    
    AIService --> OpenAIService
    AIService --> GeminiService
    
    CLI --> Scheduler
    Demo --> Scheduler
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        Local[Local Development]
        Tests[Test Suite]
        Linting[Code Quality Tools]
    end
    
    subgraph "Container Environment"
        Container[Container Image]
        PodmanCompose[Podman Compose]
        DockerCompose[Docker Compose]
        Podman[Podman Support]
        Docker[Docker Support]
    end
    
    subgraph "Production Environment"
        PyPI[PyPI Package]
        Users[End Users]
        APIs[AI APIs]
    end
    
    Local --> Tests
    Tests --> Linting
    Linting --> Container
    
    Container --> PodmanCompose
    Container --> DockerCompose
    Container --> Podman
    Container --> Docker
    
    Container --> PyPI
    PyPI --> Users
    Users --> APIs
```

## Key Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Interface Segregation**: AI services implement a common interface
3. **Dependency Inversion**: High-level modules don't depend on low-level modules
4. **Single Responsibility**: Each class has one reason to change
5. **Open/Closed Principle**: Open for extension, closed for modification

## Performance Characteristics

- **API Response Time**: < 1 second for AI sentence generation
- **Database Operations**: In-memory DuckDB for fast access
- **Memory Usage**: Efficient storage with minimal overhead
- **Scalability**: Modular design allows for easy scaling

## Quick Demo Commands

### One-shot Demo with Podman

```bash
# Run demo immediately (no build required)
# Assumes you have a .env file with your API key
podman run --rm -p 7860:7860 \
  --env-file .env \
  docker.io/library/python:3.11-slim \
  bash -c "pip install morphcards[demo] && python -m morphcards.demo"
```

### Alternative Demo Commands

```bash
# With specific version
podman run --rm -p 7860:7860 \
  --env-file .env \
  docker.io/library/python:3.11-slim \
  bash -c "pip install 'morphcards[demo]>=0.1.0' && python -m morphcards.demo"

# With custom port
podman run --rm -p 8080:7860 \
  --env-file .env \
  docker.io/library/python:3.11-slim \
  bash -c "pip install morphcards[demo] && python -m morphcards.demo"
```

### Environment Setup

**Create a `.env` file in your project root:**
```bash
# For Gemini users (default)
GEMINI_API_KEY=your-gemini-api-key-here

# For OpenAI users
# OPENAI_API_KEY=your-openai-api-key-here
```

**Note**: This documentation assumes Gemini is being used. For OpenAI users, use `OPENAI_API_KEY` instead of `GEMINI_API_KEY` in your `.env` file.

## Makefile Commands

For quick access to common commands, use the included Makefile:

```bash
make all        # Build, run demo, and show status
make build      # Build container image
make demo       # Run demo (one-shot)
make run        # Build and run
make clean      # Clean up containers
make help       # Show all available commands
```

The Makefile assumes podman is being used and automatically handles environment variables from your `.env` file.

## Security Considerations

- **API Key Management**: Environment variables for sensitive data
- **Input Validation**: Pydantic models for data validation
- **Error Handling**: Graceful fallbacks without exposing internals
- **Rate Limiting**: Built-in handling for API rate limits