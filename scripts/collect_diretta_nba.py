#!/usr/bin/env python3
"""ALEX — collector NBA da Diretta.it. Nessuna API a pagamento, nessuna fonte alternativa.
Legge i feed embedded summary-fixtures/summary-results e tenta di associare le quote
Bet365 pubblicate nelle schede evento. Le quote non trovate restano null (mai inventate).
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, sys, time
from pathlib import Path
from urllib.parse import urljoin
import requests

BASE='https://www.diretta.it'
CALENDAR=BASE+'/basket/usa/nba/calendario/'
RESULTS=BASE+'/basket/usa/nba/risultati/'
OUT=Path('data/diretta_nba.json')
HEADERS={
 'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
 'Accept-Language':'it-IT,it;q=0.9,en;q=0.8', 'Referer':BASE+'/'
}
S=requests.Session(); S.headers.update(HEADERS)

def get(url):
    err=None
    for n in range(3):
        try:
            r=S.get(url,timeout=35); r.raise_for_status(); return r.text
        except Exception as e:
            err=e; time.sleep(1.5*(n+1))
    raise RuntimeError(f'{url}: {err}')

def feed(html,name):
    # Flashscore/Diretta bootstrap: cjs.initialFeeds["summary-fixtures"] = { data: `...` }
    p=re.compile(r'''initialFeeds\s*\[\s*["']'''+re.escape(name)+r'''["']\s*\]\s*=\s*\{\s*data\s*:\s*`(.*?)`''',re.S)
    m=p.search(html)
    return m.group(1) if m else ''

def split_events(blob):
    if not blob: return []
    # Each event starts at ~AA÷<event-id>. Prefix metadata is discarded.
    chunks=re.split(r'(?=~AA÷)',blob)
    out=[]
    for chunk in chunks:
        if not chunk.startswith('~AA÷'): continue
        d={}
        for token in chunk.strip('¬').split('¬'):
            if '÷' not in token: continue
            k,v=token.split('÷',1)
            if k and k not in d: d[k]=v
        if d.get('AA'): out.append(d)
    return out

def as_int(v):
    try: return int(v)
    except (TypeError,ValueError): return None

def event_to_game(e):
    # Diretta feed: AE = home, AF = away; AG/AH are score fields when present.
    epoch=as_int(e.get('AD'))
    if not epoch: return None
    date=dt.datetime.fromtimestamp(epoch,dt.timezone.utc).date().isoformat()
    home=e.get('AE','').strip(); away=e.get('AF','').strip()
    if not home or not away: return None
    hs,aws=as_int(e.get('AG')),as_int(e.get('AH'))
    # score fields can be absent or placeholders before tip-off.
    final=hs is not None and aws is not None and e.get('AB') not in ('0','1')
    score=f'{hs}-{aws}' if final else ''
    return {'id':str(e['AA']),'date':date,'startTimeUtc':dt.datetime.fromtimestamp(epoch,dt.timezone.utc).isoformat(),
      'home':home,'away':away,'homeScore':hs if final else None,'awayScore':aws if final else None,
      'score':score,'statusCode':e.get('AB'),'statusText':'Conclusa' if final else 'Da giocare/in corso',
      'source':'Diretta.it','sourceUrl':f'{BASE}/basket/usa/nba/','updatedAt':dt.datetime.now(dt.timezone.utc).isoformat()}

def extract_links(html):
    links={}
    for href in re.findall(r'''href=["']([^"']+)["']''',html,re.I):
        u=urljoin(CALENDAR,href)
        # retain only Diretta NBA event links; event ids often appear in /match/.../#/...
        if 'diretta.it' in u and ('/match/' in u or '/partita/' in u):
            links[u]=u
    return list(links.values())

def find_bet365_markets(html):
    """Best-effort parser for rendered/embedded bookmaker data.
    Requires explicit Bet365 bookmaker context; never takes another book's prices.
    Handles common JSON shapes and visible HTML text; unrecognized shapes return null.
    """
    result={'bookmaker':'Bet365','moneylineHome':None,'moneylineAway':None,'totalLine':None,'overOdds':None,'underOdds':None,'quoteStatus':'NON_TROVATE'}
    # Parse JSON-ish script blocks recursively for bookmaker records.
    candidates=[]
    for m in re.finditer(r'<script[^>]*>(.*?)</script>',html,re.S|re.I):
        txt=m.group(1)
        if 'bet365' in txt.lower() and any(x in txt.lower() for x in ('odds','market','outcome','price')):
            candidates.append(txt)
    # Some pages render the bookmaker label and prices in ordinary markup.
    visible=re.sub(r'<[^>]+>',' ',html)
    visible=re.sub(r'\s+',' ',visible)
    if re.search(r'bet\s*365',visible,re.I):
        # Deliberately do not infer price ordering from unstructured text.
        pass
    # Search structured JSON snippets, supporting bookmaker name + market/outcomes.
    for txt in candidates:
        try:
            obj=json.loads(txt.strip())
        except Exception:
            continue
        stack=[obj]
        while stack:
            x=stack.pop()
            if isinstance(x,dict):
                book=' '.join(str(x.get(k,'')) for k in ('name','bookmaker','provider','title')).lower()
                if 'bet365' in book:
                    markets=x.get('markets') or x.get('market') or []
                    if isinstance(markets,dict): markets=[markets]
                    for mk in markets if isinstance(markets,list) else []:
                        if not isinstance(mk,dict): continue
                        label=' '.join(str(mk.get(k,'')) for k in ('name','title','marketName','type')).lower()
                        outs=mk.get('outcomes') or mk.get('selections') or []
                        vals=[]
                        for o in outs if isinstance(outs,list) else []:
                            if isinstance(o,dict):
                                nm=' '.join(str(o.get(k,'')) for k in ('name','label','outcome')).lower()
                                odd=o.get('odds') or o.get('price') or o.get('decimalOdds')
                                try: odd=float(str(odd).replace(',','.'))
                                except: odd=None
                                vals.append((nm,odd,o))
                        if ('money' in label or '1x2' in label or 'winner' in label or 'testa' in label) and len(vals)>=2:
                            # team names are matched against labels; fallback to explicit home/away keys.
                            for nm,odd,o in vals:
                                side=str(o.get('side') or o.get('position') or '').lower()
                                if side in ('home','1'): result['moneylineHome']=odd
                                if side in ('away','2'): result['moneylineAway']=odd
                        if ('total' in label or 'over/under' in label or 'totals' in label):
                            for nm,odd,o in vals:
                                if 'over' in nm: result['overOdds']=odd
                                if 'under' in nm: result['underOdds']=odd
                                line=o.get('line') or mk.get('line')
                                if line is not None:
                                    try: result['totalLine']=float(str(line).replace(',','.'))
                                    except: pass
                stack.extend(x.values())
            elif isinstance(x,list): stack.extend(x)
    if any(result[k] is not None for k in ('moneylineHome','moneylineAway','totalLine','overOdds','underOdds')):
        result['quoteStatus']='PARZIALI' if any(result[k] is None for k in ('moneylineHome','moneylineAway','totalLine','overOdds','underOdds')) else 'OK'
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--from',dest='start'); ap.add_argument('--to',dest='end'); ap.add_argument('--skip-odds',action='store_true'); args=ap.parse_args()
    today=dt.datetime.now(dt.timezone.utc).date(); start=dt.date.fromisoformat(args.start) if args.start else today-dt.timedelta(days=7); end=dt.date.fromisoformat(args.end) if args.end else today
    old={'schema':1,'games':[]}
    if OUT.exists():
        try: old=json.loads(OUT.read_text(encoding='utf-8'))
        except Exception as e: raise SystemExit(f'Archivio esistente illeggibile: {e}')
    games={str(g['id']):g for g in old.get('games',[]) if g.get('id')}
    htmls=[]
    for url in (CALENDAR,RESULTS):
        h=get(url); htmls.append((url,h)); print(f'PAGINA {url}: {len(h)} byte')
    found=0
    for url,h in htmls:
        for feed_name in ('summary-fixtures','summary-results'):
            blob=feed(h,feed_name)
            events=split_events(blob)
            print(f'{feed_name}: {len(events)} eventi incorporati in {url}')
            for e in events:
                g=event_to_game(e)
                if not g: continue
                day=dt.date.fromisoformat(g['date'])
                if not (start<=day<=end): continue
                prev=games.get(g['id'],{})
                # Preserve odds/history already collected; refresh match details.
                g={**prev,**g,'quoteHistory':prev.get('quoteHistory',[])}
                games[g['id']]=g; found+=1
    if found==0:
        raise SystemExit('ERRORE: nessuna partita nella finestra richiesta. Archivio precedente non modificato.')
    # Match pages are discovered from the event listing, then linked by event id where possible.
    # Diretta markup may not expose all quote values in static HTML. Do not fabricate them.
    if not args.skip_odds:
        # Try event URLs found in calendar/results pages; event page URL includes id or slug.
        links=[]
        for _,h in htmls: links.extend(extract_links(h))
        for u in dict.fromkeys(links):
            try:
                page=get(u)
                # Link-to-id association from URL/text is intentionally conservative.
                for gid,g in games.items():
                    if gid in u or gid in page:
                        q=find_bet365_markets(page)
                        if q['quoteStatus']!='NON_TROVATE':
                            snap={'capturedAt':dt.datetime.now(dt.timezone.utc).isoformat(),**q}
                            hist=g.setdefault('quoteHistory',[])
                            if not hist or hist[-1].get('capturedAt','')[:16]!=snap['capturedAt'][:16]: hist.append(snap)
                            g.update({k:v for k,v in q.items() if k!='bookmaker'})
                            g['bookmaker']='Bet365'; g['quoteType']='CLOSING_LINE' if dt.date.fromisoformat(g['date'])<today else 'CURRENT'
                time.sleep(.15)
            except Exception as e: print(f'Scheda non letta {u}: {e}')
    selected=sorted([g for g in games.values() if start<=dt.date.fromisoformat(g['date'])<=end],key=lambda x:(x['date'],x['startTimeUtc'],x['home']))
    payload={'schema':2,'source':'Diretta.it','bookmaker':'Bet365','updatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'period':{'from':start.isoformat(),'to':end.isoformat()},'games':sorted(games.values(),key=lambda x:(x['date'],x['startTimeUtc'])),'lastRun':{'gamesInWindow':len(selected),'eventsParsed':found,'bet365QuotesFound':sum(1 for g in selected if any(g.get(k) is not None for k in ('moneylineHome','moneylineAway','totalLine','overOdds','underOdds')))}}
    OUT.parent.mkdir(parents=True,exist_ok=True); tmp=OUT.with_suffix('.tmp'); tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(OUT)
    print(f"SALVATO {OUT}: {len(selected)} partite nella finestra; quote Bet365 associate a {payload['lastRun']['bet365QuotesFound']} partite.")
    print('Campi quote non esposti dal markup restano null: nessun dato stimato o preso da altri bookmaker.')
if __name__=='__main__': main()
