#!/usr/bin/env bash
# smoke-test.sh — exercise the bash logic in SKILL.md §Q4 (Figma MCP
# detection) and §Q6 (sibling-aware install location + path normalization)
# against a real sibling-repos parent directory.
#
# Usage:    ./smoke-test.sh <parent-dir>
# Example:  ./smoke-test.sh /Users/bentley/Desktop/bentely/fitto
# Exit:     0 = all checks passed, 1 = ≥1 failure, 2 = bad invocation / setup.
#
# The script auto-detects the APP prefix by globbing <parent>/*-android and
# stripping the suffix. It exercises:
#   - Q4 figma MCP detection (B-1 informational, B-1b empty-grep fallback)
#   - Q6 dual-layout sibling detection (B-2 cwd inside PARENT;
#                                       B-2b cwd /tmp, neither layout matches;
#                                       B-2c cwd IS PARENT — platforms as children)
#   - Q6 path normalization for tilde + relative→absolute (B-3)
#   - Q6 sibling-layout validation at TARGET_PARENT
#                          (B-4 default install location;
#                           B-4b wrong install location → warning fires)
#
# The bash blocks below mirror the canonical logic in SKILL.md §Q4 / §Q6
# (some are extracted into helpers like `detect_siblings()` for table-driven
# testing). If you change either side, change the other — there is no
# automated drift check.

set -u

PARENT="${1:-}"
if [ -z "$PARENT" ] || [ "$PARENT" = "-h" ] || [ "$PARENT" = "--help" ]; then
  cat >&2 <<USAGE
Usage: $0 <parent-dir>
  <parent-dir> must contain at least <APP>-android (ideally also -ios / -backend).
  APP prefix is auto-detected from the *-android folder name.
USAGE
  exit 2
fi
if [ ! -d "$PARENT" ]; then
  echo "Not a directory: $PARENT" >&2
  exit 2
fi

# Normalize PARENT (strip trailing slash, resolve to absolute).
PARENT=$(cd "$PARENT" && pwd)

# Auto-detect APP from <parent>/*-android.
APP=""
for d in "$PARENT"/*-android; do
  if [ -d "$d" ]; then
    base=$(basename "$d")
    APP="${base%-android}"
    break
  fi
done
if [ -z "$APP" ]; then
  echo "Couldn't detect APP prefix — no '*-android' folder found under $PARENT/" >&2
  exit 2
fi

pass=0
fail=0
check() {
  name="$1"
  actual="$2"
  expected="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  PASS $name"
    pass=$((pass+1))
  else
    echo "  FAIL $name"
    echo "       expected: $expected"
    echo "       actual:   $actual"
    fail=$((fail+1))
  fi
}

echo "Smoke test for /mobile-spine:init bash logic"
echo "  PARENT=$PARENT"
echo "  APP=$APP (auto-detected)"
echo

# ===== B-1: Q4 figma MCP detection (informational only) =====
echo "[B-1] Q4 figma MCP detection (informational)"
DETECTED_FIGMA=$(claude mcp list 2>/dev/null | grep -i figma | sed -E 's/: .*$//')
DETECTED_FIGMA_COUNT=$(printf '%s' "$DETECTED_FIGMA" | grep -c .)
echo "  DETECTED_FIGMA_COUNT=$DETECTED_FIGMA_COUNT"
[ "$DETECTED_FIGMA_COUNT" -gt 0 ] && printf '%s\n' "$DETECTED_FIGMA" | sed 's/^/    DETECTED_FIGMA_NAME=/'
echo

# ===== B-1b: empty-grep fallback (assert COUNT=0) =====
echo "[B-1b] empty-grep fallback"
EMPTY=$(echo "no figma servers here" | grep -i 'IMPOSSIBLE_TOKEN_XYZ' | sed -E 's/: .*$//')
EMPTY_COUNT=$(printf '%s' "$EMPTY" | grep -c .)
check "empty count is 0" "$EMPTY_COUNT" "0"
echo

# Mirrors SKILL.md §Q6's dual-layout sibling detection. Takes the cwd to run
# in; reads $APP from the outer scope. Echoes the detected count (0..3),
# preferring cwd-as-parent (platforms-as-children) over cwd-as-neighbor
# (platforms-via-dirname) when both find platforms.
detect_siblings() (
  cd "$1" || exit 99
  CWD_PARENT=$(dirname "$(pwd)")
  [ "$CWD_PARENT" = "/" ] && CWD_PARENT="$(pwd)"
  C=0
  for p in android ios backend; do
    [ -d "$(pwd)/$APP-$p" ] && C=$((C+1))
  done
  N=0
  for p in android ios backend; do
    [ -d "$CWD_PARENT/$APP-$p" ] && N=$((N+1))
  done
  if [ "$C" -gt 0 ]; then
    echo "$C"
  elif [ "$N" -gt 0 ]; then
    echo "$N"
  else
    echo "0"
  fi
)

# ===== B-2: sibling detection — cwd inside PARENT (cwd-as-neighbor layout) =====
echo "[B-2] Q6 sibling detection (cwd inside PARENT, platforms-via-dirname)"
check "3 siblings detected" "$(detect_siblings "$PARENT/$APP-android")" "3"
echo

# ===== B-2b: sibling detection — cwd /tmp (no <APP>-* anywhere reachable) =====
echo "[B-2b] Q6 sibling detection (cwd /tmp, neither layout finds platforms)"
check "0 siblings detected" "$(detect_siblings /tmp)" "0"
echo

# ===== B-2c: sibling detection — cwd IS PARENT (cwd-as-parent layout) =====
echo "[B-2c] Q6 sibling detection (cwd IS PARENT, platforms-as-children)"
check "3 siblings detected" "$(detect_siblings "$PARENT")" "3"
echo

# ===== B-3: path normalization matrix =====
# Mirrors SKILL.md §Q6's lightweight normalization: tilde-prefix → $HOME,
# relative → $(pwd)/$R. Intentionally does NOT collapse './' or call realpath
# (BSD realpath on macOS doesn't accept -m and errors on non-existent paths).
# Subshell function form so the `cd "$PARENT"` doesn't leak to the caller.
echo "[B-3] Q6 path normalization (relative paths resolve against $PARENT)"
normalize() (
  cd "$PARENT" || exit 99
  R="$1"
  case "$R" in
    "~"|"~/"*) R="${HOME}${R#\~}" ;;
  esac
  case "$R" in
    /*) echo "$R" ;;
    *)  echo "$(pwd)/$R" ;;
  esac
)
check "bare tilde '~'"        "$(normalize '~')"            "$HOME"
check "'~/foo'"               "$(normalize '~/foo')"        "$HOME/foo"
check "absolute '/abs/x'"     "$(normalize '/abs/x')"       "/abs/x"
check "relative 'foo'"        "$(normalize 'foo')"          "$PARENT/foo"
check "relative './foo'"      "$(normalize './foo')"        "$PARENT/./foo"
echo

# ===== B-4: validate sibling layout at default TARGET =====
echo "[B-4] Validate sibling layout at default TARGET ($PARENT/$APP-spine)"
TARGET="$PARENT/$APP-spine"
TARGET_PARENT=$(dirname "$TARGET")
[ "$TARGET_PARENT" = "/" ] && TARGET_PARENT="$TARGET"
SIBLINGS_AT_TARGET=0
for p in android ios backend; do
  [ -d "$TARGET_PARENT/$APP-$p" ] && SIBLINGS_AT_TARGET=$((SIBLINGS_AT_TARGET+1))
done
check "3 siblings at TARGET_PARENT" "$SIBLINGS_AT_TARGET" "3"
echo

# ===== B-4b: validate sibling layout at wrong TARGET =====
echo "[B-4b] Validate sibling layout at wrong TARGET ($HOME/wrong-place/foo-spine — warning should fire)"
TARGET="$HOME/wrong-place/foo-spine"
TARGET_PARENT=$(dirname "$TARGET")
[ "$TARGET_PARENT" = "/" ] && TARGET_PARENT="$TARGET"
SIBLINGS_AT_TARGET=0
for p in android ios backend; do
  [ -d "$TARGET_PARENT/$APP-$p" ] && SIBLINGS_AT_TARGET=$((SIBLINGS_AT_TARGET+1))
done
check "0 siblings at wrong TARGET_PARENT" "$SIBLINGS_AT_TARGET" "0"
echo

# ===== Summary =====
echo "Result: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
