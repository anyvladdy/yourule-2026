"""Read-only validation for the stage-0 fact-check; run from repository root."""
import argparse
import csv
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
import yaml

parser = argparse.ArgumentParser(description=__doc__)
parser.parse_args()
root = Path(__file__).resolve().parents[2]
schemas = {
 'telegram.csv': 'handle url title kind subscribers subscribers_seen owner_type channel_stance relevant_post_url relevant_post_date accessed priority note',
 'video.csv': 'platform url title channel date views views_seen accessed channel_stance note',
 'vk.csv': 'url name members members_seen owner_type channel_stance relevant_post_url relevant_post_date accessed priority note',
 'petitions.csv': 'pet_id url platform title organiser created_date signatures signatures_seen accessed target main_demands note',
 'articles.csv': 'art_id url outlet date accessed title viewpoint criticism_lines quoted_actors key_claim syndicated_copies note',
 'reality_check.csv': 'claim_id claim status source_url source_date accessed queries_tried note',
 'timeline.csv': 'date event actor type source_url source_date accessed confidence claim_id',
 'cases_summary.csv': 'site city years conflict_level outcome_for_developer key_move sources',
 'analog_cases.csv': 'site city years conflict_level outcome_for_developer key_move sources',
 'official.csv': 'doc_id url issuer doc_type date accessed object what_it_says claim_id note',
 'developer_statements.csv': 'stmt_id date channel url accessed speaker what_was_said reaction_seen claim_id',
 'building_matrix.csv': 'object status evidence evidence_date conflict follow_up',
}
result = {'csv': [], 'handoffs': [], 'yaml': [], 't06': {}}
for base in (root / 'workflow/stage0', root / 'docs'):
    paths = base.glob('*/out/*.csv') if base.name == 'stage0' else base.rglob('*.csv')
    for path in sorted(paths):
        with path.open(newline='', encoding='utf-8') as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
            fields = reader.fieldnames
        item = {'file': str(path.relative_to(root)), 'rows': len(rows), 'columns': fields,
                'schema_matches': fields == schemas[path.name].split(),
                'bad_width': sum(None in r or None in r.values() for r in rows),
                'duplicate_rows': len(rows) - len({tuple(r.values()) for r in rows}),
                'duplicate_ids': {}, 'bad_dates': []}
        for key in ('pet_id', 'art_id', 'doc_id', 'stmt_id', 'handle'):
            if key in fields:
                counts = Counter(r[key] for r in rows)
                item['duplicate_ids'][key] = [k for k, v in counts.items() if v > 1]
        if path.name == 'reality_check.csv':
            item['claim_ids_complete'] = sorted(r['claim_id'] for r in rows) == [f'C{i:02}' for i in range(1, 9)]
        for index, row in enumerate(rows, 1):
            for key in ('accessed', 'date', 'source_date', 'evidence_date', 'created_date', 'relevant_post_date', 'subscribers_seen', 'views_seen', 'signatures_seen', 'members_seen'):
                value = row.get(key, '')
                if value and not re.fullmatch(r'\d{4}(?:-\d{2}(?:-\d{2})?)?', value):
                    item['bad_dates'].append([index, key, value])
        if path.name == 'timeline.csv':
            item['sorted'] = [r['date'] for r in rows] == sorted(r['date'] for r in rows)
        if path.name == 'articles.csv':
            item['viewpoints'] = dict(Counter(r['viewpoint'] for r in rows))
            item['criticism_lines'] = dict(Counter(tag for r in rows for tag in r['criticism_lines'].split(';') if tag))
            item['outlets'] = len({r['outlet'] for r in rows})
        # Category checks use the card's controlled values.
        allowed = {
            'priority': {'1', '2', '3'},
            'viewpoint': {'critical', 'developer', 'official', 'balanced', 'other'},
            'confidence': {'high', 'medium', 'low'},
            'conflict_level': {'high', 'medium', 'low'},
            'outcome_for_developer': {'better', 'worse', 'mixed', 'unknown'},
        }
        if path.name == 'developer_statements.csv':
            allowed['channel'] = {'site', 'press', 'interview', 'social', 'other'}
        if path.name == 'building_matrix.csv':
            allowed['status'] = {'protected', 'planned_preserved', 'planned_demolished', 'planned_reproduced', 'unknown'}
        if path.name == 'reality_check.csv':
            allowed['status'] = {'confirmed', 'partly', 'not_found', 'inaccessible', 'contradicted'}
        if path.name == 'official.csv':
            allowed['doc_type'] = {'registry_entry', 'decision', 'order', 'hearing_notice', 'plan', 'press_release', 'other'}
        item['bad_categories'] = [[i, k, r[k]] for i, r in enumerate(rows, 1) for k, values in allowed.items() if k in r and r[k] not in values]
        result['csv'].append(item)
for path in sorted((root / 'workflow/stage0').glob('*/HANDOFF.md')):
    count = len(path.read_text().splitlines())
    result['handoffs'].append({'file': str(path.relative_to(root)), 'lines': count, 'pass': count <= 30})
for path in sorted((root / 'config').glob('*.yaml')):
    data = yaml.safe_load(path.read_text())
    result['yaml'].append({'file': str(path.relative_to(root)), 'valid': True})
path = root / 'workflow/stage0/T06_keyword_variants/make_variants.py'
spec = importlib.util.spec_from_file_location('review_t06', path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
source = yaml.safe_load((root / 'config/keywords.yaml').read_text())
terms = [(section, term) for section in module.SECTIONS for term in source[section]]
morph = module.pymorphy3.MorphAnalyzer()
entries, paradigms = [], {}
for section, term in terms:
    entry, paradigm = module.make_entry(morph, section, term)
    entries.append(entry)
    paradigms[term] = paradigm
report, errors = module.test_entries(entries, paradigms, terms)
saved = yaml.safe_load((path.parent / 'out/variants.yaml').read_text())
result['t06'] = {
    'input_terms': len(terms), 'saved_terms': len(saved),
    'main_guard_pass': set(t for _, t in terms) == set(module.SPECS),
    'obsolete_specs': sorted(set(module.SPECS) - set(t for _, t in terms)),
    'saved_matches_current': saved == entries,
    'report_matches_current': (path.parent / 'out/test_report.txt').read_text() == report,
    'current_regex_errors': errors, 'current_test_summary': report.splitlines()[-2],
}
print(json.dumps(result, ensure_ascii=False, indent=2))
