"""Who signed the Archi.ru open letter and when: occupation groups and signatures per day (D-42).

Run from the repository root after src/collectors/archi_petition.py. Reads
data/raw/petitions/<date>/archi_signatures.jsonl (no names are stored there) and writes aggregates only:
reports/tables/petition_occupations.csv, petition_occupation_top.csv, petition_daily.csv.

Occupation is what the signer typed, optional and unchecked. Groups come from a word list below; a field that
matches no group is `other_stated`. «студент», «школьник», «пенсионер» are the only direct signals of age in our
data, and they cover only people who chose to write them. A signature is not a person: one person can sign twice.
"""
import argparse
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/tables'
# First matching group wins, so the narrow age groups come first.
GROUPS = [
    ('student', r'студент|школьни|аспирант|учащ|магистрант|бакалавр'),
    ('pensioner', r'пенсионер|на пенсии|ветеран труда'),
    ('architecture_heritage', r'архитект|градостро|урбанист|реставрат|ландшафт|проектировщ|краевед|москвовед|'
                              r'искусствовед|историк архитект|охран\w* наслед'),
    ('design_art_media', r'дизайн|художни|фотограф|иллюстрат|арт-|скульпт|режисс|актёр|актер|актрис|артист|балет|'
                         r'балерин|музыкант|композитор|дирижёр|дирижер|сценограф|декоратор|ретуш|журналист|редактор|'
                         r'писател|копирайт|оператор|продюсер|галер|блогер|телевед|smm'),
    ('culture_science_education', r'истори|учител|преподават|педагог|воспитател|научн|учёный|ученый|библиотек|музе|'
                                  r'экскурсовод|гид\b|филолог|переводчик|культуролог|социолог|философ|доцент|профессор|'
                                  r'исследоват|биолог|геолог|геофизик|химик|физик|математик'),
    ('engineering_it', r'инженер|программист|разработчик|\bit\b|\bит\b|айти|аналитик|технолог|конструктор|электрик|'
                       r'энергетик|строител|тестировщ|devops|системн|метролог'),
    ('business_office', r'менеджер|экономист|бухгалтер|юрист|адвокат|маркетолог|предпринимат|\bип\b|самозанят|директор|'
                        r'ген\.?\s*дир|\bceo\b|руководител|финанс|продаж|риелтор|риэлтор|брокер|аудит|страхов|логист|'
                        r'\bhr\b|кадр|секретар|администратор|ассистент|консультант|коуч|связям с общественностью|'
                        r'документовед|служащ|инспектор|госслуж|чиновн'),
    ('health_social', r'врач|медсестр|медицинск|медик|стоматолог|психолог|терапевт|терапист|фельдшер|акушер|фармацевт|'
                      r'ветеринар|соцработ'),
    ('services_trades', r'продав|бариста|курьер|пекарь|повар|официант|водител|слесар|мастер|маникюр|визаж|косметолог|'
                        r'флорист|парикмахер|няня|тренер|охранник|рабоч'),
    ('not_working', r'домохозяйк|безработн|в декрете|декрет'),
]
RESIDENT = re.compile(r'жител|живу|местн', re.I)


def group(occupation):
    if not isinstance(occupation, str) or occupation.strip().lower() in ('', '-', 'нет', '—'):
        return 'not_stated'
    text = occupation.lower()
    return next((name for name, pattern in GROUPS if re.search(pattern, text)), 'other_stated')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--date', default='2026-10-29', help='collection folder date (default %(default)s)')
    args = parser.parse_args()
    path = ROOT / 'data/raw/petitions' / args.date / 'archi_signatures.jsonl'
    rows = pd.read_json(path, lines=True).drop_duplicates('sig_id', keep='last')
    ids = set(rows.sig_id)
    missing = sorted(set(range(1, max(ids) + 1)) - ids)
    rows['group'] = rows.occupation.map(group)
    rows['day'] = pd.to_datetime(rows.signed_at_msk.str[:10])

    n = len(rows)
    stated = rows[rows.group != 'not_stated']
    occupations = (rows.group.value_counts().rename('signatures').to_frame()
                   .assign(share_of_all=lambda t: (t.signatures / n).round(3),
                           share_of_stated=lambda t: (t.signatures / len(stated)).where(t.index != 'not_stated').round(3)))
    top = (stated.occupation.str.strip().str.lower().value_counts().head(40).rename('signatures')
           .rename_axis('occupation').reset_index())
    daily = rows.groupby('day').agg(signatures=('sig_id', 'size'), with_comment=('comment', lambda c: c.notna().sum()))
    daily['cumulative'] = daily.signatures.cumsum()
    OUT.mkdir(parents=True, exist_ok=True)
    occupations.to_csv(OUT / 'petition_occupations.csv', index_label='group')
    top.to_csv(OUT / 'petition_occupation_top.csv', index=False)
    daily.to_csv(OUT / 'petition_daily.csv', index_label='day')

    residents = rows.occupation.fillna('').str.contains(RESIDENT) | rows.comment.fillna('').str.contains(RESIDENT)
    print(f'{n} signatures (ids 1–{max(ids)}; {len(missing)} numbers missing), occupation stated by {len(stated)} '
          f'({len(stated) / n:.1%}), comment by {rows.comment.notna().sum()}; '
          f'a resident word («житель», «живу», «местн») in occupation or comment: {residents.sum()}')
    print(occupations.to_string())
    print('first day', daily.index.min().date(), '; top days:')
    print(daily.sort_values('signatures', ascending=False).head(8).to_string())
    by_week = rows.groupby(rows.day.dt.to_period('W-SUN').dt.start_time).size()
    print('by week:'); print(by_week.to_string())


if __name__ == '__main__':
    main()
