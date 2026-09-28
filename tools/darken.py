# darken.py (SuperScience Blue, tools)
# Created: 2026-09-27 | Last change: 2026-09-28 04:40 — header + license line added for publishing.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Derive the dark variant of SuperScience Blue from the light stylesheet.
Neutral (grey) colors have their lightness inverted into a dark range;
saturated colors (blues, status colors), pure white and near-black
shadows are kept. Usage: darken.py light.css dark.css"""
import re, sys, colorsys
def dark_rgb(r,g,b):
    h,l,s=colorsys.rgb_to_hls(r/255,g/255,b/255)
    if (r,g,b)==(255,255,255) or l<0.06 or s>0.35: return (r,g,b)
    l2=0.11+(1-l)*0.80
    s2=min(s,0.12)
    rr,gg,bb=colorsys.hls_to_rgb(h,l2,s2)
    return tuple(round(x*255) for x in (rr,gg,bb))
def hexrep(m):
    h=m.group(1)
    if len(h)==3: h=''.join(c*2 for c in h)
    if len(h)!=6: return m.group(0)
    r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
    return '#%02x%02x%02x'%dark_rgb(r,g,b)
def rgbrep(m):
    f,args=m.group(1),[a.strip() for a in m.group(2).split(',')]
    try: r,g,b=(int(float(a)) for a in args[:3])
    except ValueError: return m.group(0)
    r,g,b=dark_rgb(r,g,b)
    return f"{f}({r}, {g}, {b}{', '+args[3] if len(args)>3 else ''})"
src=open(sys.argv[1]).read()
body=src.split('*/',2)
out=re.sub(r'#([0-9a-fA-F]{3,8})\b(?![\w-])',hexrep,src)
out=re.sub(r'\b(rgba?)\(\s*([\d.\s,]+)\)',rgbrep,out)
open(sys.argv[2],'w').write(out)
