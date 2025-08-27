# MorphCards Makefile
# Assumes podman is being used (compatible with docker)

.PHONY: help build run demo test clean all install-dev install-demo mypy format audit

# Default target
help:
	@echo "MorphCards - Available Commands:"
	@echo ""
	@echo "  make build      - Build the container image"
	@echo "  make run        - Run the built container"
	@echo "  make demo       - Run demo in container (one-shot)"
	@echo "  make demo-port  - Run demo on custom port (8080)"
	@echo "  make demo-local - Run demo locally (requires install)"
	@echo "  make demo-quick - Quick local demo (auto-install)"
	@echo "  make test       - Run tests in container"
	@echo "  make clean      - Clean up containers and images"
	@echo "  make install-dev - Install development dependencies"
	@echo "  make install-demo - Install demo dependencies"
	@echo "  make all        - Build, run demo, and show status"
	@echo "  make format     - Run black and isort formatters"
	@echo "  make mypy       - Run mypy static type checker"
	@echo "  make audit      - Run security scans (Trivy and pip-audit)"
	@echo ""
	@echo "Environment:"
	@echo "  - Ensure .env file exists with your API key"
	@echo "  - For Gemini: GEMINI_API_KEY=your-key"
	@echo "  - For OpenAI: OPENAI_API_KEY=your-key"
	@echo ""

# Build the container image
build:
	@echo "🔨 Building MorphCards container..."
	podman build -t morphcards .
	@echo "✅ Build complete! Image: morphcards"

# Run the built container
run: build
	@echo "🚀 Running MorphCards container..."
	podman run --rm -p 7860:7860 --env-file .env morphcards

# Run demo directly (one-shot, no build required)
demo:
	@echo "🎯 Running MorphCards demo (one-shot)..."
	podman run --rm -p 7860:7860 --env-file .env \
		-v $(PWD):/app \
		docker.io/library/python:3.11-slim \
		bash -c "cd /app && pip install -e .[demo] && python -m morphcards.demo"

# Run demo on custom port
demo-port:
	@echo "🎯 Running MorphCards demo on port 8080..."
	podman run --rm -p 8080:7860 --env-file .env \
		-v $(PWD):/app \
		docker.io/library/python:3.11-slim \
		bash -c "cd /app && pip install -e .[demo] && python -m morphcards.demo"

# Run demo with specific version
demo-version:
	@echo "🎯 Running MorphCards demo with specific version..."
	podman run --rm -p 7860:7860 --env-file .env \
		-v $(PWD):/app \
		docker.io/library/python:3.11-slim \
		bash -c "cd /app && pip install -e .[demo] && python -m morphcards.demo"

# Run tests
test:
	@echo "🌊 Running tests..."
	podman run -q --rm --env-file .env \
		-v $(PWD):/app \
		docker.io/library/python:3.11-slim \
		bash -c "cd /app && pip -q install -e .[dev,demo] && pytest"

# Run mypy
mypy:
	@echo "🔍 Running mypy..."
	podman run --rm \
		-v $(PWD):/app \
		docker.io/library/python:3.11-slim \
		bash -c "cd /app && pip install -e .[dev] && mypy src/morphcards/core.py"

# Run black and isort formatters
format:
	@echo "💅 Running black and isort..."
	podman run --rm \
		-v $(PWD):/app \
		docker.io/library/python:3.11-slim \
		bash -c "cd /app && pip install -e .[dev] && black src/ tests/ && isort src/ tests/"

# Run security scans (Trivy and pip-audit)
audit:
	@echo "🔍 Running security audits (Trivy and pip-audit)..."
	podman run --rm -v $(PWD):/app aquasec/trivy fs --scanners vuln,secret,config --severity HIGH,CRITICAL /app
	podman run --rm -v $(PWD):/app docker.io/library/python:3.11-slim bash -c "cd /app && pip install -e .[dev] && pip-audit"

# Clean up containers and images
clean:
	@echo "🧹 Cleaning up..."
	@podman container prune -f 2>/dev/null || true
	@podman image prune -f 2>/dev/null || true
	@podman rmi morphcards 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Install development dependencies locally
install-dev:
	@echo "📦 Installing development dependencies..."
	python3 -m pip install -e .[dev]
	@echo "✅ Development dependencies installed!"

# Install demo dependencies locally
install-demo:
	@echo "📦 Installing demo dependencies..."
	python3 -m pip install -e .[demo]
	@echo "✅ Demo dependencies installed!"

# Run demo locally (requires local installation)
demo-local: install-demo
	@echo "🎯 Running MorphCards demo locally..."
	python3 -m morphcards.demo

# Quick local demo (installs and runs immediately)
demo-quick:
	@echo "🎯 Quick local demo (installing dependencies)..."
	python3 -m pip install --upgrade pip
	python3 -m pip install -e .[demo]
	@echo "✅ Dependencies installed, starting demo..."
	python3 -m morphcards.demo

# Show container status
status:
	@echo "📊 Container Status:"
	@echo "Running containers:"
	@podman ps --filter "ancestor=morphcards" --format "table {{.Names}}	{{.Status}}	{{.Ports}}" 2>/dev/null || echo "No running containers"
	@echo ""
	@echo "Available images:"
	@podman images morphcards --format "table {{.Repository}}	{{.Tag}}	{{.Size}}" 2>/dev/null || echo "No morphcards images found"

# Check if .env file exists
check-env:
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found!"; \
		echo "Please create a .env file with your API key:"; \
		echo "  GEMINI_API_KEY=your-gemini-api-key-here"; \
		echo "  # or"; \
		echo "  OPENAI_API_KEY=your-openai-api-key-here"; \
		exit 1; \
	fi
	@echo "✅ .env file found"

# Run everything: build, demo, and show status
all: check-env build demo status
	@echo ""
	@echo "🎉 MorphCards is running!"
	@echo "🌐 Open your browser to: http://localhost:7860"
	@echo "📱 Demo interface available at: http://localhost:7860"
	@echo ""
	@echo "To stop the demo, press Ctrl+C"
	@echo "To clean up: make clean"

# Development workflow
dev: check-env install-dev
	@echo "🚀 Development environment ready!"
	@echo "Run tests: make test"
	@echo "Run demo locally: make demo-local"

# Quick start (build and run in background)
quick: check-env build
	@echo "🚀 Starting MorphCards in background..."
	podman run -d --name morphcards-demo -p 7860:7860 --env-file .env morphcards
	@echo "✅ MorphCards running in background!"
	@echo "🌐 Demo available at: http://localhost:7860"
	@echo "To stop: podman stop morphcards-demo"
	@echo "To view logs: podman logs morphcards-demo"

# Stop background containers
stop:
	@echo "🛑 Stopping background containers..."
	@podman stop morphcards-demo 2>/dev/null || echo "No background containers to stop"
	@echo "✅ Stopped!"

# Show logs
logs:
	@echo "📋 Container logs:"
	@podman logs morphcards-demo 2>/dev/null || echo "No logs available (container may not be running)"

# Health check
health:
	@echo "🏥 Health check..."
	@if curl -s http://localhost:7860 > /dev/null; then \
		echo "✅ MorphCards is running and responding"; \
	else \
		echo "❌ MorphCards is not responding"; \
		echo "Check if container is running: make status"; \
	fi
