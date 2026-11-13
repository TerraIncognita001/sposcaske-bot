"""title + artist -> Wikidata item -> public-domain check -> Commons file (size, licence, thumb URL). 3 requests per work."""
import requests, sys, json, time
UA = {'User-Agent': 'ArtShortsResearch/0.1 (python-requests; educational video research)'}
WD = 'https://www.wikidata.org/w/api.php'; CM = 'https://commons.wikimedia.org/w/api.php'; SQ = 'https://query.wikidata.org/sparql'
S = requests.Session(); S.headers.update(UA)
def get(url, **params):
    for wait in (0, 6, 20, 45, 90):
        time.sleep(wait)
        r = S.get(url, params=params, timeout=40)
        if r.status_code == 200: return r.json()
        if r.status_code not in (429, 503): r.raise_for_status()
        ra = r.headers.get('Retry-After')
        if ra and ra.isdigit(): time.sleep(min(int(ra), 120))
    raise RuntimeError(f'rate limited: {url}')
def find(title, artist):
    hits = get(WD, action='wbsearchentities', search=title, language='en', type='item', limit=20, format='json')['search']
    last = artist.split()[-1].lower(); kinds = ('paint', 'fresco', 'artwork', 'drawing', 'print', 'engraving', 'mural')
    best = next((h for h in hits if last in (h.get('description') or '').lower() and any(k in (h.get('description') or '').lower() for k in kinds)), None) \
        or next((h for h in hits if 'painting' in (h.get('description') or '').lower()), None)
    if not best: return {'title': title, 'error': 'no wikidata hit', 'hits': [(h['id'], h.get('description')) for h in hits[:5]]}
    q = best['id']
    sp = f'''SELECT ?img ?creatorLabel ?died ?inc ?collLabel ?portrait (COUNT(DISTINCT ?sl) AS ?links) (COUNT(DISTINCT ?dep) AS ?depicts) WHERE {{
      BIND(wd:{q} AS ?w) OPTIONAL{{?w wdt:P18 ?img}} OPTIONAL{{?w wdt:P170 ?creator. OPTIONAL{{?creator wdt:P570 ?died}} OPTIONAL{{?creator wdt:P18 ?portrait}}}}
      OPTIONAL{{?w wdt:P571 ?inc}} OPTIONAL{{?w wdt:P195 ?coll}} OPTIONAL{{?sl schema:about ?w}} OPTIONAL{{?w wdt:P180 ?dep}}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }} GROUP BY ?img ?creatorLabel ?died ?inc ?collLabel ?portrait LIMIT 1'''
    b = get(SQ, query=sp, format='json')['results']['bindings']; b = b[0] if b else {}
    v = lambda k: b.get(k, {}).get('value')
    fn = lambda u: requests.utils.unquote(u.rsplit('/', 1)[-1]) if u else None
    r = {'title': title, 'qid': q, 'desc': best.get('description'), 'artist': v('creatorLabel'), 'artist_died': (v('died') or '')[:4] or None,
         'inception': (v('inc') or '')[:4] or None, 'collection': v('collLabel'), 'sitelinks': int(v('links') or 0), 'depicts_n': int(v('depicts') or 0),
         'image': fn(v('img')), 'artist_portrait': fn(v('portrait'))}
    if r['image']:
        ii = get(CM, action='query', titles='File:' + r['image'], prop='imageinfo', iiprop='url|size|mime|extmetadata', iiurlwidth=2400, format='json')
        inf = next(iter(ii['query']['pages'].values()))['imageinfo'][0]; em = inf.get('extmetadata', {})
        r.update(width=inf['width'], height=inf['height'], mime=inf['mime'], thumb=inf.get('thumburl'), url=inf['url'],
                 license=em.get('LicenseShortName', {}).get('value'), copyrighted=em.get('Copyrighted', {}).get('value'))
    died = int(r['artist_died']) if (r['artist_died'] or '').isdigit() else None
    r['pd_ok'] = bool(died and died <= 1925 and r.get('image'))   # author dead 100+ years: safe worldwide
    return r
if __name__ == '__main__':
    out = []
    for t, a in json.loads(sys.argv[1]):
        try: out.append(find(t, a))
        except Exception as e: out.append({'title': t, 'error': repr(e)})
        time.sleep(1.5)
    print(json.dumps(out, indent=1, ensure_ascii=False))
