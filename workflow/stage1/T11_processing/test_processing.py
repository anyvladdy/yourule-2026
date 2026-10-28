"""Offline regression checks for T11. Run with python test_processing.py [-v]."""
import json
import tempfile
import unittest
from pathlib import Path
from collections import Counter
import build_corpus as b

STAMP = '2026-10-28T12:00:00Z'


def video(identity, title, description=''):
    return {'id': identity, '_collected_at': STAMP,
            'snippet': {'title': title, 'description': description, 'publishedAt': STAMP,
                        'channelId': 'source-identity', 'channelTitle': 'Public source'},
            'statistics': {}}


def comment(identity, text, **extra):
    return {'id': identity, 'snippet': {'textOriginal': text, 'publishedAt': STAMP,
            'authorDisplayName': '@fictional_person', 'authorChannelId': {'value': 'person-identity'},
            **extra}}


def thread(video_id, top, replies=()):
    return {'id': 'thread-resource-' + top['id'], '_collected_at': STAMP,
            'snippet': {'videoId': video_id, 'topLevelComment': top, 'totalReplyCount': len(replies)},
            'replies': {'comments': list(replies)}}


class Processing(unittest.TestCase):
    def setUp(self):
        self.old_root = b.ROOT
        self.site = b.make_site()
        self.temp = tempfile.TemporaryDirectory(prefix='t11-check-')
        b.ROOT = Path(self.temp.name)
        self.yt = b.ROOT / 'data/raw/youtube/2026-10-28'
        self.yt.mkdir(parents=True)

    def tearDown(self):
        b.ROOT = self.old_root
        self.temp.cleanup()

    def write(self, path, items):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in items))

    def load(self):
        stats, snapshots, private = Counter(), {}, set()
        rows = b.youtube(self.site, b'fictional-salt', stats, snapshots, private)
        return {r['id']: r for r in rows}, stats

    def test_reply_makes_entire_digest_thread_relevant(self):
        self.write(self.yt/'videos_a.jsonl', [video('digest','Новости','Об Электрозаводе')])
        self.write(self.yt/'comments_digest.jsonl', [
            thread('digest',comment('root','Не согласен'),[comment('child','Угроза наследию')]),
            thread('digest',comment('unrelated','Прогноз погоды'))])
        rows, _ = self.load()
        self.assertTrue(rows['root']['relevant'])
        self.assertTrue(rows['child']['relevant'])
        self.assertFalse(rows['unrelated']['relevant'])
        self.assertEqual(rows['root']['parent_id'],'digest')
        self.assertEqual(rows['child']['parent_id'],'root')
        self.assertEqual(rows['child']['thread_id'],'root')
        self.assertIsNone(rows['child']['likes'])
        self.assertIsNone(rows['child']['author_display'])

    def test_topical_context_and_source_owner(self):
        self.write(self.yt/'videos_a.jsonl',[video('topical','Судьба Электрозавода')])
        self.write(self.yt/'comments_topical.jsonl',[thread('topical',comment('a','Да',authorChannelId={'value':'source-identity'}))])
        rows, _ = self.load()
        self.assertTrue(rows['a']['relevant'])
        self.assertEqual(rows['a']['relevance_reason'],'topical_source')
        self.assertTrue(rows['a']['is_source_owner'])
        self.assertEqual(rows['a']['author_id_hash'], rows['topical']['author_id_hash'])

    def test_exact_selection_and_pilot_exclusion(self):
        self.write(self.yt/'videos_a.jsonl',[video('plural','Электрозаводы'),video('station','Электрозаводская'),video('yes','Электрозавод')])
        self.write(self.yt/'comments_plural.jsonl',[thread('plural',comment('bad','снос'))])
        self.write(self.yt/'comments_yes_pilot1.jsonl',[thread('yes',comment('pilot','снос'))])
        self.write(self.yt/'comments_yes_partial_a.jsonl',[thread('yes',comment('partial','снос'))])
        rows, stats = self.load()
        self.assertEqual(set(rows),{'yes'})
        self.assertEqual(stats['youtube_excluded_top_level'],1)

    def test_dedupe_latest_snapshot(self):
        self.write(self.yt/'videos_a.jsonl',[video('v','Электрозавод')])
        old = thread('v',comment('c','Ранняя версия'))
        new = thread('v',comment('c','Поздняя версия'))
        old['_collected_at'] = '2026-10-27T12:00:00Z'
        self.write(self.yt/'comments_a.jsonl',[new,old])
        rows, stats = self.load()
        self.assertEqual(rows['c']['text'],'Поздняя версия')
        self.assertEqual(stats['duplicates_youtube_message'],1)
        self.assertEqual(stats['youtube_duplicate_top_level'],1)

    def test_contact_mask_and_time_boundaries(self):
        self.assertEqual(b.mask('@someone mail@example.org +7 (999) 123-45-67',None),'[user] [email] [phone]')
        self.assertEqual(b.mask('1915–1928 и 2026-10-28',None),'1915–1928 и 2026-10-28')
        for stamp, expected in [('2026-05-31T23:59:59Z',False),('2026-06-01T00:00:00Z',True),('2026-10-28T23:59:59Z',True),('2026-10-29T00:00:00Z',False)]:
            row=b.base_row('youtube','x','video','x','topical','',stamp,STAMP)
            self.assertEqual(row['in_window'],expected)
        self.assertEqual(b.utc('2026-06-01T03:00:00+03:00'),'2026-06-01T00:00:00Z')

    def test_telegram_namespaced_parents_and_existing_hash(self):
        p=b.ROOT/'workflow/stage0/T01_telegram_video/out/telegram.csv'
        p.parent.mkdir(parents=True)
        p.write_text('handle,title,owner_type\nchan,Public source,media\n')
        base=b.ROOT/'data/raw/telegram/2026-10-28'
        self.write(base/'posts_chan.jsonl',[{'id':1,'channel':'chan','text':'Электрозавод','published_at':STAMP,'_collected_at':STAMP,'views':'1.2K'}])
        common={'post_id':1,'channel':'chan','text':'Да','published_at':STAMP,'_collected_at':STAMP,'sender_hash':'existinghash'}
        self.write(base/'comments_chan.jsonl',[dict(common,id=2,reply_to=None),dict(common,id=3,reply_to=2)])
        rows=b.telegram(self.site,b'fictional-salt',Counter(),{})
        byid={r['id']:r for r in rows}
        self.assertEqual(byid['chan:post:1:comment:3']['parent_id'],'chan:post:1:comment:2')
        self.assertEqual(byid['chan:post:1:comment:2']['parent_id'],'chan:post:1')
        self.assertEqual(byid['chan:post:1:comment:2']['author_id_hash'],'existinghash')
        self.assertTrue(all(r['relevant'] for r in rows))
        self.assertIsNone(byid['chan:post:1']['views'])


if __name__ == '__main__':
    unittest.main()
