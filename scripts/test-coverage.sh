#!/bin/bash
# Generate test coverage report with HTML output

set -e
set -x

echo "Running tests with coverage..."
poetry run pytest tests/ --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=80 -v

echo "Coverage report generated in htmlcov/"
echo "Open htmlcov/index.html to view detailed coverage report"
