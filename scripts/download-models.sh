#!/bin/bash
set -euo pipefail

# Model download script for kanoa-mlops
# Usage: ./download-models.sh [model-name]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_DIR="${MODELS_DIR:-$HOME/.cache/kanoa/models}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    if ! command -v huggingface-cli &> /dev/null; then
        log_error "huggingface-cli not found. Install with: pip install huggingface-hub"
        exit 1
    fi
}

download_molmo() {
    local variant="$1"
    local model_id
    local output_dir

    case "$variant" in
        molmo-7b-d|7b-d)
            model_id="allenai/Molmo-7B-D-0924"
            output_dir="$MODELS_DIR/molmo"
            ;;
        molmo-7b-o|7b-o)
            model_id="allenai/Molmo-7B-O-0924"
            output_dir="$MODELS_DIR/molmo-7b-o"
            ;;
        molmoe-1b|1b)
            model_id="allenai/MolmoE-1B-0924"
            output_dir="$MODELS_DIR/molmoe-1b"
            ;;
        gemma-3-4b|g3-4b)
            model_id="google/gemma-3-4b-it"
            output_dir="$MODELS_DIR/gemma-3-4b"
            ;;
        gemma-3-12b|g3-12b)
            model_id="google/gemma-3-12b-it"
            output_dir="$MODELS_DIR/gemma-3-12b"
            ;;
        gemma-3-27b|g3-27b)
            model_id="google/gemma-3-27b-it"
            output_dir="$MODELS_DIR/gemma-3-27b"
            ;;
        *)
            log_error "Unknown model variant: $variant"
            echo "Available variants:"
            echo "  - Molmo: molmo-7b-d, molmo-7b-o, molmoe-1b"
            echo "  - Gemma 3: gemma-3-4b, gemma-3-12b, gemma-3-27b"
            exit 1
            ;;
    esac

    log_info "Downloading $model_id to $output_dir"
    
    mkdir -p "$output_dir"
    
    huggingface-cli download "$model_id" \
        --local-dir "$output_dir" \
        --local-dir-use-symlinks False
    
    log_info "✓ Downloaded $model_id"
    log_info "Model location: $output_dir"
    log_info ""
    log_info "To use with vLLM, set:"
    log_info "  export MOLMO_MODEL_PATH=$output_dir"
}

show_usage() {
    cat << EOF
Usage: $0 [model-name]

Download models for kanoa-mlops.

Available models:
  molmo-7b-d    Molmo 7B Dense (default, recommended)
  molmo-7b-o    Molmo 7B Optimized
  molmoe-1b     MolmoE 1B (efficient variant)
  gemma-3-4b    Gemma 3 4B (Multimodal)
  gemma-3-12b   Gemma 3 12B (Multimodal, recommended)
  gemma-3-27b   Gemma 3 27B (High performance)

Environment variables:
  MODELS_DIR    Base directory for models (default: ~/.cache/kanoa/models)

Examples:
  $0 molmo-7b-d
  MODELS_DIR=/data/models $0 molmo-7b-d
EOF
}

main() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 0
    fi

    check_dependencies

    case "$1" in
        -h|--help)
            show_usage
            exit 0
            ;;
        molmo-*|gemma-3-*|*b-*|*b)
            download_molmo "$1"
            ;;
        *)
            log_error "Unknown model: $1"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
