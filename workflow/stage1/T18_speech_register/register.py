"""T18: deterministic register proxies; no age prediction, no network.
Run once to draw validation.csv; fill ok/comment by reading texts, then rerun.
Coverage platforms suffixed :without_largest omit the largest publication.
All shares are fractions. Missing authors excluded from author denominators.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/analysis'))
from label_sample import analysis_slice, CORPUS, DZEN
HERE = Path(__file__).resolve().parent
OUT = HERE / 'out'
PRIVATE = ROOT / 'data/interim/register'
SEED = 20261029
STANCE_COLUMNS = 'family platform group n oppose support mixed neutral oppose_share fisher_p'.split()


def normalize(text):
    return str(text).lower().replace('ё', 'е')


def matches(text, marker):
    value = str(text).replace('ё', 'е') if marker.get('raw_case') else normalize(text)
    return bool(re.search(marker['regex'], value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tests-only', action='store_true')
    args = parser.parse_args()
    markers = yaml.safe_load((OUT / 'markers.yaml').read_text())
    for family, rules in markers.items():
        for rule in rules:
            assert 2 <= len(rule['positive']) <= 3 and 2 <= len(rule['negative']) <= 3
            for t in rule['positive']:
                assert matches(t, rule), (family, 'positive', t)
            for t in rule['negative']:
                assert not matches(t, rule), (family, 'negative', t)
    print('Regex tests passed')
    if args.tests_only:
        return
    full = pd.concat([pd.read_parquet(CORPUS), pd.read_parquet(DZEN)], ignore_index=True)
    df = analysis_slice(full).copy().sort_values('id').reset_index(drop=True)
    assert len(df) == 5905 and df.id.is_unique
    # Publication root, not reply thread or community. Walk supplied parent links.
    idx = {(r.platform, r.id): (r.row_type, r.parent_id) for r in full.itertuples()}
    def publication(row):
        node, seen = row.id, set()
        while (row.platform, node) in idx:
            if node in seen:
                raise ValueError('parent cycle')
            seen.add(node)
            kind, parent = idx[(row.platform, node)]
            if kind in ('post', 'video', 'article'):
                return node
            if not isinstance(parent, str) or not parent:
                break
            node = parent
        return node
    df['publication_key'] = [publication(r) for r in df.itertuples()]
    df['author_key'] = [f'{p}:{a}' if pd.notna(a) and a else None
                        for p, a in zip(df.platform, df.author_id_hash)]
    for family, rules in markers.items():
        df[family] = df.text.map(lambda t: any(matches(t, r) for r in rules))
    PRIVATE.mkdir(parents=True, exist_ok=True)
    flags = df[['id', *markers]].copy()
    flags.to_csv(PRIVATE / 'flags.csv', index=False)
    drawn = []
    for family in markers:
        hit = df[df[family]][['id', 'text']]
        hit = hit.sample(n=min(40, len(hit)), random_state=SEED).sort_values('id')
        hit['family'], hit['ok'], hit['comment'] = family, '', ''
        drawn.append(hit[['id', 'family', 'text', 'ok', 'comment']])
    validation = pd.concat(drawn, ignore_index=True)
    vp = PRIVATE / 'validation.csv'
    if not vp.exists():
        validation.to_csv(vp, index=False)
    checked = pd.read_csv(vp, keep_default_na=False)
    assert checked[['id','family','text']].equals(validation[['id','family','text']]), 'validation draw changed'
    precision = {}
    for family in markers:
        v = checked[checked.family == family]
        good = v.ok.astype(str).isin(['0', '1'])
        precision[family] = float(v.ok.astype(int).mean()) if len(v) and good.all() else None
    scopes = [('all', df)]
    summary = {'claim_type': 'proxy', 'period': '2026-06-01/2026-10-28',
               'decision_rule': 'before stance: youth union < 0.05 OR older < 0.05 => untestable',
               'age_inference': False, 'precision': precision, 'denominators': {}, 'largest': {}}
    reduced = []
    for platform, g in df.groupby('platform', sort=True):
        sizes = g.groupby('publication_key').size().sort_values(ascending=False, kind='stable')
        largest = sizes.index[0]
        small = g[g.publication_key != largest]
        summary['largest'][platform] = int(sizes.iloc[0])
        scopes.extend([(platform,g),(platform+':without_largest',small)])
        reduced.append(small)
    scopes.append(('all:without_largest',pd.concat(reduced)))
    rows = []
    for name, g in scopes:
        a = g.author_key.nunique()
        author_families = g.dropna(subset=['author_key']).groupby('author_key')[list(markers)].max().sum(axis=1)
        summary['denominators'][name] = dict(texts=len(g), authors=a,
            missing_author_texts=int(g.author_key.isna().sum()), multiple_families=int((author_families > 1).sum()))
        for family in markers:
            h = g[g[family]]
            p = precision[family]
            rows.append(dict(family=family, platform=name, texts=len(h), texts_share=len(h)/len(g),
                             authors=h.author_key.nunique(), authors_share=h.author_key.nunique()/a,
                             precision=p, kept=p is not None and p >= .7))
    pd.DataFrame(rows).to_csv(OUT/'coverage.csv', index=False, float_format='%.8f')
    summary['status'] = 'waiting_labels'
    path = ROOT/'data/interim/labelling/labels_gemini-3.8-flash.jsonl'
    lines = path.read_text().splitlines() if path.exists() else []
    summary['labels_lines'] = len(lines)
    stance_rows = []
    if len(lines) == 1522 and all(p is not None for f,p in precision.items() if df[f].any()):
        # Read stance only after complete file and frozen dictionaries / validation.
        labels = pd.DataFrame([json.loads(line) for line in lines])
        sample = pd.read_parquet(ROOT/'data/interim/labelling/sample.parquet')
        assert labels.id.is_unique and set(labels.id) == set(sample.id)
        assert labels.stance.isin(['oppose','support','mixed','neutral']).all()
        joined = sample[['id','stratum']].merge(labels[['id','stance','flags']],on='id',validate='one_to_one')
        summary['case_excluded'] = int((joined.stratum != 'random').sum())
        joined = joined[joined.stratum == 'random']
        summary['off_topic_excluded'] = int(joined['flags'].map(lambda x: 'off_topic' in x).sum())
        joined = joined[~joined['flags'].map(lambda x: 'off_topic' in x)]
        s = df.merge(joined[['id','stance']],on='id',validate='one_to_one')
        n = s.author_key.nunique()
        youth = s[s.youth_slang | s.chat_orthography].author_key.nunique()
        older = s[s.older_register].author_key.nunique()
        summary['decision'] = dict(texts=len(s), authors=n, missing_author_texts=int(s.author_key.isna().sum()), youth_union_authors=youth,
                                   youth_union_share=youth/n, older_authors=older, older_share=older/n)
        fail = youth/n < .05 or older/n < .05
        summary['status'] = 'untestable' if fail else 'coverage_threshold_passed_not_age_validation'
        if not fail:
            from scipy.stats import fisher_exact
            for family in markers:
                if precision[family] is None or precision[family] < .7:
                    continue
                for platform,g in [('all',s),*list(s.groupby('platform',sort=True))]:
                    groups = [g[g[family]],g[~g[family]]]
                    p = None
                    if all(len(x) >= 30 for x in groups):
                        p = float(fisher_exact([[int((x.stance=='oppose').sum()),int((x.stance!='oppose').sum())]
                                               for x in groups]).pvalue)
                    for name,x in zip(['covered','other'],groups):
                        counts = x.stance.value_counts()
                        stance_rows.append(dict(family=family, platform=platform,group=name,n=len(x),
                          **{v:int(counts.get(v,0)) for v in ['oppose','support','mixed','neutral']},
                          oppose_share=counts.get('oppose',0)/len(x) if len(x)>=30 else None,fisher_p=p))
    pd.DataFrame(stance_rows,columns=STANCE_COLUMNS).to_csv(OUT/'stance_by_family.csv',index=False,float_format='%.8f')
    inputs = [CORPUS, DZEN, OUT/'markers.yaml', vp]
    if len(lines) == 1522:
        inputs += [path, ROOT/'data/interim/labelling/sample.parquet']
    summary['input_sha256'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    (PRIVATE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
