#!/bin/bash
# Setup pre-commit for ShellCast project
# This script installs pre-commit in both analysis and web environments

set -e

echo "🔧 Setting up pre-commit for ShellCast project..."

# Check if pre-commit is installed globally
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit globally..."
    pip install pre-commit
else
    echo "✅ pre-commit is already installed globally"
fi

# Check if shellcheck is available (optional)
if command -v shellcheck &> /dev/null; then
    echo "✅ shellcheck is available for shell script linting"
else
    echo "⚠️  shellcheck not found - shell script linting will be skipped"
    echo "   Install with: brew install shellcheck (macOS) or apt-get install shellcheck (Ubuntu)"
fi

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

# Install pre-commit in analysis environment
echo "🐍 Installing pre-commit in analysis environment..."
cd analysis/shellcast-analysis
source analysisenv/bin/activate
pip install pre-commit
deactivate
cd ../..

# Install pre-commit in web environment
echo "🌐 Installing pre-commit in web environment..."
cd web
source webvenv/bin/activate
pip install pre-commit
deactivate
cd ..

echo "✅ Pre-commit setup complete!"
echo ""
echo "📋 Usage:"
echo "  # Run pre-commit on all files"
echo "  pre-commit run --all-files"
echo ""
echo "  # Run pre-commit on staged files only"
echo "  git commit"
echo ""
echo "  # Update pre-commit hooks"
echo "  pre-commit autoupdate"
echo ""
echo "  # Skip pre-commit for a commit (not recommended)"
echo "  git commit --no-verify"
