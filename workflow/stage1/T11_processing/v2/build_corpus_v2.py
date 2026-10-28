"""Build an independent corpus v2 from YouTube, Telegram and VK; preserve all v1 outputs.

Run from repository root. Only completed *.jsonl in the explicit three directories
are used. No discovery, browser access, Dzen or dsh output is read.
"""
import argparse, csv, hashlib, importlib.util, json, re, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('t11_base',HERE.parent/'build_corpus.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
EXTRA=[('published_date',pa.string()),('date_precision',pa.string()),('period',pa.string()),
       ('parent_present',pa.bool_()),('thread_present',pa.bool_()),('context_complete',pa.bool_()),
       ('counter_precision',pa.string())]
SCHEMA=pa.schema(list(b.FIELDS)+EXTRA)
OUT=HERE/'out'

def period(day):
    if not day:return 'unknown'
    if day<'2025-02-08':return 'P0'
    if day<'2025-09-15':return 'P1'
    if day<'2026-06-01':return 'P2'
    if day<='2026-10-28':return 'P3'
    return 'after_cut'

def vk_number(value):
    if value is None or value=='':return None
    value=re.sub(r'[\s\u00a0\u202f]','',str(value))
    return int(value) if re.fullmatch(r'\d+',value) else None

def vk_row(raw, kind, post, salt):
    date=raw.get('published_at')
    day_only=bool(date and re.fullmatch(r'\d{4}-\d{2}-\d{2}',date))
    # A calendar date is not a known publication instant. No invented midnight.
    date_iso=None if day_only or not date else b.utc(date)
    day=date if day_only else date_iso[:10] if date_iso else None
    row=dict.fromkeys(SCHEMA.names)
    source=post.get('source') or 'unknown'
    row.update(id=str(raw['id']),platform='vk',source='vk',url=raw.get('url'),
               source_id=source,source_kind=source,row_type=kind,text=raw.get('text') or '',
               collected_at=b.utc(raw['_collected_at']),published_at=date_iso,published_date=day,
               date_precision='day' if day_only else 'second' if date_iso else 'unknown',
               in_window=bool(day and '2026-06-01'<=day<='2026-10-28'),period=period(day),
               media_type='text',author_id_hash=raw.get('author_hash'),
               author_type='org' if raw.get('owner_kind',raw.get('author_kind'))=='community' else 'person',
               author_display=raw.get('author_display') if raw.get('owner_kind',raw.get('author_kind'))=='community' else None,
               is_source_owner=raw.get('is_post_owner') if kind!='post' else None,
               likes=vk_number(raw.get('likes')),reposts=vk_number(raw.get('reposts')),
               comments_count=vk_number(raw.get('comments')),collector_version='t11_v2/1.0',
               counter_precision='exact_or_null',matched_keywords=[])
    if kind=='post':
        row.update(parent_id=None,thread_id=row['id'],relevant=bool(SITE.search(row['text'])),
                   relevance_reason='post_mentions' if SITE.search(row['text']) else 'search_hit_without_term')
        if row['author_type']=='org':
            row['author_id_hash']=b.author_hash(salt,'vk',str(raw['id']).split('_')[0])
    else:
        row.update(parent_id=raw.get('parent_id'),thread_id=raw.get('thread_id'),
                   relevant=bool(SITE.search(post.get('text') or '')),relevance_reason='thread_context')
    return row

SITE=b.make_site()

def build():
    stats=Counter();snapshots={};private=set();salt=(ROOT/'.secrets/hash_salt').read_bytes()
    rows=b.youtube(SITE,salt,stats,snapshots,private)
    rows+=b.telegram(SITE,salt,stats,snapshots)
    for row in rows:
        row.update(published_date=row['published_at'][:10],date_precision='second',
                   period=period(row['published_at'][:10]),counter_precision='exact_or_null',collector_version='t11_v2/1.0')
        if row['source_id'] in ('sosedi_preobrazhenskoe','sokolinaya_gora_vao'):
            row['source_kind']='district'
            if row['row_type']=='post':row['author_display']=row['source_id']
    base=ROOT/'data/raw/vk/2026-10-28'
    post_files=b.complete_files(base,'posts');comment_files=b.complete_files(base,'comments')
    stats['vk_post_files']=len(post_files);stats['vk_comment_files']=len(comment_files)
    posts=b.latest(b.load_rows(post_files,snapshots),lambda r:str(r['id']),stats,'vk_post')
    comments=b.latest(b.load_rows(comment_files,snapshots),lambda r:str(r['id']),stats,'vk_comment')
    rows += [vk_row(raw,'post',raw,salt) for _,raw in sorted(posts.items())]
    for _,raw in sorted(comments.items()):
        post=posts.get(str(raw['post_id']))
        if post is None:raise ValueError('VK comment without post; no context may be invented')
        rows.append(vk_row(raw,'comment',post,salt))
    stats['vk_unique_posts']=len(posts);stats['vk_unique_comments']=len(comments)
    forbidden=re.compile('|'.join(re.escape(v) for v in sorted(private,key=lambda x:(-len(x),x)))) if private else None
    for row in rows:
        raw_text=row['text'];row['matched_keywords']=sorted(set(m[0].casefold() for rx in (SITE,b.TOPIC) for m in rx.finditer(raw_text)))
        row['text']=b.mask(raw_text,forbidden);row['author_display']=b.mask(row['author_display'],forbidden)
        row['lang']=b.language(row['text'])
        stats['masked_rows'] += row['text'] != raw_text
    keys={(r['platform'],r['id']) for r in rows}
    bykey={(r['platform'],r['id']):r for r in rows}
    for r in rows:
        r['parent_present']=r['parent_id'] is None or (r['platform'],r['parent_id']) in keys
        r['thread_present']=r['thread_id'] is None or (r['platform'],r['thread_id']) in keys
        r['context_complete']=r['parent_present'] and r['thread_present']
        stats[r['platform']+'_missing_parent_rows']+=not r['parent_present']
        stats[r['platform']+'_missing_thread_rows']+=not r['thread_present']
    # Propagate missing context to descendants without replacing any real ID.
    for _ in range(len(rows)):
        changed=False
        for r in rows:
            parent=bykey.get((r['platform'],r['parent_id']))
            if r['context_complete'] and parent and not parent['context_complete']:
                r['context_complete']=False;changed=True
        if not changed:break
    rows.sort(key=lambda r:(r['platform'],r['id']))
    assert len(keys)==len(rows),'duplicate keys'
    assert all(r['published_at'] is None or r['published_at'].endswith('Z') for r in rows),'timestamp'
    assert all(r['published_at'] is None for r in rows if r['date_precision']=='day'),'invented time'
    assert all(not forbidden.search(str(v)) for r in rows for v in r.values() if v is not None),'raw author leak'
    assert all(not(b.EMAIL.search(r['text']) or b.HANDLE.search(r['text']) or b.PHONE.search(r['text'])) for r in rows),'unmasked contact'
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==v for p,v in snapshots.items()),'inputs changed'
    assert sum(r['platform']=='youtube' and r['row_type'] in ('comment','reply') for r in rows)==stats['youtube_unique_raw_messages']
    for platform in ('youtube','telegram','vk'):
        group=[r for r in rows if r['platform']==platform]
        stats[platform+'_rows']=len(group)
        stats[platform+'_in_window_relevant_reactions']=sum(r['row_type'] in ('comment','reply') and r['in_window'] and r['relevant'] for r in group)
        stats[platform+'_incomplete_context_rows']=sum(not r['context_complete'] for r in group)
    table=pa.Table.from_pylist(rows,schema=SCHEMA)
    target=ROOT/'data/processed/corpus_v2.parquet'
    tmp=target.with_suffix('.tmp');pq.write_table(table,tmp,compression='zstd')
    assert pq.read_table(tmp).equals(table),'parquet readback'
    tmp.replace(target)
    OUT.mkdir(exist_ok=True)
    with (OUT/'corpus_summary_v2.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=b.SUMMARY_FIELDS);w.writeheader();w.writerows(b.summary(rows))
    inputs=[{'path':str(p.relative_to(ROOT)),'sha256':v} for p,v in sorted(snapshots.items())]
    payload={'version':'v2','analysis_window':['2026-06-01','2026-10-28'],
             'excluded_sources':['dsh outputs','Dzen','T12','T13 artifacts','T14','T15'],
             'inputs':inputs,'counts':dict(sorted(stats.items())),
             'quality_note':'Original missing parents are preserved and flagged, never replaced with invented rows; day-only dates stay dates.'}
    (OUT/'build_manifest.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    report=['PASS unique keys; privacy; UTC when timestamp known; no invented date times; immutable input snapshots; parquet readback.',
            'WARNING strict T11 parent-exists criterion is not met where raw parents are absent. Preserved IDs and context_complete flags permit review.']
    report += [f'{k}={v}' for k,v in sorted(stats.items())]
    (OUT/'build_checks.txt').write_text('\n'.join(report)+'\n')
    print('\n'.join(report))

if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    build()
