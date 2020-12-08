#! /bin/bash

# Blacken all files
black *.py

# Type check all files
mypy *.py --ignore-missing-imports

# Lint all files
find . -name "*.py" | xargs pylint