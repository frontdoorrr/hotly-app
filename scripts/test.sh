#!/bin/bash

set -e
set -x

poetry run pytest --cov=app --cov-report=term-missing app/tests "${@}"