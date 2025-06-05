#!/usr/bin/env bash
# MCP Configuration Transfer: Windsurf → Cursor (Local System)
# Enhanced version with better error handling and validation

set -euo pipefail

# Configuration - Updated with all likely profile locations
profiles=(bootssd-2t User default CachedProfilesData)
declare -g src="" profile="" dest=""
dry_run=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Copy MCP server configurations from Windsurf to Cursor safely.

OPTIONS:
    -d, --dry-run    Show what would be copied without making changes
    -h, --help       Show this help message
    -v, --verbose    Enable verbose output
    -l, --list       List all available settings files

EXAMPLES:
    $0              # Copy MCP configs
    $0 --dry-run    # Preview changes without applying
    $0 --list       # Show all settings files found
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dry-run)
            dry_run=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            set -x
            shift
            ;;
        -l|--list)
            list_mode=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Detect OS and set appropriate config paths
detect_config_paths() {
    case "$(uname -s)" in
        Darwin)  # macOS
            WINDSURF_BASE="$HOME/Library/Application Support/Windsurf"
            CURSOR_BASE="$HOME/Library/Application Support/Cursor"
            ;;
        Linux)
            WINDSURF_BASE="$HOME/.config/Windsurf"
            CURSOR_BASE="$HOME/.config/Cursor"
            ;;
        CYGWIN*|MINGW32*|MSYS*|MINGW*)  # Windows
            WINDSURF_BASE="$APPDATA/Windsurf"
            CURSOR_BASE="$APPDATA/Cursor"
            ;;
        *)
            log_error "Unsupported operating system: $(uname -s)"
            exit 1
            ;;
    esac
    
    log_info "Detected OS: $(uname -s)"
    log_info "Windsurf config path: $WINDSURF_BASE"
    log_info "Cursor config path: $CURSOR_BASE"
    
    # Verify paths exist
    if [[ ! -d "$WINDSURF_BASE" ]]; then
        log_error "Windsurf configuration directory not found: $WINDSURF_BASE"
        exit 1
    fi
    
    if [[ ! -d "$CURSOR_BASE" ]]; then
        log_error "Cursor configuration directory not found: $CURSOR_BASE"
        exit 1
    fi
}

# Check if required tools are available
check_dependencies() {
    local missing_tools=()
    
    for tool in jq; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install missing tools:"
        for tool in "${missing_tools[@]}"; do
            case "$tool" in
                jq)
                    log_info "  - Install jq: sudo apt-get install jq (Ubuntu/Debian)"
                    log_info "  - Install jq: sudo yum install jq (CentOS/RHEL)"
                    log_info "  - Install jq: brew install jq (macOS)"
                    ;;
            esac
        done
        exit 1
    fi
}

# List all settings files for debugging
list_all_settings() {
    log_info "=== WINDSURF SETTINGS FILES ==="
    find "$WINDSURF_BASE" -name "settings.json" -type f 2>/dev/null | while read -r f; do
        echo "  📄 $f"
        if [[ -r "$f" ]] && jq -e '.mcpServers' "$f" &>/dev/null; then
            echo "    ✅ Contains mcpServers"
            jq -r '.mcpServers | keys[]' "$f" 2>/dev/null | sed 's/^/      • /'
        else
            echo "    ❌ No mcpServers found"
        fi
    done
    
    log_info "=== CURSOR SETTINGS FILES ==="
    find "$CURSOR_BASE" -name "settings.json" -type f 2>/dev/null | while read -r f; do
        echo "  📄 $f"
        if [[ -r "$f" ]] && jq -e '.mcpServers' "$f" &>/dev/null; then
            echo "    ✅ Contains mcpServers"
            jq -r '.mcpServers | keys[]' "$f" 2>/dev/null | sed 's/^/      • /'
        else
            echo "    ❌ No mcpServers found"
        fi
    done
}

# Enhanced search for Windsurf settings with mcpServers configuration
find_windsurf_mcp_config() {
    log_info "Searching for Windsurf MCP configurations..."
    
    # First, search all possible profile locations
    local search_paths=(
        "$WINDSURF_BASE/User/settings.json"
        "$WINDSURF_BASE/bootssd-2t/settings.json"
        "$WINDSURF_BASE/bootssd-2t/User/settings.json"
        "$WINDSURF_BASE/settings.json"
    )
    
    # Also do a recursive search for any settings.json with mcpServers
    while IFS= read -r -d '' f; do
        search_paths+=("$f")
    done < <(find "$WINDSURF_BASE" -name "settings.json" -type f -print0 2>/dev/null)
    
    # Remove duplicates
    local unique_paths=($(printf '%s\n' "${search_paths[@]}" | sort -u))
    
    for f in "${unique_paths[@]}"; do
        if [[ -f "$f" && -r "$f" ]]; then
            log_info "Checking: $f"
            if jq -e '.mcpServers' "$f" &>/dev/null && [[ $(jq '.mcpServers | length' "$f" 2>/dev/null) -gt 0 ]]; then
                src="$f"
                # Extract profile name from path
                profile=$(echo "$f" | sed "s|$WINDSURF_BASE/||" | sed 's|/.*||')
                [[ "$profile" == "settings.json" ]] && profile="root"
                log_success "Found MCP configuration in: $f"
                log_info "Profile identified as: $profile"
                return 0
            else
                log_info "  No mcpServers or empty mcpServers in: $f"
            fi
        fi
    done
    
    log_error "No mcpServers configuration found in any Windsurf settings"
    log_info "Searched locations under: $WINDSURF_BASE"
    return 1
}

# Validate JSON structure
validate_json() {
    local file="$1"
    if [[ ! -r "$file" ]]; then
        log_error "Cannot read file: $file"
        return 1
    fi
    
    if ! jq empty "$file" 2>/dev/null; then
        log_error "Invalid JSON in file: $file"
        return 1
    fi
    return 0
}

# Show MCP configuration preview
show_mcp_preview() {
    log_info "MCP Servers found in Windsurf ($src):"
    echo "----------------------------------------"
    if jq -e '.mcpServers' "$src" &>/dev/null; then
        jq -r '.mcpServers | to_entries[] | "  • \(.key): \(.value.command // .value.args[0] // "unknown command")"' "$src" 2>/dev/null || {
            log_warning "Could not parse MCP servers for detailed preview"
            jq '.mcpServers | keys[]' "$src" 2>/dev/null | sed 's/^/  • /'
        }
    else
        log_warning "No mcpServers found in source file"
    fi
    echo "----------------------------------------"
}

# Create destination path and backup
prepare_cursor_settings() {
    # Try to find the best matching profile in Cursor
    local cursor_profiles=(
        "$CURSOR_BASE/User/settings.json"
        "$CURSOR_BASE/bootssd-2t/settings.json"
        "$CURSOR_BASE/bootssd-2t/User/settings.json"
        "$CURSOR_BASE/settings.json"
    )
    
    # If we have a specific profile from Windsurf, try to match it
    if [[ "$profile" != "root" && "$profile" != "" ]]; then
        dest="$CURSOR_BASE/$profile/settings.json"
        # Check if User subfolder exists in this profile
        if [[ -f "$CURSOR_BASE/$profile/User/settings.json" ]]; then
            dest="$CURSOR_BASE/$profile/User/settings.json"
        fi
    else
        # Default to User settings
        dest="$CURSOR_BASE/User/settings.json"
    fi
    
    local dest_dir
    dest_dir="$(dirname "$dest")"
    
    log_info "Target destination: $dest"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY-RUN] Would create directory: $dest_dir"
        log_info "[DRY-RUN] Would prepare destination file: $dest"
        return 0
    fi
    
    # Create destination directory
    mkdir -p "$dest_dir"
    log_success "Created destination directory: $dest_dir"
    
    # Create backup if destination exists
    if [[ -f "$dest" ]]; then
        local ts backup_file
        ts=$(date +%Y%m%d-%H%M%S)
        backup_file="${dest}.bak-$ts"
        cp "$dest" "$backup_file"
        log_success "Backup created: $backup_file"
    else
        log_info "No existing Cursor settings file found, creating new one"
        echo '{}' > "$dest"
    fi
}

# Perform the MCP configuration copy
copy_mcp_config() {
    local temp_file="${dest}.tmp"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY-RUN] Would copy MCP configuration from:"
        log_info "[DRY-RUN]   Source: $src"
        log_info "[DRY-RUN]   Dest:   $dest"
        return 0
    fi
    
    # Validate source JSON
    validate_json "$src" || {
        log_error "Source file has invalid JSON structure"
        return 1
    }
    
    # Validate destination JSON
    validate_json "$dest" || {
        log_error "Destination file has invalid JSON structure"
        return 1
    }
    
    # Extract MCP servers and merge
    log_info "Merging MCP configuration..."
    if jq --slurpfile mcp_servers <(jq '.mcpServers' "$src") \
       '.mcpServers = $mcp_servers[0]' \
       "$dest" > "$temp_file" 2>/dev/null; then
        
        # Validate the merged result
        if validate_json "$temp_file"; then
            mv "$temp_file" "$dest"
            log_success "MCP configuration successfully copied to Cursor"
        else
            log_error "Merged configuration is invalid JSON"
            rm -f "$temp_file"
            return 1
        fi
    else
        log_error "Failed to merge MCP configuration"
        rm -f "$temp_file"
        return 1
    fi
}

# Verify the copy was successful
verify_copy() {
    if [[ "$dry_run" == "true" ]]; then
        return 0
    fi
    
    log_info "Verifying copy..."
    
    if jq -e '.mcpServers' "$dest" &>/dev/null; then
        local src_count dest_count
        src_count=$(jq '.mcpServers | length' "$src")
        dest_count=$(jq '.mcpServers | length' "$dest")
        
        if [[ "$src_count" == "$dest_count" ]]; then
            log_success "Verification passed: $dest_count MCP servers copied"
        else
            log_warning "Server count mismatch: source=$src_count, destination=$dest_count"
        fi
        
        log_info "MCP Servers now in Cursor:"
        jq -r '.mcpServers | to_entries[] | "  • \(.key)"' "$dest" 2>/dev/null || echo "  (Could not list server names)"
    else
        log_error "Verification failed: No mcpServers found in destination"
        return 1
    fi
}

# Main execution
main() {
    log_info "Starting MCP configuration transfer: Windsurf → Cursor"
    
    if [[ "$dry_run" == "true" ]]; then
        log_warning "DRY-RUN MODE: No changes will be made"
    fi
    
    # Pre-flight checks
    detect_config_paths
    check_dependencies
    
    # If list mode, show all settings and exit
    if [[ "${list_mode:-false}" == "true" ]]; then
        list_all_settings
        exit 0
    fi
    
    # Find and process MCP configuration
    find_windsurf_mcp_config || exit 1
    show_mcp_preview
    
    # Prepare destination
    prepare_cursor_settings
    
    # Perform copy
    copy_mcp_config
    
    # Verify result
    verify_copy
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY-RUN completed. Run without --dry-run to apply changes."
    else
        log_success "MCP configuration transfer completed successfully!"
        log_info "You may need to restart Cursor for changes to take effect."
    fi
}

# Error handling
trap 'log_error "Script failed at line $LINENO"' ERR

# Run main function
main "$@" 