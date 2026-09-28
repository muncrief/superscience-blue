# convert.py (SuperScience Blue, tools)
# Created: 2026-09-27 | Last change: 2026-09-28 04:40 — header + license line added for publishing.
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK3 -> GTK4 conversion of SuperScience Blue. Reads gtk-3.0/gtk.css, writes gtk-4.0/gtk.css body."""
import re, sys
from cssparse import parse, split_sel

# ---------- property transforms ----------
ICON_EFFECT={'dim':'opacity(0.5)','highlight':'brightness(1.2)','none':'none'}
def gtk_gradient(v):
    def rep(m):
        a=[x.strip() for x in split_sel(m.group(1))]
        if a[0]!='radial': return m.group(0)
        pos,r=a[1],float(a[4]); stops=a[5:]
        cols=[]
        for s in stops:
            mm=re.match(r'(from|to)\((.*)\)$',s)
            if mm: cols.append(mm.group(2))
            else:
                mm=re.match(r'color-stop\(([\d.]+),\s*(.*)\)$',s); cols.append(mm.group(2))
        p=pos.split()
        if p==['center','center']:
            return f"radial-gradient(circle farthest-side at center, {cols[0]} 0%, {cols[-1]} {min(100,round(r*200))}%)"
        edge=[x for x in p if x!='center'][0]
        return f"radial-gradient(ellipse farthest-side at {edge}, {cols[0]} 0%, {cols[-1]} 100%)"
    return re.sub(r'-gtk-gradient\(((?:[^()]|\((?:[^()]|\([^()]*\))*\))*)\)',rep,v)

def fix_decl(k,v,log):
    if re.match(r'-[A-Z]',k): log['vendor']+=1; return None
    if k=='-gtk-outline-radius': log['outline-radius']+=1; return None
    if k=='-gtk-icon-effect': log['icon-effect']+=1; return ('-gtk-icon-filter',ICON_EFFECT.get(v,'none'))
    if '-gtk-gradient' in v: log['gradient']+=1; return (k,gtk_gradient(v))
    if k=='box-shadow' and re.fullmatch(r'rgba?\([^)]*\)',v): log['bad-shadow']+=1; return None
    return (k,v)

# ---------- selector transforms (add GTK4 equivalents, keep originals) ----------
def gtk4_variants(s):
    v=s
    v=re.sub(r'\bbutton\.titlebutton','windowcontrols > button',v)
    v=re.sub(r'(?<![\w-])\.titlebutton','windowcontrols > button',v)
    v=re.sub(r'menubar\s*>\s*menuitem','menubar > item',v)
    v=re.sub(r'(?<![\w.-])toolbar(?![\w-])','.toolbar',v)
    v=re.sub(r'(?<![\w.-])messagedialog(?![\w-])','window.dialog.message',v)
    v=re.sub(r'combobox\s*>\s*box\s*>\s*button','dropdown > button',v)
    v=re.sub(r'(?<![\w.-])combobox(?![\w-])','dropdown',v)
    v=re.sub(r'(spinbutton[^ ]*(?:\s*>\s*|\s+))entry\b',r'\1text',v)
    v=re.sub(r'headerbar\s*>\s*','headerbar ',v)
    v=re.sub(r'(?<![\w.-])placessidebar(?![\w-])','.navigation-sidebar',v)
    v=re.sub(r'(?<![\w.-])list(?![\w-])','listview',v)
    # popover: GTK4 draws its box on the contents/arrow child nodes
    v=re.sub(r'(popover[\w.:()-]*)\s*>\s*(?!contents|arrow)',r'\1 > contents > ',v)
    return v if v!=s else None

BOX_PROPS=('background','border','box-shadow','padding','border-radius','background-color','background-image','background-clip','border-color','border-width','border-style')
def popover_self(s):
    # selector whose last compound targets the popover node itself
    last=re.split(r'\s*[>+~]\s*|\s+',s.strip())[-1]
    return re.fullmatch(r'popover(\.[\w-]+|:[\w-]+(\([^)]*\))?)*',last) is not None

DECORATION=re.compile(r'(?<![\w.-])decoration(?![\w-])')
def decoration_variant(s):
    if not DECORATION.search(s): return None
    v=re.sub(r'(\.[\w-]+(?::[\w-]+)*)\s+decoration(:[\w-]+)*',lambda m:'window'+m.group(1)+(m.group(2) or ''),s)
    v=re.sub(r'(?<![\w.-])decoration(:[\w-]+)*',lambda m:'window.csd'+(m.group(1) or ''),v)
    return v

def render_decls(ds,ind='  '):
    return ''.join(f"{ind}{k}: {v};\n" for k,v in ds)

def convert(items,log,ind=''):
    out=[]
    for it in items:
        t=it[0]
        if t=='comment': out.append(ind+it[1]+'\n'); continue
        if t=='stmt': out.append(ind+it[1]+';\n'); continue
        if t=='at':
            out.append(f"{ind}{it[1]} {{\n"+''.join(convert(it[2],log,ind+'  '))+f"{ind}}}\n"); continue
        sel,body=it[1],it[2]
        if sel.startswith(('from','to')) or re.fullmatch(r'[\d.%\s,]+',sel):  # keyframe
            ds=[fix_decl(k,v,log) for k,v in _d(body)]
            out.append(f"{ind}{sel} {{\n{render_decls([d for d in ds if d],ind+'  ')}{ind}}}\n"); continue
        ds=[d for d in (fix_decl(k,v,log) for k,v in _d(body)) if d]
        if not ds: log['emptied']+=1; continue
        sels=split_sel(sel); keep=[]; pop=[]; deco=[]
        # GTK3 draws "*" outlines only on the focused widget; GTK4 draws them
        # on every widget. Move them to *:focus-visible (keyboard focus).
        if [x.strip() for x in sels]==['*'] and any(k.startswith('outline') for k,_ in ds):
            ol=[d for d in ds if d[0].startswith('outline')]; ds=[d for d in ds if not d[0].startswith('outline')]
            out.append(f"{ind}*:focus-visible {{\n{render_decls(ol,ind+'  ')}{ind}}}\n"); log['focus-outline']+=1
            if not ds: continue
        for s in sels:
            s=re.sub(r'\s+',' ',s)
            if popover_self(s): pop.append(s); continue
            keep.append(s)
            v=gtk4_variants(s)
            if v: keep.append(v); log['variant']+=1
            dv=decoration_variant(s)
            if dv: deco.append(dv)
        if keep: out.append(f"{ind}{', '.join(dict.fromkeys(keep))} {{\n{render_decls(ds,ind+'  ')}{ind}}}\n")
        if pop:
            log['popover']+=1
            box=[d for d in ds if d[0].startswith(BOX_PROPS)]; rest=[d for d in ds if not d[0].startswith(BOX_PROPS)]
            if rest: out.append(f"{ind}{', '.join(pop)} {{\n{render_decls(rest,ind+'  ')}{ind}}}\n")
            if box:
                out.append(f"{ind}{', '.join(p+' > contents' for p in pop)} {{\n{render_decls(box,ind+'  ')}{ind}}}\n")
                arrow=[d for d in box if d[0] in ('background-color','background-image','border','border-color','border-width','border-style','background')]
                if arrow: out.append(f"{ind}{', '.join(p+' > arrow' for p in pop)} {{\n{render_decls(arrow,ind+'  ')}{ind}}}\n")
        if deco:
            log['decoration']+=1
            dd=[d for d in ds if d[0]!='margin']
            if dd: out.append(f"{ind}{', '.join(dict.fromkeys(deco))} {{\n{render_decls(dd,ind+'  ')}{ind}}}\n")
    return out

def _d(body):
    body=re.sub(r'/\*.*?\*/','',body,flags=re.S)
    r=[]
    for d in body.split(';'):
        if ':' in d:
            k,v=d.split(':',1); r.append((k.strip(),re.sub(r'\s+',' ',v.strip())))
    return r

if __name__=='__main__':
    import collections
    src=open(sys.argv[1]).read()
    log=collections.Counter()
    body=''.join(convert(parse(src),log))
    open(sys.argv[2],'w').write(body)
    print(dict(log))
