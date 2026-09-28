# csscheck.py (SuperScience Blue, tools)
# Created: 2026-09-27 | Last change: 2026-09-28 04:40 — header + license line added for publishing.
# SPDX-License-Identifier: GPL-3.0-or-later
import sys, gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk, Gio
Gtk.init()
errs=[]
p=Gtk.CssProvider()
def on_err(prov, section, error):
    loc=section.get_start_location()
    errs.append((loc.lines+1, error.message))
p.connect('parsing-error', on_err)
p.load_from_file(Gio.File.new_for_path(sys.argv[1]))
for l,m in errs: print(f"{l}: {m}")
print(f"TOTAL_ERRORS {len(errs)}", file=sys.stderr)
