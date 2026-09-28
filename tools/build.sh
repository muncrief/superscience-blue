#!/bin/bash
#
# build.sh (SuperScience Blue, tools)
# Created: 2026-09-27 22:25 | Last change: 2026-09-28 04:40 — moved out of the
# theme into tools/; paths follow the repo layout; the dark variant is written
# to tools/proposals/ (not shipped until approved).
#
# Rebuilds theme/gtk-4.0/gtk.css from theme/gtk-3.0/gtk.css + supplement.css,
# and tools/proposals/gtk-dark.css (derived from gtk.css by darken.py), then
# checks them and theme/gtk-4.0/libadwaita.css with GTK4's own CSS parser.
# libadwaita.css is hand-edited, not built.
# Run after any change to gtk-3.0/gtk.css, convert.py, supplement.css or
# darken.py. Apps must be restarted to pick up changes.
# Needs: python3, python-gobject, gtk4.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
set -o nounset
set -o errexit

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
GTK3="$ROOT/theme/gtk-3.0"
GTK4="$ROOT/theme/gtk-4.0"
DARK="$HERE/proposals/gtk-dark.css"
NOW="$(date "+%Y-%m-%d %H:%M")"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 "$HERE/convert.py" "$GTK3/gtk.css" "$TMP/body.css"
{
    printf '/* gtk.css (SuperScience Blue, gtk-4.0) */\n'
    printf '/* Created: 2026-09-27 21:53 | Last change: %s — rebuilt by tools/build.sh from gtk-3.0/gtk.css + supplement.css. */\n\n' "$NOW"
    cat "$TMP/body.css" "$HERE/supplement.css"
} > "$GTK4/gtk.css"

tail -n +3 "$GTK4/gtk.css" > "$TMP/light.css"
python3 "$HERE/darken.py" "$TMP/light.css" "$TMP/dark.css"
mkdir -p "$(dirname "$DARK")"
{
    printf '/* gtk-dark.css (SuperScience Blue, gtk-4.0) */\n'
    printf '/* Created: 2026-09-27 22:23 | Last change: %s — rebuilt by tools/build.sh: DERIVED from gtk.css by darken.py (a proposal, not an original design). */\n' "$NOW"
    cat "$TMP/dark.css"
} > "$DARK"

for f in "$GTK4/gtk.css" "$DARK" "$GTK4/libadwaita.css"
do
    printf '%-16s ' "$(basename "$f")"
    python3 "$HERE/csscheck.py" "$f" 2>&1 >/dev/null
done
