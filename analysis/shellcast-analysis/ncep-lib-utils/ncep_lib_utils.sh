#!/bin/sh
# Build cnvgrib (NCEPLIBS-grib_util) for Florida xmrg_proc.sh.
# Prefer: ./setup-florida-dev.sh --cnvgrib  (Homebrew deps + gfortran)
#
# Installs NOAA libraries under nceplibs/dependencies, then grib_util → nceplibs/bin/cnvgrib.

set -eu

ROOT=$PWD
echo "$ROOT"

DEPS_PREFIX="$ROOT/nceplibs/dependencies"
INSTALL_PREFIX="$ROOT/nceplibs"

JOBS="${JOBS:-4}"
if command -v sysctl >/dev/null 2>&1; then
  JOBS=$(sysctl -n hw.ncpu 2>/dev/null || echo "$JOBS")
fi

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_gfortran() {
  command -v gfortran >/dev/null 2>&1 || die "gfortran required (brew install gcc)"
}

homebrew_cmake_prefix_path() {
  if ! command -v brew >/dev/null 2>&1; then
    return 0
  fi
  _path=""
  for _pkg in jasper libpng zlib openblas openjpeg libaec; do
    _prefix=$(brew --prefix "$_pkg" 2>/dev/null) || continue
    if [ -d "$_prefix" ]; then
      if [ -z "$_path" ]; then
        _path="$_prefix"
      else
        _path="$_path:$_prefix"
      fi
    fi
  done
  printf '%s' "$_path"
}

openblas_cmake_args() {
  if ! command -v brew >/dev/null 2>&1; then
    return 0
  fi
  _ob=$(brew --prefix openblas 2>/dev/null) || return 0
  if [ -f "$_ob/lib/libopenblas.dylib" ]; then
    printf '%s' "-DBLAS_LIBRARIES=$_ob/lib/libopenblas.dylib -DLAPACK_LIBRARIES=$_ob/lib/libopenblas.dylib"
  elif [ -f "$_ob/lib/libopenblas.so" ]; then
    printf '%s' "-DBLAS_LIBRARIES=$_ob/lib/libopenblas.so -DLAPACK_LIBRARIES=$_ob/lib/libopenblas.so"
  fi
}

CMAKE_PREFIX_PATH="$DEPS_PREFIX"
_brew_prefixes=$(homebrew_cmake_prefix_path)
if [ -n "$_brew_prefixes" ]; then
  CMAKE_PREFIX_PATH="$CMAKE_PREFIX_PATH:$_brew_prefixes"
fi

_BLAS_LAPACK=$(openblas_cmake_args)

clone_or_update() {
  _dir="$1"
  _url="$2"
  if [ -d "$_dir/.git" ]; then
    echo "Updating $_dir"
    git -C "$_dir" pull --ff-only || true
  else
    git clone --depth 1 "$_url" "$_dir"
  fi
}

build_nceplib() {
  _name="$1"
  _url="$2"
  _dir="$ROOT/NCEPLIBS-$_name"
  clone_or_update "$_dir" "$_url"
  rm -rf "$_dir/build"
  mkdir -p "$_dir/build"
  # shellcheck disable=SC2086
  (cd "$_dir/build" && cmake \
    -DCMAKE_INSTALL_PREFIX="$DEPS_PREFIX" \
    -DCMAKE_PREFIX_PATH="$CMAKE_PREFIX_PATH" \
    $_BLAS_LAPACK \
    .. && make -j"$JOBS" && make install)
  CMAKE_PREFIX_PATH="$DEPS_PREFIX:$CMAKE_PREFIX_PATH"
}

require_gfortran
mkdir -p "$DEPS_PREFIX"

echo "==> NCEPLIBS-bacio"
build_nceplib bacio https://github.com/NOAA-EMC/NCEPLIBS-bacio.git

echo "==> NCEPLIBS-sp"
build_nceplib sp https://github.com/NOAA-EMC/NCEPLIBS-sp.git

echo "==> NCEPLIBS-w3emc"
build_nceplib w3emc https://github.com/NOAA-EMC/NCEPLIBS-w3emc.git

echo "==> NCEPLIBS-g2c"
build_nceplib g2c https://github.com/NOAA-EMC/NCEPLIBS-g2c.git

echo "==> NCEPLIBS-ip"
build_nceplib ip https://github.com/NOAA-EMC/NCEPLIBS-ip.git

echo "==> NCEPLIBS-g2"
build_nceplib g2 https://github.com/NOAA-EMC/NCEPLIBS-g2.git

echo "==> NCEPLIBS-grib_util (cnvgrib)"
GRIB_UTIL_DIR="$ROOT/NCEPLIBS-grib_util"
clone_or_update "$GRIB_UTIL_DIR" https://github.com/NOAA-EMC/NCEPLIBS-grib_util.git
rm -rf "$GRIB_UTIL_DIR/build"
mkdir -p "$GRIB_UTIL_DIR/build"
# Use DEPS_PREFIX only here — mixing Homebrew paths into CMAKE_PREFIX_PATH can hide bacio.
# shellcheck disable=SC2086
(cd "$GRIB_UTIL_DIR/build" && cmake \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX" \
  -DCMAKE_PREFIX_PATH="$DEPS_PREFIX" \
  $_BLAS_LAPACK \
  .. && make -j"$JOBS" cnvgrib && make install)

_cnvgrib="$INSTALL_PREFIX/bin/cnvgrib"
[ -x "$_cnvgrib" ] || die "cnvgrib missing after install: $_cnvgrib"
chmod +x "$_cnvgrib"

# cnvgrib links @rpath/libg2c.0.dylib from the NCEPLIBS-g2c build.
if [ -f "$DEPS_PREFIX/lib/libg2c.0.dylib" ] && command -v install_name_tool >/dev/null 2>&1; then
  install_name_tool -add_rpath "$DEPS_PREFIX/lib" "$_cnvgrib" 2>/dev/null || true
fi

echo "cnvgrib ready: $_cnvgrib"
