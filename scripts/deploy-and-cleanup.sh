#!/bin/bash

# ShellCast Deploy Script
# This script deploys to Google App Engine.
# NOTE: Staging bucket cleanup was removed from this script (it could hang).
# The standalone cleanup-staging*.sh scripts can still be run manually if needed.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 -d DIR [DEPLOY_OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --directory DIR          Specify the web app directory to deploy"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "Deploy Options:"
    echo "  --no-promote                Deploy without promoting traffic"
    echo "  --no-cache                  Deploy without using cached files"
    echo "  --version VERSION           Deploy specific version"
    echo ""
    echo "Examples:"
    echo "  $0 -d web/shellcast-web-fl                    # Deploy FL app"
    echo "  $0 -d web/shellcast-web-nc --no-promote       # Deploy NC app without promoting"
}

# Function to check if directory exists and contains app.yaml
check_deploy_directory() {
    local dir="$1"

    if [ ! -d "$dir" ]; then
        print_error "Directory $dir does not exist"
        exit 1
    fi

    if [ ! -f "$dir/app.yaml" ]; then
        print_error "Directory $dir does not contain app.yaml"
        exit 1
    fi

    print_status "Deploy directory validated: $dir"
}

# Function to deploy to App Engine
deploy_app() {
    local deploy_dir="$1"
    local deploy_opts="$2"

    print_header "Deploying to Google App Engine"
    print_status "Deploy directory: $deploy_dir"

    # Change to deploy directory
    cd "$deploy_dir"

    # Build deployment command
    local deploy_cmd="gcloud app deploy"

    if [ -n "$deploy_opts" ]; then
        deploy_cmd="$deploy_cmd $deploy_opts"
    fi

    print_status "Running: $deploy_cmd"

    # Execute deployment
    if eval "$deploy_cmd"; then
        print_status "Deployment completed successfully!"
    else
        print_error "Deployment failed!"
        exit 1
    fi

    # Return to original directory
    cd - > /dev/null
}

# Main script logic
main() {
    local deploy_dir=""
    local deploy_opts=""

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--directory)
                deploy_dir="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            --no-promote|--no-cache|--version)
                deploy_opts="$deploy_opts $1"
                if [[ $1 == --version ]]; then
                    deploy_opts="$deploy_opts $2"
                    shift
                fi
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    print_header "ShellCast Deploy Script"

    # Check if gcloud is available
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi

    # Validate deploy directory
    if [ -z "$deploy_dir" ]; then
        print_error "Deploy directory is required. Use -d option or --help for usage."
        exit 1
    fi

    check_deploy_directory "$deploy_dir"

    # Deploy the application
    deploy_app "$deploy_dir" "$deploy_opts"

    print_status "Deploy process completed successfully!"
}

# Run main function with all arguments
main "$@"
