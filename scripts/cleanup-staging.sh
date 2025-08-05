#!/bin/bash

# ShellCast Staging Cleanup Script
# This script cleans up Google App Engine staging storage

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get project name from gcloud config
PROJECT_NAME=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_NAME" ]; then
    print_error "No project configured. Please run 'gcloud config set project PROJECT_NAME' first."
    exit 1
fi

print_status "Project: $PROJECT_NAME"
print_warning "This will delete ALL files in staging.$PROJECT_NAME.appspot.com"
print_warning "You will need to use 'gcloud app deploy --no-cache' for next deployment"

read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Deleting staging files..."
    
    if gsutil -m rm "gs://staging.$PROJECT_NAME.appspot.com/**"; then
        print_status "Staging files deleted successfully!"
        print_status "Remember to use 'gcloud app deploy --no-cache' for next deployment"
    else
        print_error "Failed to delete staging files"
        exit 1
    fi
else
    print_status "Operation cancelled"
fi 