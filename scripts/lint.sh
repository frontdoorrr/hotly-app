#!/bin/bash

set -e
set -x

poetry run mypy app
poetry run black app tests --check
poetry run isort app tests --check-only
poetry run flake8 app tests
poetry run bandit -r app -c bandit.yaml