#!/bin/bash

# ShellCast Enhanced Staging Cleanup Script
# This script cleans up Google Cloud Storage staging files after App Engine deployment
# Supports multiple projects and provides comprehensive cleanup options

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

# Function to check if gcloud is installed and authenticated
check_gcloud_setup() {
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi

    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not authenticated with gcloud. Please run 'gcloud auth login' first."
        exit 1
    fi
}

# Function to get project name
get_project_name() {
    local project_name
    project_name=$(gcloud config get-value project 2>/dev/null)

    if [ -z "$project_name" ]; then
        print_error "No project configured. Please run 'gcloud config set project PROJECT_NAME' first."
        exit 1
    fi

    echo "$project_name"
}

# Function to clean staging files for a specific project
clean_staging_for_project() {
    local project_name="$1"
    local force_cleanup="$2"

    local staging_bucket="staging.$project_name.appspot.com"

    print_status "Project: $project_name"
    print_status "Staging bucket: $staging_bucket"

    # Check if staging bucket exists
    if ! gsutil ls "gs://$staging_bucket" &> /dev/null; then
        print_warning "Staging bucket $staging_bucket does not exist or is not accessible."
        return 0
    fi

    if [ "$force_cleanup" != "true" ]; then
        print_warning "This will delete ALL files in $staging_bucket"
        print_warning "You will need to use 'gcloud app deploy --no-cache' for next deployment"

        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo

        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Operation cancelled for $project_name"
            return 0
        fi
    fi

    print_status "Deleting staging files for $project_name..."

    # Delete all files in staging bucket
    if gsutil -m rm "gs://$staging_bucket/**" 2>/dev/null; then
        print_status "Staging files deleted successfully for $project_name!"
    else
        print_warning "No files found in staging bucket for $project_name or bucket is empty"
    fi
}

# Function to clean specific staging directories
clean_specific_staging_dirs() {
    local project_name="$1"
    local staging_bucket="staging.$project_name.appspot.com"

    print_status "Cleaning specific staging directories for $project_name..."

    # Common staging directories to clean
    local dirs=("containers/images" "app" "source-contexts" "temp")

    for dir in "${dirs[@]}"; do
        local path="gs://$staging_bucket/$dir"
        if gsutil ls "$path" &> /dev/null; then
            print_status "Cleaning $dir..."
            if gsutil -m rm -r "$path/**" 2>/dev/null; then
                print_status "Cleaned $dir successfully"
            fi
        else
            print_status "Directory $dir does not exist or is empty"
        fi
    done
}

# Function to list staging files (for verification)
list_staging_files() {
    local project_name="$1"
    local staging_bucket="staging.$project_name.appspot.com"

    print_status "Listing staging files for $project_name..."

    if gsutil ls "gs://$staging_bucket" &> /dev/null; then
        gsutil ls -r "gs://$staging_bucket" | head -20
        echo "..."
    else
        print_warning "Staging bucket $staging_bucket does not exist or is not accessible."
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --project PROJECT_NAME    Specify project name (default: current gcloud project)"
    echo "  -f, --force                   Force cleanup without confirmation"
    echo "  -l, --list                    List staging files instead of deleting"
    echo "  -s, --specific                Clean only specific staging directories"
    echo "  -a, --all-projects           Clean staging for all known ShellCast projects"
    echo "  -h, --help                    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Clean staging for current project with confirmation"
    echo "  $0 -f                        # Force clean staging for current project"
    echo "  $0 -p ncsu-shellcast         # Clean staging for specific project"
    echo "  $0 -l                        # List staging files for current project"
    echo "  $0 -s                        # Clean specific staging directories only"
    echo "  $0 -a                        # Clean staging for all ShellCast projects"
}

# Main script logic
main() {
    local project_name=""
    local force_cleanup=false
    local list_files=false
    local specific_dirs=false
    local all_projects=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--project)
                project_name="$2"
                shift 2
                ;;
            -f|--force)
                force_cleanup=true
                shift
                ;;
            -l|--list)
                list_files=true
                shift
                ;;
            -s|--specific)
                specific_dirs=true
                shift
                ;;
            -a|--all-projects)
                all_projects=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    print_header "ShellCast Staging Cleanup Script"

    # Check gcloud setup
    check_gcloud_setup

    # Handle all projects option
    if [ "$all_projects" = true ]; then
        local projects=("ncsu-shellcast" "shellcast-fl" "shellcast-nc" "shellcast-sc")

        for proj in "${projects[@]}"; do
            echo ""
            print_header "Processing project: $proj"

            if [ "$list_files" = true ]; then
                list_staging_files "$proj"
            elif [ "$specific_dirs" = true ]; then
                clean_specific_staging_dirs "$proj"
            else
                clean_staging_for_project "$proj" "$force_cleanup"
            fi
        done

        print_status "Completed processing all projects"
        exit 0
    fi

    # Get project name if not specified
    if [ -z "$project_name" ]; then
        project_name=$(get_project_name)
    fi

    # Execute based on options
    if [ "$list_files" = true ]; then
        list_staging_files "$project_name"
    elif [ "$specific_dirs" = true ]; then
        clean_specific_staging_dirs "$project_name"
    else
        clean_staging_for_project "$project_name" "$force_cleanup"
    fi

    print_status "Operation completed successfully!"

    if [ "$force_cleanup" != true ] && [ "$list_files" != true ] && [ "$specific_dirs" != true ]; then
        print_warning "Remember to use 'gcloud app deploy --no-cache' for next deployment"
    fi
}

# Run main function with all arguments
main "$@"
