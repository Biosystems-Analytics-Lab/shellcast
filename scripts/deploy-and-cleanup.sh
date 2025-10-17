#!/bin/bash

# ShellCast Deploy and Cleanup Script
# This script deploys to Google App Engine and then cleans up staging files

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
    echo "Usage: $0 [OPTIONS] [DEPLOY_OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --directory DIR          Specify the web app directory to deploy"
    echo "  -p, --project PROJECT_NAME   Specify project name (default: current gcloud project)"
    echo "  -f, --force                  Force cleanup without confirmation"
    echo "  -n, --no-cleanup            Skip staging cleanup after deployment"
    echo "  -c, --cleanup-only          Only run cleanup, skip deployment"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "Deploy Options:"
    echo "  --no-promote                Deploy without promoting traffic"
    echo "  --no-cache                  Deploy without using cached files"
    echo "  --version VERSION           Deploy specific version"
    echo ""
    echo "Examples:"
    echo "  $0 -d web/shellcast-web-fl                    # Deploy FL app and cleanup"
    echo "  $0 -d web/shellcast-web-nc --no-promote       # Deploy NC app without promoting"
    echo "  $0 -d web/shellcast-web-sc -f                 # Deploy SC app with force cleanup"
    echo "  $0 -c -p ncsu-shellcast                       # Only cleanup staging"
    echo "  $0 -n -d web/shellcast-web-fl                 # Deploy without cleanup"
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

# Function to run cleanup
run_cleanup() {
    local project_name="$1"
    local force_cleanup="$2"

    print_header "Running Staging Cleanup"

    # Get the directory of this script
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local cleanup_script="$script_dir/cleanup-staging-enhanced.sh"

    if [ ! -f "$cleanup_script" ]; then
        print_error "Cleanup script not found: $cleanup_script"
        exit 1
    fi

    # Build cleanup command
    local cleanup_cmd="$cleanup_script"

    if [ -n "$project_name" ]; then
        cleanup_cmd="$cleanup_cmd -p $project_name"
    fi

    if [ "$force_cleanup" = true ]; then
        cleanup_cmd="$cleanup_cmd -f"
    fi

    print_status "Running: $cleanup_cmd"

    # Execute cleanup
    if eval "$cleanup_cmd"; then
        print_status "Cleanup completed successfully!"
    else
        print_error "Cleanup failed!"
        exit 1
    fi
}

# Main script logic
main() {
    local deploy_dir=""
    local project_name=""
    local force_cleanup=false
    local skip_cleanup=false
    local cleanup_only=false
    local deploy_opts=""

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--directory)
                deploy_dir="$2"
                shift 2
                ;;
            -p|--project)
                project_name="$2"
                shift 2
                ;;
            -f|--force)
                force_cleanup=true
                shift
                ;;
            -n|--no-cleanup)
                skip_cleanup=true
                shift
                ;;
            -c|--cleanup-only)
                cleanup_only=true
                shift
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

    print_header "ShellCast Deploy and Cleanup Script"

    # Check if gcloud is available
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi

    # Handle cleanup-only mode
    if [ "$cleanup_only" = true ]; then
        run_cleanup "$project_name" "$force_cleanup"
        exit 0
    fi

    # Validate deploy directory
    if [ -z "$deploy_dir" ]; then
        print_error "Deploy directory is required. Use -d option or --help for usage."
        exit 1
    fi

    check_deploy_directory "$deploy_dir"

    # Deploy the application
    deploy_app "$deploy_dir" "$deploy_opts"

    # Run cleanup if not skipped
    if [ "$skip_cleanup" != true ]; then
        echo ""
        run_cleanup "$project_name" "$force_cleanup"
    else
        print_warning "Skipping staging cleanup as requested"
    fi

    print_status "Deploy and cleanup process completed successfully!"
}

# Run main function with all arguments
main "$@"
