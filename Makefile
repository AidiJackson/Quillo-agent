.PHONY: run migrate revision test install clean

# Get APP_PORT from environment or default to 8000
APP_PORT ?= 8000

# Run the application
run:
	uvicorn app:app --reload --port $(APP_PORT)

# Run Alembic migrations
migrate:
	alembic upgrade head

# Create a new Alembic revision
revision:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG is required. Usage: make revision MSG='your message'"; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(MSG)"

# Run tests
test:
	pytest -q

# Install dependencies
install:
	pip install -r requirements.txt

# Clean up generated files
clean:
	rm -rf __pycache__ .pytest_cache logs/ *.db
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Create logs directory
logs:
	mkdir -p logs

# Setup (install + migrate)
setup: install migrate logs
	@echo "✅ Setup complete! Run 'make run' to start the server."
