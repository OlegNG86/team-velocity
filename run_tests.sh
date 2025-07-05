#!/bin/bash
# Script to run tests with the test environment

# Set the environment file to use for tests
export PYTHONPATH=$PYTHONPATH:$(pwd)
export DOTENV_PATH=tests/.env.test

# Run the tests
pytest -v "$@"
