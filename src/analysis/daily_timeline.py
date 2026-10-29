"""One daily timeline of the conflict: signatures under the Archi.ru letter, publications and reactions about the site
on each platform, media articles, Wordstat and events (D-42).

Run from the repository root after src/collectors/archi_petition.py. Reads data/raw/petitions/<date>/archi_signatures.jsonl,
data/processed/corpus_v2.parquet and corpus_dzen.parquet (relevant rows only), the 27 media articles of T03,
reports/tables/attention_weekly.csv and docs/project_facts/timeline.csv. Days are Moscow days. Writes aggregates only:
reports/tables/daily_timeline.csv and reports/tables/signature_peaks.csv.

A signature peak is a day in the top 10 by signatures. Next to it: publications on that day and the day before, and
events within two days. Spearman correlations of daily signatures with daily publications (same day and next day) are
printed for orientation. Timing does not show cause: a news item, a repost and the signatures can share a trigger.
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/tables'
START, END = '2026-06-01', '2026-10-28'


def moscow_day(df):
    """Moscow calendar day: from the UTC time when there is one, else the stored calendar day."""
    stamp = pd.to_datetime(df.published_at, utc=True, errors='coerce').dt.tz_convert('Europe/Moscow').dt.tz_localize(None)
    return stamp.dt.normalize().fillna(pd.to_datetime(df.published_date, errors='coerce'))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--date', default='2026-10-29', help='signature collection folder date (default %(default)s)')
    args = parser.parse_args()
    days = pd.date_range(START, END, freq='D')
    table = pd.DataFrame(index=days)

    signatures = pd.read_json(ROOT / 'data/raw/petitions' / args.date / 'archi_signatures.jsonl', lines=True)
    signatures = signatures.drop_duplicates('sig_id')
    table['signatures'] = signatures.groupby(pd.to_datetime(signatures.signed_at_msk.str[:10])).size()

    corpus = pd.concat([pd.read_parquet(ROOT / 'data/processed/corpus_v2.parquet'),
                        pd.read_parquet(ROOT / 'data/processed/corpus_dzen.parquet')], ignore_index=True)
    corpus = corpus[corpus.relevant.astype(bool)].assign(day=lambda d: moscow_day(d))
    is_publication = corpus.row_type.isin(['post', 'video'])
    for platform, part in corpus[is_publication].groupby('platform'):
        table[f'publications_{platform}'] = part.groupby('day').size()
    for platform, part in corpus[~is_publication].groupby('platform'):
        table[f'reactions_{platform}'] = part.groupby('day').size()

    articles = pd.read_csv(ROOT / 'workflow/stage0/T03_media/out/articles.csv')
    table['media_articles'] = articles.groupby(pd.to_datetime(articles.date, errors='coerce')).size()
    table = table.fillna(0).astype(int)
    table['publications_all'] = table.filter(like='publications_').sum(axis=1) + table.media_articles
    table['reactions_all'] = table.filter(like='reactions_').sum(axis=1)

    weekly = pd.read_csv(OUT / 'attention_weekly.csv', parse_dates=['week']).set_index('week')
    table['wordstat_week_elektrozavod'] = weekly['Электрозавод'].reindex(table.index, method='ffill')
    events = pd.read_csv(ROOT / 'docs/project_facts/timeline.csv')
    events = events[events.date.str.len() == 10].assign(day=lambda e: pd.to_datetime(e.date))
    table['events'] = [' | '.join(events.loc[events.day == d, 'event'].str[:80]) for d in table.index]
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / 'daily_timeline.csv', index_label='day')

    peaks = []
    for day in table.signatures.nlargest(10).index:
        window = table.loc[day - pd.Timedelta(days=1):day]
        near = events[(events.day >= day - pd.Timedelta(days=2)) & (events.day <= day + pd.Timedelta(days=1))]
        peaks.append({'day': day.date(), 'signatures': table.at[day, 'signatures'],
                      'publications_day_and_before': int(window.publications_all.sum()),
                      'reactions_day_and_before': int(window.reactions_all.sum()),
                      'events_within_2_days': ' | '.join(f'{d.date()} {t[:80]}' for d, t in zip(near.day, near.event))})
    peaks = pd.DataFrame(peaks)
    peaks.to_csv(OUT / 'signature_peaks.csv', index=False)

    active = table.loc[table.signatures.ne(0).idxmax():]
    same = active.signatures.corr(active.publications_all, method='spearman')
    lagged = active.signatures.corr(active.publications_all.shift(1), method='spearman')
    reactions = active.signatures.corr(active.reactions_all, method='spearman')
    print(f'signatures in window: {table.signatures.sum():,} of {len(signatures):,}; first signature day '
          f'{table.signatures.ne(0).idxmax().date()}')
    print(f'Spearman, daily signatures vs publications: same day {same:.2f}, publications one day before {lagged:.2f}; '
          f'vs reactions same day {reactions:.2f} (n = {len(active)} days)')
    print(peaks.drop(columns='events_within_2_days').to_string(index=False))
    print('written: reports/tables/daily_timeline.csv, reports/tables/signature_peaks.csv')


if __name__ == '__main__':
    main()
