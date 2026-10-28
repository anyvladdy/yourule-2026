"""Build out/statements.csv for T14 and validate the card's schema. Run: python .../build_statements.py"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'out' / 'statements.csv'
COLS = ['actor', 'actor_type', 'date', 'url', 'accessed', 'channel', 'stance', 'criticism_lines',
        'what_they_say', 'label', 'note']
TYPES = {'tenant', 'cultural_space', 'municipal_deputy', 'municipal_council', 'city_deputy', 'state_deputy', 'other'}
STANCES = {'oppose', 'support', 'mixed', 'neutral'}
LINES = {'heritage_loss', 'facadism_fake_reproduction', 'collusion_with_city', 'no_masterplan_transparency',
         'no_real_hearings', 'commercial_density', 'loss_of_cultural_spaces', 'local_impacts', 'other'}
MAG = 'https://moskvichmag.ru/gorod/art-klaster-s-atmosferoj-legkogo-syura-kak-byla-ustroena-zhizn-elektrozavoda/'
TD = 'https://takiedela.ru/2026/09/zdes-byl-svet/'
YAB1 = 'https://www.yabloko.ru/regnews/Moscow/2026/06/18'
YAB2 = 'https://www.yabloko.ru/regnews/Moscow/2026/07/08'
KPRF = 'http://msk.kprf.ru/2026/07/31/290614/'
TG_SH = 'https://t.me/AnnaShatunovskayaBurno'

ROWS = [
 ('Мастерская «Кладем на все» (шелкография)', 'tenant', '2025-03-24', MAG, 'Москвич Mag, интервью',
  'neutral', 'loss_of_cultural_spaces',
  'Отъезд с завода — личная трагедия; мастера не знают, куда податься, а город враждебен к тем, кто делает руками',
  'fact', 'о проекте прямо не высказывается: оценка относится к выезду'),
 ('Мастерская «Хрупко» (керамика)', 'tenant', '2025-03-24', MAG, 'Москвич Mag, интервью',
  'neutral', 'loss_of_cultural_spaces',
  '«Это уже конец, прямо сейчас сносят стены»; керамистам нужна мокрая точка, такой мастерской больше не найти',
  'fact', 'о проекте прямо не высказывается: оценка относится к выезду'),
 ('Мастерская «Алекс Миллер» (реклама и производство)', 'tenant', '2025-03-24', MAG, 'Москвич Mag, интервью',
  'neutral', 'loss_of_cultural_spaces',
  'Грустно, что ушла эпоха; ценность завода для мастерской — люди, а не местоположение и историчность здания',
  'fact', 'высказывание о выезде, не о проекте'),
 ('Мастерская «No frame и Обанзе» (швейное производство)', 'tenant', '2025-03-24', MAG, 'Москвич Mag, интервью',
  'oppose', 'commercial_density;loss_of_cultural_spaces',
  'Мастера разбегутся по Москве, а на месте завода построят «какой-нибудь БЦ для воротничков»',
  'fact', ''),
 ('Мастерская «Гала Граффити» (сувениры и мерч)', 'tenant', '2025-03-24', MAG, 'Москвич Mag, интервью',
  'neutral', '',
  'По зданию скучать не будет: «если я и буду скучать, то только по людям»; условия на заводе считает плохими',
  'fact', 'линий критики не выражает'),
 ('Мастерская Sklarna (стекло)', 'tenant', '2025-03-24', MAG, 'Москвич Mag, интервью',
  'neutral', 'loss_of_cultural_spaces',
  'Похожих условий в Москве не найти, промзоны сносятся; уже ищет помещение в Подмосковье',
  'fact', 'о проекте прямо не высказывается: говорит о сносе промзон в целом'),
 ('Студия My Pole Space (танец на пилоне)', 'tenant', '2026-09-30', TD, 'Такие дела, репортаж',
  'neutral', 'loss_of_cultural_spaces',
  'После пожара студия ушла с завода, равнозначную площадку не нашла, московский филиал закрылся',
  'fact', 'интервью опубликовано 2026-09-30; выезд после пожара 2025 года'),
 ('Проект «Красный Вольфрам» (иммерсивные экскурсии)', 'cultural_space', '2026-09-30', TD, 'Такие дела, репортаж',
  'neutral', 'loss_of_cultural_spaces',
  'После закрытия завода выставки и экскурсии прекратились; автор проекта хотел сделать на заводе музей',
  'fact', 'интервью опубликовано 2026-09-30'),
 ('Московское региональное отделение партии «Яблоко»', 'other', '2026-06-18', YAB1, 'yabloko.ru, заявление бюро',
  'oppose', 'heritage_loss;facadism_fake_reproduction;no_masterplan_transparency',
  'Новодел — фальсификация; требует раскрыть судьбу корпусов и добиться оценки Департамента наследия',
  'fact', 'заявление политической партии, не депутата'),
 ('Московское региональное отделение партии «Яблоко»', 'other', '2026-07-08', YAB2, 'yabloko.ru, пресс-релиз',
  'oppose', 'heritage_loss;facadism_fake_reproduction',
  'Партия собирает подписи за госохрану комплекса и призывает власти и застройщика отказаться от «тихого сноса»',
  'fact', 'заявление политической партии, не депутата'),
 ('Д. Л. Медведев, кандидат в Госдуму от КПРФ по округу 204', 'other', '2026-07-29', KPRF,
  'msk.kprf.ru, пресс-служба МГК КПРФ', 'oppose',
  'heritage_loss;facadism_fake_reproduction;commercial_density',
  'Провёл встречу против сноса у Электрозаводской, 12А и направил коллективное заявление избирателей в органы власти',
  'fact', 'не депутат: кандидат; округ 204 на выборах 2026 выиграл В. Третьяк'),
 ('А. Г. Шатуновская-Бюрно, кандидат в Госдуму от «Яблока» по округу 204', 'other', '2026-06-23', TG_SH,
  'Telegram, личный канал', 'oppose', 'heritage_loss',
  '«Электрозавод — жемчужина Преображенки под угрозой сноса»; призвала добиваться сохранения комплекса',
  'fact', 'не депутат: кандидат; часть постов канала — репосты'),
]

rows = []
for r in ROWS:
    actor, atype, date, url, channel, stance, lines, say, label, note = r
    rows.append(dict(zip(COLS, [actor, atype, date, url, '2026-10-28', channel, stance, lines, say, label, note])))

errors = []
for i, row in enumerate(rows, 1):
    if row['actor_type'] not in TYPES:
        errors.append(f'{i}: bad actor_type {row["actor_type"]}')
    if row['stance'] not in STANCES:
        errors.append(f'{i}: bad stance {row["stance"]}')
    for line in filter(None, row['criticism_lines'].split(';')):
        if line not in LINES:
            errors.append(f'{i}: bad line {line}')
    if len(row['what_they_say']) > 200:
        errors.append(f'{i}: what_they_say {len(row["what_they_say"])} chars')
    if row['what_they_say'].count('«') > 1:
        errors.append(f'{i}: more than one «» phrase')
    if not row['url'].startswith('http') or row['accessed'] != '2026-10-28':
        errors.append(f'{i}: bad url/accessed')
    if not row['date'] or len(row['date']) != 10:
        errors.append(f'{i}: bad date')

if len({(r['actor'], r['date']) for r in rows}) != len(rows):
    errors.append('duplicate actor+date')

print(f'rows: {len(rows)} (cap 25); tenants/cultural: {sum(r["actor_type"] in {"tenant","cultural_space"} for r in rows)}')
print('errors:', errors or 'none')
if errors:
    raise SystemExit(1)

with OUT.open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print('written:', OUT.relative_to(HERE))
