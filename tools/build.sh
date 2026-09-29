#!/bin/bash
#
# build.sh (SuperScience Blue, tools)
# Created: 2026-09-27 22:25 | Last change: 2026-09-29 16:37 — builds the dark
# theme (theme-dark/: gtk-3.0 and gtk-4.0 stylesheets and images) instead of
# the old tools/proposals/gtk-dark.css; files are only rewritten when their
# content changes. Previous entry: moved out of the theme into tools/.
#
# Rebuilds:
#   theme/gtk-4.0/gtk.css           from theme/gtk-3.0/gtk.css + supplement.css
#   theme-dark/gtk-3.0/gtk.css      darken.py of theme/gtk-3.0/gtk.css
#   theme-dark/gtk-4.0/gtk.css      darken.py of theme/gtk-4.0/gtk.css
#   theme-dark/gtk-*/assets, borders  darken_images.py of the light images
# then checks the GTK4 stylesheets and theme/gtk-4.0/libadwaita.css with GTK4's
# own CSS parser (GTK3 stylesheets use GTK3-only properties, so they are not).
# libadwaita.css and theme-dark/index.theme are hand-edited, not built.
# Run after any change to gtk-3.0/gtk.css, convert.py, supplement.css,
# darken.py or darken_images.py. Apps must be restarted to pick up changes.
# Needs: python3, python-gobject, python-pillow, gtk4.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
set -o nounset
set -o errexit

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
LIGHT="$ROOT/theme"
DARK="$ROOT/theme-dark"
NOW="$(date "+%Y-%m-%d %H:%M")"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# write_css TARGET CREATED DESCRIPTION BODY
# Writes a two-line header plus BODY to TARGET, unless TARGET already holds
# exactly that body (then the file, and its date, are left alone).
write_css()
{
    local l_target="$1" l_created="$2" l_desc="$3" l_body="$4"
    if [ -f "$l_target" ] && tail -n +4 "$l_target" | cmp -s - "$l_body"
    then
        return 0
    fi
    local l_theme="SuperScience Blue"
    case "$l_target" in "$DARK"/*) l_theme="SuperScience Blue-Dark" ;; esac
    mkdir -p "$(dirname "$l_target")"
    {
        printf '/* %s (%s, %s) */\n' "$(basename "$l_target")" "$l_theme" "$(basename "$(dirname "$l_target")")"
        printf '/* Created: %s | Last change: %s — %s */\n\n' "$l_created" "$NOW" "$l_desc"
        cat "$l_body"
    } > "$l_target"
    echo "wrote ${l_target#"$ROOT"/}"
}

# Light GTK4 stylesheet
python3 "$HERE/convert.py" "$LIGHT/gtk-3.0/gtk.css" "$TMP/body.css"
cat "$TMP/body.css" "$HERE/supplement.css" > "$TMP/gtk4.css"
write_css "$LIGHT/gtk-4.0/gtk.css" "2026-09-27 21:53" \
    "rebuilt by tools/build.sh from gtk-3.0/gtk.css + supplement.css." "$TMP/gtk4.css"

# Dark stylesheets, DERIVED from the light ones by darken.py
python3 "$HERE/darken.py" "$LIGHT/gtk-3.0/gtk.css" "$TMP/dark3.css"
write_css "$DARK/gtk-3.0/gtk.css" "2026-09-29 16:37" \
    "rebuilt by tools/build.sh: DERIVED from theme/gtk-3.0/gtk.css by darken.py." "$TMP/dark3.css"
python3 "$HERE/darken.py" "$TMP/gtk4.css" "$TMP/dark4.css"
write_css "$DARK/gtk-4.0/gtk.css" "2026-09-27 22:23" \
    "rebuilt by tools/build.sh: DERIVED from theme/gtk-4.0/gtk.css by darken.py." "$TMP/dark4.css"

# Dark images, DERIVED from the light ones by darken_images.py
for v in gtk-3.0 gtk-4.0
do
    for d in assets borders
    do
        rm -rf "$DARK/$v/$d"
        (cd "$HERE" && python3 darken_images.py "$LIGHT/$v/$d" "$DARK/$v/$d")
    done
done

for f in "$LIGHT/gtk-4.0/gtk.css" "$LIGHT/gtk-4.0/libadwaita.css" "$DARK/gtk-4.0/gtk.css"
do
    printf '%-40s ' "${f#"$ROOT"/}"
    python3 "$HERE/csscheck.py" "$f" 2>&1 >/dev/null
done
