# For Developers

This document provides instructions for developers who want to contribute to MorphCards or run it in a containerized environment. For user documentation, please see the [main README file](README.md).

## 🚀 Quick Demo (One Command)

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
