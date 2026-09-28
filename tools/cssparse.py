# cssparse.py (SuperScience Blue, tools)
# Created: 2026-09-27 | Last change: 2026-09-28 04:40 — header + license line added for publishing.
# SPDX-License-Identifier: GPL-3.0-or-later
import re
def parse(text):
    """Return list of items: ('comment',s) ('stmt',s) ('rule',sel,body) ('at',head,[items])"""
    i=0; n=len(text); out=[]
    def skipws(i):
        while i<n and text[i].isspace(): i+=1
        return i
    def block(i):
        items=[]
        while True:
            i=skipws(i)
            if i>=n: return items,i
            if text[i]=='}': return items,i+1
            if text.startswith('/*',i):
                j=text.index('*/',i)+2; items.append(('comment',text[i:j])); i=j; continue
            # read prelude until { or ;
            j=i; depth=0
            while j<n:
                c=text[j]
                if text.startswith('/*',j): j=text.index('*/',j)+2; continue
                if c=='(': depth+=1
                elif c==')': depth-=1
                elif depth==0 and c in '{;': break
                j+=1
            pre=text[i:j].strip()
            if j>=n: return items,j
            if text[j]==';':
                items.append(('stmt',pre)); i=j+1; continue
            if pre.startswith('@'):
                sub,k=block(j+1); items.append(('at',pre,sub)); i=k; continue
            # rule body until matching }
            k=j+1; d=0
            while k<n:
                if text.startswith('/*',k): k=text.index('*/',k)+2; continue
                if text[k]=='{': d+=1
                elif text[k]=='}':
                    if d==0: break
                    d-=1
                k+=1
            items.append(('rule',pre,text[j+1:k])); i=k+1
    items,_=block(0)
    return items
def split_sel(sel):
    parts=[];d=0;cur=''
    for c in sel:
        if c=='(':d+=1
        if c==')':d-=1
        if c==',' and d==0: parts.append(cur.strip()); cur=''
        else: cur+=c
    if cur.strip(): parts.append(cur.strip())
    return parts
def decls(body):
    body=re.sub(r'/\*.*?\*/','',body,flags=re.S)
    out=[]
    for d in body.split(';'):
        if ':' in d:
            k,v=d.split(':',1); out.append((k.strip(),v.strip()))
    return out
def walk(items,ctx=()):
    for it in items:
        if it[0]=='at': yield from walk(it[2],ctx+(it[1],))
        elif it[0]=='rule': yield ctx,it[1],it[2]
