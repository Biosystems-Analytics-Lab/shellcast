#!/usr/bin/env bash
# Florida analysis dev setup — wgrib2 (required for NC/SC/FL PQPF crop + FL xmrg_proc.sh)
# and optional Homebrew / cnvgrib helpers for xmrg_proc.sh.
#
# Run from anywhere:
#   ./analysis/shellcast-analysis/setup-florida-dev.sh
#   ./analysis/shellcast-analysis/setup-florida-dev.sh --wgrib2
#   ./analysis/shellcast-analysis/setup-florida-dev.sh --all
#   ./analysis/shellcast-analysis/setup-florida-dev.sh --wgrib2 --brew-tools
#
# wgrib2: clones https://github.com/NOAA-EMC/wgrib2 into this directory, builds with CMake,
# and installs the binary so cron and subprocess calls can find it.
#
# On macOS, pqpf_procs.py uses /usr/local/bin/wgrib2 (see src/pqpf_procs.py). This script
# installs there by default. Override with INSTALL_PREFIX if needed.
#
# Prerequisites (install before running — see docs/analysis/01-GETTING_STARTED.md §5.1):
#   - C compiler: Xcode Command Line Tools (cc) and/or: brew install gcc
#   - cmake: brew install cmake
#   - make, git
#
# After build, the command must be installed as /usr/local/bin/wgrib2 (not only
# wgrib2/build/src/wgrib2) so cron and pqpf_procs.py can find it — §5.3–5.4.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
WGRIB2_REPO="${WGRIB2_REPO:-https://github.com/NOAA-EMC/wgrib2.git}"
WGRIB2_DIR="${WGRIB2_DIR:-$ROOT/wgrib2}"
WGRIB2_TAG="${WGRIB2_TAG:-}" # e.g. v3.8.0 from release; empty = default branch
INSTALL_PREFIX="${INSTALL_PREFIX:-/usr/local}"
JOBS="${JOBS:-$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)}"

INSTALL_WGRIB2=0
INSTALL_BREW_TOOLS=0
INSTALL_CNvgrib=0
FLAG_WGRIB2=0
FLAG_ALL=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

  (no options)   Same as --wgrib2 (clone, build, install wgrib2)

Options:
  --wgrib2       Clone, build, and install wgrib2 to ${INSTALL_PREFIX}/bin/wgrib2
  --all          --wgrib2 + --brew-tools + --cnvgrib
  --brew-tools   brew install cdo gdal (+ cnvgrib build deps)
  --cnvgrib      Run ncep-lib-utils/ncep_lib_utils.sh (needs brew deps first)
  -h, --help     Show this help

Flags are composable, e.g. --wgrib2 --brew-tools

Environment:
  INSTALL_PREFIX   Install root (default: /usr/local)
  WGRIB2_DIR       Clone directory (default: $ROOT/wgrib2)
  WGRIB2_TAG       Git tag to checkout after clone (e.g. v3.8.0)
  JOBS             Parallel make jobs (default: ${JOBS})

After wgrib2 install, verify:
  ${INSTALL_PREFIX}/bin/wgrib2
  wgrib2 -version   # if ${INSTALL_PREFIX}/bin is on PATH

Cron note: xmrg_proc.sh expects wgrib2 on PATH (/usr/local/bin is prepended).
           pqpf_procs.py on macOS calls /usr/local/bin/wgrib2 explicitly.
EOF
}

log() { printf '==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

for arg in "$@"; do
  case "$arg" in
    --all) FLAG_ALL=1 ;;
    --wgrib2) FLAG_WGRIB2=1 ;;
    --brew-tools) INSTALL_BREW_TOOLS=1 ;;
    --cnvgrib) INSTALL_CNvgrib=1 ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ $# -eq 0 ]]; then
  INSTALL_WGRIB2=1
elif [[ "$FLAG_ALL" -eq 1 ]]; then
  INSTALL_WGRIB2=1
  INSTALL_BREW_TOOLS=1
  INSTALL_CNvgrib=1
else
  [[ "$FLAG_WGRIB2" -eq 1 ]] && INSTALL_WGRIB2=1
  if [[ "$INSTALL_WGRIB2" -eq 0 && "$INSTALL_BREW_TOOLS" -eq 0 && "$INSTALL_CNvgrib" -eq 0 ]]; then
    die "No install steps selected. Use --wgrib2, --brew-tools, --cnvgrib, or --all (see --help)."
  fi
fi

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

ensure_build_prereqs() {
  require_cmd make
  require_cmd git
  if ! command -v cc >/dev/null 2>&1 && ! command -v gcc >/dev/null 2>&1; then
    die "C compiler required (cc or gcc). On macOS: xcode-select --install  OR  brew install gcc"
  fi
  if command -v cmake >/dev/null 2>&1; then
    return 0
  fi
  if command -v brew >/dev/null 2>&1; then
    log "cmake not found; installing via Homebrew..."
    brew install cmake
    return 0
  fi
  die "cmake is required (3.15+). Install with: brew install cmake"
}

clone_wgrib2() {
  if [[ -d "$WGRIB2_DIR/.git" ]]; then
    log "Updating existing wgrib2 clone at $WGRIB2_DIR"
    git -C "$WGRIB2_DIR" fetch --tags origin
  else
    log "Cloning $WGRIB2_REPO into $WGRIB2_DIR"
    git clone "$WGRIB2_REPO" "$WGRIB2_DIR"
  fi
  if [[ -n "$WGRIB2_TAG" ]]; then
    log "Checking out tag $WGRIB2_TAG"
    git -C "$WGRIB2_DIR" checkout "$WGRIB2_TAG"
  fi
}

build_install_wgrib2() {
  local build_dir="$WGRIB2_DIR/build"
  log "Configuring wgrib2 (CMake) — minimal build without g2c/netcdf"
  rm -rf "$build_dir"
  mkdir -p "$build_dir"
  cd "$build_dir"
  cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX" \
    -DUSE_G2CLIB=OFF \
    -DUSE_NETCDF=OFF \
    -DUSE_IPOLATES=OFF \
    -G "Unix Makefiles"

  log "Building wgrib2 (-j${JOBS})..."
  make -j"$JOBS"

  log "Installing wgrib2 to ${INSTALL_PREFIX}/bin (may prompt for sudo)..."
  if mkdir -p "$INSTALL_PREFIX/bin" 2>/dev/null && [[ -w "$INSTALL_PREFIX" ]]; then
    make install
  else
    sudo mkdir -p "$INSTALL_PREFIX/bin"
    sudo make install
  fi

  local installed="$INSTALL_PREFIX/bin/wgrib2"
  [[ -x "$installed" ]] || die "Expected binary not found after install: $installed"

  # pqpf_procs.py on Darwin hard-codes /usr/local/bin/wgrib2
  if [[ "$(uname -s)" == "Darwin" && "$installed" != "/usr/local/bin/wgrib2" ]]; then
    log "Linking /usr/local/bin/wgrib2 -> $installed (macOS pqpf_procs.py expects this path)"
    if sudo mkdir -p /usr/local/bin && sudo ln -sf "$installed" /usr/local/bin/wgrib2; then
      installed="/usr/local/bin/wgrib2"
    else
      die "Could not link /usr/local/bin/wgrib2. Re-run with INSTALL_PREFIX=/usr/local or create the symlink manually."
    fi
  fi

  log "wgrib2 installed:"
  "$installed" 2>&1 | head -3
}

install_cnvgrib_brew_deps() {
  command -v brew >/dev/null 2>&1 || die "Homebrew required for --cnvgrib (jasper, libpng, zlib, openblas, gcc)"
  command -v gfortran >/dev/null 2>&1 || die "gfortran required for cnvgrib (brew install gcc)"
  log "Installing cnvgrib build dependencies (jasper, libpng, zlib, openblas)"
  brew install jasper libpng zlib openblas
}

install_brew_tools() {
  command -v brew >/dev/null 2>&1 || die "Homebrew required for --brew-tools / --all"
  log "Installing CDO and GDAL (Florida xmrg_proc.sh)"
  brew install cdo gdal
  install_cnvgrib_brew_deps
}

install_cnvgrib() {
  install_cnvgrib_brew_deps
  local ncep_script="$ROOT/ncep-lib-utils/ncep_lib_utils.sh"
  [[ -f "$ncep_script" ]] || die "Not found: $ncep_script"
  log "Building cnvgrib via ncep_lib_utils.sh (run from ncep-lib-utils/)"
  chmod +x "$ncep_script"
  (cd "$ROOT/ncep-lib-utils" && ./ncep_lib_utils.sh)
  local cnvgrib="$ROOT/ncep-lib-utils/nceplibs/bin/cnvgrib"
  [[ -x "$cnvgrib" ]] || die "cnvgrib build finished but binary missing: $cnvgrib"
  chmod +x "$cnvgrib"
  log "cnvgrib ready: $cnvgrib"
}

chmod_fl_scripts() {
  local xmrg="$ROOT/src/fl_pqpf/xmrg_proc.sh"
  if [[ -f "$xmrg" ]]; then
    chmod +x "$xmrg"
    log "chmod +x $xmrg"
  fi
}

main() {
  log "ShellCast Florida dev setup (root: $ROOT)"

  if [[ "$INSTALL_WGRIB2" -eq 1 ]]; then
    ensure_build_prereqs
    clone_wgrib2
    build_install_wgrib2
  fi

  if [[ "$INSTALL_BREW_TOOLS" -eq 1 ]]; then
    install_brew_tools
  fi

  if [[ "$INSTALL_CNvgrib" -eq 1 ]]; then
    install_cnvgrib
  fi

  if [[ "$INSTALL_WGRIB2" -eq 1 || "$INSTALL_CNvgrib" -eq 1 ]]; then
    chmod_fl_scripts
  fi

  log "Done."
  if [[ "$INSTALL_WGRIB2" -eq 1 ]]; then
    echo "  wgrib2: ${INSTALL_PREFIX}/bin/wgrib2 (and /usr/local/bin/wgrib2 on macOS when INSTALL_PREFIX=/usr/local)"
  fi
  if [[ "$INSTALL_WGRIB2" -eq 1 && "$INSTALL_BREW_TOOLS" -eq 0 && "$INSTALL_CNvgrib" -eq 0 ]]; then
    echo "  Next: ./setup-florida-dev.sh --all   OR   ./setup-florida-dev.sh --brew-tools --cnvgrib"
  fi
}

main
