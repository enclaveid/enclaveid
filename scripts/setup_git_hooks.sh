#!/bin/bash

# File: setup-git-hooks.sh

echo "Setting up Git hooks..."

# Ensure the hooks directory exists
mkdir -p .git/hooks

# Copy the pre-commit hook
cp scripts/git-hooks/pre-commit .git/hooks/pre-commit

# Make the hook executable
chmod +x .git/hooks/pre-commit

echo "Git hooks setup completed."
