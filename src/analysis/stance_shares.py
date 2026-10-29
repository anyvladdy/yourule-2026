"""Shares of stance and criticism lines from the labelled sample (D-28, D-38), by platform and by where people talk.

Run from the repository root with .venv/bin/python after `label_sample.py label` has finished.
Reads data/interim/labelling/sample.parquet and labels_<model>.jsonl; writes aggregates only to reports/tables/
(no texts, no author hashes, so the tables can go to git).

Shares are among reactions about the site: rows flagged `off_topic` are counted and then left out.
Inside a platform the sample is a random draw with at most 3 rows per author, so rows count equally and messages of
very active authors are under-drawn. Across platforms each row carries its platform weight (slice size / sample size).
Totals are shares of this author-capped sample, not an estimate of all 5,905 reactions (Codex F1); the 95% interval
uses Kish's effective sample size and ignores the author cap, so it is approximate. On 2026-10-29 the oppose share was
65.7% weighted, 66.2% unweighted and 66.1% with each author counted once. The case thread (D-36) is reported on its
own line and never mixed in.
"""
import argparse
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LABELS = ROOT / 'data/interim/labelling'
OUT = ROOT / 'reports/tables'
STANCES = ['oppose', 'support', 'mixed', 'neutral']
LINES = ['heritage_loss', 'facadism_fake_reproduction', 'collusion_with_city', 'no_masterplan_transparency',
         'no_real_hearings', 'commercial_density', 'loss_of_cultural_spaces', 'local_impacts', 'other']
# Where people talk (D-39). District: communities of ВАО and of the two districts next to the site.
# Preservation and city history: channels of preservationists, city historians and the architecture press.
# City media: editorial channels of city outlets. Everything else is the wide audience: YouTube videos, Dzen blogs and
# posts found by VK's search across the whole network.
SEGMENTS = {
    'district': {'best_vao', 'vao_moscow', 'sokgor', 'club230930257', 'podsluh_preobr', 'vaonews', 'act_preobrajenka',
                 'sokolinaya_gora_vao', 'pamyat_mesta', 'sosedi_preobrazhenskoe'},
    'preservation': {'archnadzor_official', 'engineer_media', 'mskved', 'archi_ru'},
    'city_media': {'moskvichmag', 'Москвич Mag', 'Такие Дела', 'BFM.ru', 'Абзац'},
}


def segment(source_id):
    return next((name for name, ids in SEGMENTS.items() if source_id in ids), 'wide')


def wilson(k, n, z=1.96):
    """95% Wilson interval for k of n; works for a non-integer effective n."""
    if n <= 0:
        return math.nan, math.nan
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def shares(part, group, weighted):
    """One row per group: n, off-topic count, on-topic n, share and 95% interval of each stance."""
    rows = []
    for key, g in part.groupby(group):
        on = g[~g.off_topic]
        w = on.weight if weighted else pd.Series(1.0, index=on.index)
        n_eff = w.sum() ** 2 / (w ** 2).sum() if len(on) else 0
        row = {group: key, 'n': len(g), 'off_topic': int(g.off_topic.sum()), 'n_on_topic': len(on),
               'n_effective': round(n_eff, 1)}
        for stance in STANCES:
            p = w[on.stance == stance].sum() / w.sum() if len(on) else math.nan
            low, high = wilson(p * n_eff, n_eff)
            row.update({stance: round(p, 3), f'{stance}_low': round(low, 3), f'{stance}_high': round(high, 3)})
        rows.append(row)
    return pd.DataFrame(rows)


def lines(part, group):
    """Among on-topic reactions that oppose or are mixed: share naming each criticism line (multi-label)."""
    critical = part[~part.off_topic & part.stance.isin(['oppose', 'mixed'])]
    rows = []
    for key, g in critical.groupby(group):
        row = {group: key, 'n_critical': len(g)}
        for line in LINES:
            row[line] = round(g.criticism_lines.map(lambda v: line in v).mean(), 3)
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--model', default='gemini-3.8-flash', help='labels file labels_<model>.jsonl (default %(default)s)')
    args = parser.parse_args()
    sample = pd.read_parquet(LABELS / 'sample.parquet')
    labels = pd.read_json(LABELS / f'labels_{args.model}.jsonl', lines=True).drop_duplicates('id', keep='last')
    df = sample.merge(labels[['id', 'stance', 'flags', 'criticism_lines']], on='id', how='left')
    missing = df.stance.isna().sum()
    if missing:
        print(f'warning: {missing} of {len(df)} sampled rows have no label yet; they are left out')
        df = df[df.stance.notna()]
    df['off_topic'] = df['flags'].map(lambda v: 'off_topic' in v)
    df['segment'] = df.source_id.map(segment)
    OUT.mkdir(parents=True, exist_ok=True)

    random, case = df[df.stratum == 'random'], df[df.stratum != 'random']
    by_platform = pd.concat([shares(random, 'platform', weighted=False),
                             shares(random.assign(platform='all, weighted'), 'platform', weighted=True)])
    by_segment = pd.concat([shares(random, 'segment', weighted=True),
                            shares(random.assign(segment='all, weighted'), 'segment', weighted=True)])
    case_table = shares(case.assign(stratum='case thread (D-36)'), 'stratum', weighted=False)
    lines_platform = pd.concat([lines(random, 'platform'), lines(random.assign(platform='all, unweighted'), 'platform')])
    lines_segment = lines(random, 'segment')
    segment_sources = (random.groupby(['segment', 'platform', 'source_id'], dropna=False).size()
                       .reset_index(name='n').sort_values(['segment', 'n'], ascending=[True, False]))
    segment_sources.loc[segment_sources.source_id.str.fullmatch(r'[0-9a-f]{16}', na=False), 'source_id'] = 'private blog (hash)'

    outputs = {'stance_by_platform.csv': by_platform, 'stance_by_segment.csv': by_segment,
               'stance_case_thread.csv': case_table, 'lines_by_platform.csv': lines_platform,
               'lines_by_segment.csv': lines_segment, 'segment_sources.csv': segment_sources}
    for name, table in outputs.items():
        table.to_csv(OUT / name, index=False)
    columns = ['n', 'off_topic', 'n_on_topic', 'oppose', 'support', 'mixed', 'neutral']
    print(f'model {args.model}; {len(df)} labelled rows')
    print(by_platform.set_index('platform')[columns].to_string())
    print(by_segment.set_index('segment')[columns].to_string())
    print(case_table.set_index('stratum')[columns].to_string())
    print(lines_platform.set_index('platform').to_string())
    print('written:', ', '.join(f'reports/tables/{name}' for name in outputs))


if __name__ == '__main__':
    main()
