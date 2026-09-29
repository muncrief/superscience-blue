# darken.py (SuperScience Blue, tools)
# Created: 2026-09-27 | Last change: 2026-09-29 16:47 — rules for areas that are already dark or blue in the light theme (header bars, title bars, menu bars, the Xfce panel, the Whisker menu) keep their colors; mixed rules are split. Previous entry: very pale tints (chroma under 10%) count as grey.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Derive the dark variant of SuperScience Blue from the light stylesheet.
Neutral (grey) colors have their lightness inverted into a dark range;
saturated colors (blues, status colors), pure white and near-black
shadows are kept. Rules that only style areas which are already dark or
blue in the light theme (KEEP) are left unchanged, so their light text
stays readable; a rule listing both kinds of selectors is split in two.
Usage: darken.py light.css dark.css"""
import re, sys, colorsys

# Areas that are already dark or blue in the light theme
KEEP=re.compile(r'headerbar|\.titlebar|menubar|\.xfce4-panel|panel-toplevel|'
                r'XfcePanel|#tasklist-button|\.mate-panel-menu-bar|#whiskermenu')

def dark_rgb(r,g,b):
    h,l,s=colorsys.rgb_to_hls(r/255,g/255,b/255)
    chroma=(max(r,g,b)-min(r,g,b))/255
    if (r,g,b)==(255,255,255) or l<0.06 or (s>0.35 and chroma>0.10): return (r,g,b)
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
def convert(text):
    text=re.sub(r'#([0-9a-fA-F]{3,8})\b(?![\w-])',hexrep,text)
    return re.sub(r'\b(rgba?)\(\s*([\d.\s,]+)\)',rgbrep,text)

def split_selectors(sel):
    """Split a selector list at top-level commas (not inside parentheses)."""
    parts,depth,cur=[],0,''
    for c in sel:
        if c=='(': depth+=1
        elif c==')': depth-=1
        if c==',' and depth==0:
            parts.append(cur.strip()); cur=''
        else:
            cur+=c
    if cur.strip(): parts.append(cur.strip())
    return parts

def chunks(src):
    """Yield ('text', s) for statements/whitespace/comments and
    ('rule', prelude, body) for top-level rules; nested blocks stay in body."""
    i,n,start,depth,brace=0,len(src),0,0,0
    while i<n:
        if src.startswith('/*',i):
            j=src.find('*/',i+2)
            i=n if j<0 else j+2
            continue
        c=src[i]
        if c=='{':
            if depth==0: brace=i
            depth+=1
        elif c=='}':
            depth-=1
            if depth==0:
                yield ('rule',src[start:brace],src[brace+1:i])
                start=i+1
        elif c==';' and depth==0:
            yield ('text',src[start:i+1])
            start=i+1
        i+=1
    if start<n: yield ('text',src[start:])

def darken_css(src):
    out=[]
    for ch in chunks(src):
        if ch[0]=='text':
            out.append(convert(ch[1])); continue
        prelude,body=ch[1],ch[2]
        cut=prelude.rfind('*/')+2 if '*/' in prelude else 0
        lead,sel=prelude[:cut],prelude[cut:]
        if sel.strip().startswith('@'):
            out.append(convert(prelude)+'{'+convert(body)+'}'); continue
        sels=split_selectors(sel)
        keep=[s for s in sels if KEEP.search(s)]
        conv=[s for s in sels if not KEEP.search(s)]
        if not keep:
            out.append(convert(prelude)+'{'+convert(body)+'}')
        elif not conv:
            out.append(prelude+'{'+body+'}')
        else:
            ws=sel[:len(sel)-len(sel.lstrip())]
            out.append(convert(lead)+ws+',\n'.join(conv)+' {'+convert(body)+'}\n'
                       +',\n'.join(keep)+' {'+body+'}')
    return ''.join(out)

def main():
    src=open(sys.argv[1]).read()
    open(sys.argv[2],'w').write(darken_css(src))
if __name__=="__main__":
    main()
